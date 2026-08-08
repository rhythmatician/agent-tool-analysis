"""Deep analysis pipeline for agent tool exposure reports."""

from __future__ import annotations

import itertools
import math
import statistics
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from .clustering import (
    agglomerative_clusters,
    all_pair_metrics,
    build_adjacency_counts,
    build_session_index,
    cluster_boundary_metrics,
    cluster_internal_affinity,
    tool_boundary_metrics,
)
from .cost_evaluation import (
    COST_SCENARIOS,
    DEFAULT_GITHUB_EXPOSURE_RATES,
    cluster_exposure_economics,
    github_exposure_sensitivity,
    scenario_cost,
)
from .exposure_models import (
    EXPOSURE_MODELS,
    baseline_exposure_states,
    dynamic_tool_group_inventory,
    exposure_consistency,
    exposure_evidence_summary,
    exposure_model_summary,
    provider_availability_diagnostics,
    provider_scoped_session_diagnostics,
)
from .exposure_reporting import build_exposure_matrix, exposure_matrix_summary
from .nmf_screening import NMFConfig, run_nmf_screening
from .replay_harness import BASELINE_ARCHITECTURE_ID
from .telemetry_ingestion import (
    CONTROL_PLANE_TOOLS,
    Session,
    classify_tool_roles,
    normalize_tool_name,
    tool_role,
)
from .tool_definition_registry import (
    DefinitionRecord,
    DefinitionRegistry,
    ExplicitDefinitionProvider,
    ManifestDefinitionProvider,
    MappingDefinitionProvider,
)

KNOWN_DEPENDENCIES = {
    "apply_patch": {"execute/runTests", "create_file"},
    "edit": {"execute/runTests", "create_file"},
    "spawn_agent": {"list_agents", "wait_agent", "interrupt_agent", "followup_task"},
    "list_dir": {"file_search", "grep_search"},
    "exec": {"send_message", "wait"},
}
ESTIMATION_BASIS = "global distribution of resolved definition tokens (25th percentile / median / 75th percentile)"
DECISION_GITHUB_EXPOSURE_RATES = (0.25, 0.50, 0.75, 1.0)
DECISION_DELEGATION_OVERHEADS = (0, 100, 250, 500)


def load_explicit_tool_costs(path: str | None) -> dict[str, int]:
    if not path:
        return {}
    with open(path, "r", encoding="utf-8") as stream:
        data = __import__("json").load(stream)
    if not isinstance(data, dict):
        raise ValueError("--tool-costs must contain a JSON object.")
    costs: dict[str, int] = {}
    for raw_name, raw_value in data.items():
        name = normalize_tool_name(raw_name)
        if not name:
            continue
        if isinstance(raw_value, int):
            tokens = raw_value
        elif isinstance(raw_value, dict) and isinstance(raw_value.get("tokens"), int):
            tokens = raw_value["tokens"]
        else:
            raise ValueError(
                f"Invalid token cost for {raw_name!r}; expected integer or {{'tokens': int}}."
            )
        if tokens < 0:
            raise ValueError(f"Token cost for {raw_name!r} cannot be negative.")
        costs[name] = tokens
    return costs


@dataclass
class ToolStat:
    name: str
    sessions: int = 0
    calls: int = 0
    sessions_exposed: int = 0
    sessions_called: int = 0
    usage_rate: float = 0.0
    call_given_exposed: float | None = None
    expected_unused_tokens_per_session: float | None = None
    definition_tokens: int | None = None
    definition_cost_source: str = "unknown"
    estimated_cost_low: float | None = None
    estimated_cost_mid: float | None = None
    estimated_cost_high: float | None = None
    estimation_basis: str | None = None
    estimation_confidence: str | None = None


def acquire_definitions(
    observed_names: Iterable[str],
    vscode_definitions: dict[str, DefinitionRecord],
    codex_definitions: dict[str, DefinitionRecord],
    explicit_path: str | None,
    definition_roots: Iterable[str],
) -> tuple[
    dict[str, DefinitionRecord],
    DefinitionRegistry,
    ManifestDefinitionProvider,
    dict[str, Any],
]:
    explicit = ExplicitDefinitionProvider.from_path(explicit_path, normalize_tool_name)
    telemetry = MappingDefinitionProvider(
        [*vscode_definitions.values(), *codex_definitions.values()], precedence=200
    )
    manifest = ManifestDefinitionProvider(
        definition_roots, normalize_tool_name, runtime="codex"
    )
    registry = DefinitionRegistry([explicit, telemetry, manifest])
    definitions = registry.resolve_all(observed_names)
    explicit_records = [
        record for record in explicit.records() if record.estimated_tokens is not None
    ]
    telemetry_records = list(telemetry.records())
    return (
        definitions,
        registry,
        manifest,
        {
            "explicit_records": len(explicit_records),
            "telemetry_records": len(telemetry_records),
            "runtime_manifest": manifest.discovery_summary(),
        },
    )


def build_stats(
    sessions: list[Session],
    definitions: dict[str, DefinitionRecord],
    explicit_costs: dict[str, int],
    *,
    call_sessions: list[Session] | None = None,
    exposure_sessions: list[Session] | None = None,
) -> dict[str, ToolStat]:
    call_sessions = (
        call_sessions if call_sessions is not None else [s for s in sessions if s.calls]
    )
    exposure_sessions = (
        exposure_sessions
        if exposure_sessions is not None
        else [s for s in sessions if s.exposed_tools]
    )
    session_counts: Counter[str] = Counter()
    call_counts: Counter[str] = Counter()
    exposure_counts: Counter[str] = Counter()
    called_in_exposed: Counter[str] = Counter()
    for session in call_sessions:
        session_counts.update(session.tool_set)
        call_counts.update(session.calls)
    for session in exposure_sessions:
        exposure_counts.update(session.exposed_tools)
        called_in_exposed.update(session.tool_set & session.exposed_tools)
    total_calls = len(call_sessions)
    total_exposure = len(exposure_sessions)
    names = sorted(
        set(session_counts)
        | set(exposure_counts)
        | set(definitions)
        | set(explicit_costs)
    )
    stats: dict[str, ToolStat] = {}
    for name in names:
        definition_tokens = None
        cost_source = "unknown"
        definition = definitions.get(name)
        if definition is not None:
            definition_tokens = definition.estimated_tokens
            cost_source = (
                definition.source
                if definition.provider == "explicit"
                else f"{definition.provider}:{definition.source}:chars/4"
            )
        if name in explicit_costs:
            definition_tokens = explicit_costs[name]
            cost_source = "explicit"
        stat = ToolStat(
            name=name,
            sessions=session_counts[name],
            calls=call_counts[name],
            sessions_exposed=exposure_counts[name],
            sessions_called=session_counts[name],
            usage_rate=session_counts[name] / total_calls if total_calls else 0.0,
            call_given_exposed=called_in_exposed[name] / exposure_counts[name]
            if exposure_counts[name]
            else None,
            definition_tokens=definition_tokens,
            definition_cost_source=cost_source,
        )
        if definition_tokens is not None:
            stat.expected_unused_tokens_per_session = (
                definition_tokens
                * (exposure_counts[name] - called_in_exposed[name])
                / total_exposure
                if total_exposure
                else 0.0
            )
        stats[name] = stat
    infer_unresolved_costs(stats)
    return stats


def percentile(values: list[int], q: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return float(ordered[0])
    position = (len(ordered) - 1) * q
    low, high = math.floor(position), math.ceil(position)
    if low == high:
        return float(ordered[low])
    fraction = position - low
    return ordered[low] * (1 - fraction) + ordered[high] * fraction


def infer_unresolved_costs(stats: dict[str, ToolStat]) -> None:
    resolved = [
        stat.definition_tokens
        for stat in stats.values()
        if stat.definition_tokens is not None
    ]
    if not resolved:
        return
    estimates = {
        name: percentile(resolved, quantile)
        for name, quantile in (("low", 0.25), ("mid", 0.50), ("high", 0.75))
    }
    for stat in stats.values():
        if stat.definition_tokens is not None or (
            stat.calls == 0 and stat.sessions_exposed == 0
        ):
            continue
        stat.estimated_cost_low = estimates["low"]
        stat.estimated_cost_mid = estimates["mid"]
        stat.estimated_cost_high = estimates["high"]
        stat.estimation_basis = ESTIMATION_BASIS
        stat.estimation_confidence = "low"


def session_population_summary(sessions: list[Session]) -> dict[str, int]:
    with_calls = [s for s in sessions if s.calls]
    with_exposure = [s for s in sessions if s.exposed_tools]
    return {
        "sessions_total": len(sessions),
        "sessions_with_calls": len(with_calls),
        "sessions_with_direct_exposure": len(with_exposure),
        "sessions_with_calls_and_exposure": sum(
            bool(s.calls and s.exposed_tools) for s in sessions
        ),
        "sessions_with_calls_without_exposure": sum(
            bool(s.calls and not s.exposed_tools) for s in sessions
        ),
        "sessions_with_exposure_without_calls": sum(
            bool(s.exposed_tools and not s.calls) for s in sessions
        ),
    }


def classify_tools(
    stats: dict[str, ToolStat], global_usage_threshold: float
) -> dict[str, str]:
    known_costs = [
        stat.definition_tokens
        for stat in stats.values()
        if stat.definition_tokens is not None
    ]
    high_cost = percentile(known_costs, 0.75)
    result = {}
    for name, stat in stats.items():
        expensive = (
            high_cost is not None
            and stat.definition_tokens is not None
            and stat.definition_tokens >= high_cost
        )
        if stat.usage_rate >= global_usage_threshold:
            result[name] = (
                "ubiquitous-expensive: keep available, compress definition first"
                if expensive
                else "global-candidate: ubiquitous"
            )
        elif stat.definition_tokens is None:
            result[name] = "specialization-candidate: cost unknown"
        elif expensive:
            result[name] = (
                "strong-specialization-candidate: expensive and non-ubiquitous"
            )
        else:
            result[name] = "specialization-candidate"
    return result


def choose_global_tools(
    stats: dict[str, ToolStat], global_usage_threshold: float
) -> set[str]:
    return {
        name
        for name, stat in stats.items()
        if stat.usage_rate >= global_usage_threshold
    }


def make_candidate_agents(
    clusters: list[set[str]],
    global_tools: set[str],
    stats: dict[str, ToolStat],
    sessions: list[Session],
    pairs: dict[tuple[str, str], dict[str, float]],
    min_cluster_size: int,
    min_cluster_sessions: int,
) -> list[dict[str, Any]]:
    agents = []
    for index, cluster in enumerate(clusters, start=1):
        candidate_id = f"cluster_{index:02d}"
        specialist = set(cluster) - global_tools
        covered = sum(bool(session.tool_set & specialist) for session in sessions)
        if len(specialist) < min_cluster_size or covered < min_cluster_sessions:
            continue
        tools = sorted(specialist, key=lambda tool: (-stats[tool].sessions, tool))
        agents.append(
            {
                "candidate_id": candidate_id,
                "cluster_id": candidate_id,
                "tools": tools,
                "session_coverage_count": covered,
                "session_coverage_rate": covered / len(sessions) if sessions else 0.0,
                "internal_affinity": cluster_internal_affinity(specialist, pairs),
                "known_definition_tokens": sum(
                    stats[t].definition_tokens or 0
                    for t in specialist
                    if stats[t].definition_tokens is not None
                ),
                "unknown_cost_tools": sorted(
                    t for t in specialist if stats[t].definition_tokens is None
                ),
            }
        )
    return agents


def dependency_warnings(
    candidate_agents: list[dict[str, Any]], global_tools: set[str], all_tools: set[str]
) -> list[dict[str, Any]]:
    warnings = []
    for agent in candidate_agents:
        missing: dict[str, list[str]] = defaultdict(list)
        tools = set(agent["tools"])
        for tool in tools:
            for dependency in KNOWN_DEPENDENCIES.get(tool, set()):
                if (
                    dependency in all_tools
                    and dependency not in tools
                    and dependency not in global_tools
                ):
                    missing[tool].append(dependency)
        if missing:
            warnings.append(
                {
                    "candidate_id": agent["candidate_id"],
                    "missing_dependencies": {
                        tool: sorted(values) for tool, values in sorted(missing.items())
                    },
                }
            )
    return warnings


def dependency_preservation_warnings(
    used_tools: set[str],
    retained_tools: set[str],
    all_tools: set[str],
) -> list[dict[str, Any]]:
    """Report required dependencies that cannot be retained in a flat baseline."""
    warnings: dict[str, set[str]] = defaultdict(set)
    for root in used_tools:
        for dependency in KNOWN_DEPENDENCIES.get(root, set()):
            if dependency not in all_tools or dependency not in retained_tools:
                warnings[root].add(dependency)

    return [
        {
            "tool": tool,
            "missing_dependencies": sorted(dependencies),
        }
        for tool, dependencies in sorted(warnings.items())
    ]


def build_pruned_flat_baseline(
    sessions: list[Session],
    stats: dict[str, ToolStat],
    *,
    global_tools: set[str],
) -> dict[str, Any]:
    """Build a flat parent surface from used tools plus known dependencies."""
    used_tools = {name for name, stat in stats.items() if stat.calls > 0}
    retained_tools = set(used_tools)
    pending = list(sorted(used_tools))
    while pending:
        tool = pending.pop()
        for dependency in sorted(KNOWN_DEPENDENCIES.get(tool, set())):
            if dependency not in retained_tools:
                retained_tools.add(dependency)
                pending.append(dependency)

    all_tools = set(stats)
    removed_tools = all_tools - retained_tools
    warnings = dependency_preservation_warnings(
        used_tools=used_tools,
        retained_tools=retained_tools,
        all_tools=all_tools,
    )
    before = expected_token_cost_scenarios(
        sessions=sessions,
        stats=stats,
        global_tools=global_tools,
        candidate_agents=[],
        delegation_overhead_tokens=0,
        exposure_model="observed_only",
    )
    after = expected_token_cost_scenarios(
        sessions=sessions,
        stats=stats,
        global_tools=global_tools,
        candidate_agents=[],
        delegation_overhead_tokens=0,
        exposure_model="observed_only",
        baseline_tools=retained_tools,
    )
    scenarios: dict[str, dict[str, float | None]] = {}
    for scenario in COST_SCENARIOS:
        before_tokens = before[scenario]["baseline_tokens_per_session"]
        after_tokens = after[scenario]["baseline_tokens_per_session"]
        if before_tokens is None or after_tokens is None:
            absolute_reduction = None
            relative_reduction = None
        else:
            absolute_reduction = before_tokens - after_tokens
            relative_reduction = (
                absolute_reduction / before_tokens if before_tokens else None
            )
        scenarios[scenario] = {
            "baseline_tokens_per_session_before_pruning": before_tokens,
            "baseline_tokens_per_session_after_pruning": after_tokens,
            "absolute_reduction": absolute_reduction,
            "relative_reduction": relative_reduction,
        }
    called_tools = {tool for session in sessions for tool in session.tool_set}
    directly_observed_never_used_tools = {
        name
        for name in removed_tools
        if stats[name].sessions_exposed > 0 and stats[name].calls == 0
    }
    catalog_only_tools_removed = {
        name
        for name in removed_tools
        if stats[name].sessions_exposed == 0 and stats[name].calls == 0
    }
    unresolved_retained_runtime_tools = {
        name
        for name in retained_tools
        if stats.get(name) is not None
        and stats[name].calls > 0
        and stats[name].definition_tokens is None
    }
    return {
        "architecture_id": "pruned_flat_baseline",
        "used_tools": sorted(used_tools),
        "tools_removed": sorted(removed_tools),
        "tools_retained": sorted(retained_tools),
        "catalog_tokens_removed": {
            scenario: _cost_for_tools(stats, removed_tools, scenario)
            for scenario in COST_SCENARIOS
        },
        "directly_observed_never_used_tools_removed": sorted(
            directly_observed_never_used_tools
        ),
        "catalog_only_tools_removed": sorted(catalog_only_tools_removed),
        "observed_exposure_tokens_removed_per_session": {
            scenario: scenarios[scenario]["absolute_reduction"]
            for scenario in COST_SCENARIOS
        },
        "unresolved_retained_runtime_tool_exposure": {
            "status": "unknown" if unresolved_retained_runtime_tools else "none",
            "tool_count": len(unresolved_retained_runtime_tools),
            "tools": sorted(unresolved_retained_runtime_tools),
        },
        "baseline_tokens_per_session_before_pruning": {
            scenario: scenarios[scenario]["baseline_tokens_per_session_before_pruning"]
            for scenario in COST_SCENARIOS
        },
        "baseline_tokens_per_session_after_pruning": {
            scenario: scenarios[scenario]["baseline_tokens_per_session_after_pruning"]
            for scenario in COST_SCENARIOS
        },
        "absolute_reduction": {
            scenario: scenarios[scenario]["absolute_reduction"]
            for scenario in COST_SCENARIOS
        },
        "relative_reduction": {
            scenario: scenarios[scenario]["relative_reduction"]
            for scenario in COST_SCENARIOS
        },
        "historical_called_tool_coverage": (
            len(called_tools & retained_tools) / len(called_tools)
            if called_tools
            else 1.0
        ),
        "recommendation": {
            "action": "remove_directly_observed_never_used_tools",
            "headline": (
                "Remove the "
                f"{len(directly_observed_never_used_tools)} directly observed, "
                "never-used exposed tools now."
            ),
            "tool_count": len(directly_observed_never_used_tools),
            "tools": sorted(directly_observed_never_used_tools),
        },
        "dependency_preservation_warnings": warnings,
        "scenarios": scenarios,
    }


def _cost_for_tools(
    stats: dict[str, ToolStat],
    tools: set[str],
    scenario: str,
) -> float | None:
    costs = [scenario_cost(stats[tool], scenario) for tool in tools if tool in stats]
    return (
        sum(cost for cost in costs if cost is not None)
        if all(cost is not None for cost in costs)
        else None
    )


def _grid_net_reduction(
    sensitivity: dict[str, Any], exposure_rate: float, scenario: str = "mid"
) -> float | None:
    point = next(
        (
            item
            for item in sensitivity["grid"]
            if math.isclose(item["assumed_exposure_rate"], exposure_rate)
        ),
        None,
    )
    return (
        point["scenarios"][scenario]["net_token_reduction_per_session"]
        if point
        else None
    )


def _pareto_frontier(subsets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    dimensions = (
        "break_even_exposure_rate_mid",
        "definition_tokens_mid",
        "activation_rate",
    )
    eligible = [
        row for row in subsets if all(row[key] is not None for key in dimensions)
    ]
    frontier = []
    for candidate in eligible:
        if not any(
            all(other[key] <= candidate[key] for key in dimensions)
            and any(other[key] < candidate[key] for key in dimensions)
            for other in eligible
            if other is not candidate
        ):
            frontier.append(candidate)
    return sorted(
        frontier,
        key=lambda row: (
            row[dimensions[0]],
            row[dimensions[1]],
            row[dimensions[2]],
            row["tools"],
        ),
    )


def _criterion_winner(
    subsets: list[dict[str, Any]], key: str, *, maximize: bool = False
) -> dict[str, Any] | None:
    eligible = [row for row in subsets if row[key] is not None]
    return (
        min(
            eligible,
            key=lambda row: (
                (-row[key] if maximize else row[key]),
                row["definition_tokens_mid"]
                if row["definition_tokens_mid"] is not None
                else float("inf"),
                row["activation_rate"],
                row["tools"],
            ),
        )
        if eligible
        else None
    )


def evaluate_cluster_one_subsets(
    sessions: list[Session],
    stats: dict[str, ToolStat],
    cluster_tools: Iterable[str],
    pairs: dict[tuple[str, str], dict[str, float]],
    all_clustered_tools: Iterable[str],
    global_tools: set[str],
    delegation_overhead_tokens: int,
    exposure_rates: Iterable[float],
) -> dict[str, Any] | None:
    tools = tuple(sorted(set(cluster_tools)))
    if len(tools) < 2:
        return None
    requested = tuple(float(rate) for rate in exposure_rates)
    rates = tuple(dict.fromkeys((*requested, 0.25, 0.50, 1.0)))
    rows: list[dict[str, Any]] = []
    for size in range(2, len(tools) + 1):
        for combination in itertools.combinations(tools, size):
            subset = set(combination)
            sensitivity = github_exposure_sensitivity(
                sessions, stats, subset, delegation_overhead_tokens, rates
            )
            definition_tokens = {
                scenario: (
                    sum(cost for cost in costs if cost is not None)
                    if all(cost is not None for cost in costs)
                    else None
                )
                for scenario in COST_SCENARIOS
                for costs in [[scenario_cost(stats[tool], scenario) for tool in subset]]
            }
            margins = [
                tool_boundary_metrics(tool, subset, pairs, all_clustered_tools)[
                    "boundary_margin"
                ]
                for tool in subset
            ]
            warnings = dependency_warnings(
                [{"candidate_id": "cluster_01_subset", "tools": list(combination)}],
                global_tools,
                set(stats),
            )
            rows.append(
                {
                    "tools": list(combination),
                    "tool_count": size,
                    "reference_cluster": size == len(tools),
                    "historical_called_tool_coverage_rate": 1.0,
                    "activation_rate": sensitivity["activation_rate"],
                    **{
                        f"definition_tokens_{scenario}": definition_tokens[scenario]
                        for scenario in COST_SCENARIOS
                    },
                    **{
                        f"break_even_exposure_rate_{scenario}": sensitivity[
                            f"break_even_exposure_rate_{scenario}"
                        ]
                        for scenario in COST_SCENARIOS
                    },
                    "internal_affinity": cluster_internal_affinity(subset, pairs),
                    "mean_boundary_margin": statistics.fmean(margins),
                    "min_boundary_margin": min(margins),
                    "net_reduction_at_25%": _grid_net_reduction(sensitivity, 0.25),
                    "net_reduction_at_50%": _grid_net_reduction(sensitivity, 0.50),
                    "net_reduction_at_100%": _grid_net_reduction(sensitivity, 1.0),
                    "exposure_rate_grid": [
                        point
                        for point in sensitivity["grid"]
                        if point["assumed_exposure_rate"] in requested
                    ],
                    "dependency_warnings": warnings[0]["missing_dependencies"]
                    if warnings
                    else {},
                }
            )
    frontier = _pareto_frontier(rows)
    viable = [
        row
        for row in rows
        if row["break_even_exposure_rate_mid"] is not None
        and row["break_even_exposure_rate_mid"] <= 1.0
    ]
    winners = {
        "lowest_break_even_exposure_rate": _criterion_winner(
            rows, "break_even_exposure_rate_mid"
        ),
        "greatest_mid_case_savings_at_25_percent_exposure": _criterion_winner(
            rows, "net_reduction_at_25%", maximize=True
        ),
        "greatest_mid_case_savings_at_50_percent_exposure": _criterion_winner(
            rows, "net_reduction_at_50%", maximize=True
        ),
        "greatest_mid_case_savings_at_100_percent_exposure": _criterion_winner(
            rows, "net_reduction_at_100%", maximize=True
        ),
        "highest_internal_affinity_among_economically_viable_subsets": _criterion_winner(
            viable, "internal_affinity", maximize=True
        ),
    }
    return {
        "cluster_id": "cluster_01",
        "cluster_tools": list(tools),
        "subset_count": len(rows),
        "pareto_dimensions": [
            "break_even_exposure_rate_mid",
            "definition_tokens_mid",
            "activation_rate",
        ],
        "reference": next(row for row in rows if row["reference_cluster"]),
        "pareto_frontier": frontier,
        "best_subsets": winners,
        "subsets": rows,
    }


def build_candidate_decision_table(
    subset_analysis: dict[str, Any] | None,
) -> dict[str, Any] | None:
    """Evaluate Pareto candidates and the reference on a fixed economics grid."""
    if subset_analysis is None:
        return None

    selected = [
        *(("pareto", row) for row in subset_analysis["pareto_frontier"]),
        ("reference", subset_analysis["reference"]),
    ]
    candidates = []
    for index, (candidate_type, row) in enumerate(selected, start=1):
        definition_tokens = row["definition_tokens_mid"]
        cells = []
        for exposure_rate in DECISION_GITHUB_EXPOSURE_RATES:
            for overhead in DECISION_DELEGATION_OVERHEADS:
                expected = (
                    row["activation_rate"] * (definition_tokens + overhead)
                    if definition_tokens is not None
                    else None
                )
                baseline = (
                    exposure_rate * definition_tokens
                    if definition_tokens is not None
                    else None
                )
                reduction = (
                    baseline - expected
                    if baseline is not None and expected is not None
                    else None
                )
                cells.append(
                    {
                        "github_baseline_exposure_rate": exposure_rate,
                        "delegation_overhead_tokens_per_activation": overhead,
                        "activation_rate": row["activation_rate"],
                        "specialist_definition_tokens": definition_tokens,
                        "expected_tokens_per_session": expected,
                        "absolute_reduction_per_session": reduction,
                        "relative_reduction": reduction / baseline
                        if reduction is not None and baseline
                        else None,
                        "break_even_github_exposure_rate": expected / definition_tokens
                        if expected is not None and definition_tokens
                        else None,
                        "internal_affinity": row["internal_affinity"],
                        "minimum_boundary_margin": row["min_boundary_margin"],
                    }
                )
        known_reductions = [
            cell["absolute_reduction_per_session"]
            for cell in cells
            if cell["absolute_reduction_per_session"] is not None
        ]
        candidates.append(
            {
                "candidate_id": "cluster_01_reference"
                if candidate_type == "reference"
                else f"pareto_{index:02d}",
                "candidate_type": candidate_type,
                "tools": row["tools"],
                "tool_count": row["tool_count"],
                "activation_rate": row["activation_rate"],
                "specialist_definition_tokens": definition_tokens,
                "internal_affinity": row["internal_affinity"],
                "minimum_boundary_margin": row["min_boundary_margin"],
                "worst_case_positive_reduction": min(known_reductions)
                if known_reductions
                else None,
                "viable_cells": sum(reduction > 0 for reduction in known_reductions)
                / len(cells)
                if len(known_reductions) == len(cells) and cells
                else None,
                "cells": cells,
            }
        )
    return {
        "cost_scenario": "mid",
        "github_baseline_exposure_rates": list(DECISION_GITHUB_EXPOSURE_RATES),
        "delegation_overhead_tokens_per_activation": list(
            DECISION_DELEGATION_OVERHEADS
        ),
        "candidate_count": len(candidates),
        "grid_cells_per_candidate": len(DECISION_GITHUB_EXPOSURE_RATES)
        * len(DECISION_DELEGATION_OVERHEADS),
        "candidates": candidates,
    }


def expected_known_token_cost(
    sessions: list[Session],
    stats: dict[str, ToolStat],
    global_tools: set[str],
    candidate_agents: list[dict[str, Any]],
    delegation_overhead_tokens: int,
    *,
    exposure_sessions: list[Session] | None = None,
) -> dict[str, Any]:
    exposure_sessions = (
        exposure_sessions
        if exposure_sessions is not None
        else [s for s in sessions if s.exposed_tools]
    )
    known = {name for name, stat in stats.items() if stat.definition_tokens is not None}
    baseline = (
        statistics.fmean(
            sum(
                stats[name].definition_tokens or 0
                for name in session.exposed_tools
                if name in known
            )
            for session in exposure_sessions
        )
        if exposure_sessions
        else 0.0
    )
    membership = {
        tool: agent["candidate_id"]
        for agent in candidate_agents
        for tool in agent["tools"]
    }
    shared_known = global_tools & known
    parent_tools = {
        tool for tool in known if tool not in membership and tool not in shared_known
    }
    agent_costs = {
        agent["candidate_id"]: sum(
            stats[t].definition_tokens or 0 for t in agent["tools"] if t in known
        )
        + sum(stats[t].definition_tokens or 0 for t in shared_known)
        for agent in candidate_agents
    }
    per_session = []
    specialist_counts = []
    for session in exposure_sessions:
        activated = {
            membership[tool] for tool in session.tool_set if tool in membership
        }
        cost = sum(
            stats[name].definition_tokens or 0
            for name in session.exposed_tools
            if name in parent_tools
        )
        cost += sum(
            agent_costs[agent] + delegation_overhead_tokens for agent in activated
        )
        per_session.append(cost)
        specialist_counts.append(len(activated))
    expected = statistics.fmean(per_session) if per_session else 0.0
    scenarios = {
        model: expected_token_cost_scenarios(
            sessions,
            stats,
            global_tools,
            candidate_agents,
            delegation_overhead_tokens,
            exposure_sessions=exposure_sessions,
            exposure_model=model,
        )
        for model in EXPOSURE_MODELS
    }
    total_calls = sum(stat.calls for stat in stats.values())
    known_calls = sum(stats[name].calls for name in known)
    exposure_rows = sum(len(session.exposed_tools) for session in exposure_sessions)
    return {
        "known_cost_coverage": {
            "tools_with_known_cost": len(known),
            "tools_total": len(stats),
            "catalog_coverage_rate": len(known) / len(stats) if stats else 0.0,
            "observed_tools_with_known_cost": sum(
                1 for name in known if stats[name].calls > 0
            ),
            "observed_tools_total": sum(1 for stat in stats.values() if stat.calls > 0),
            "observed_tool_coverage_rate": sum(
                1 for name in known if stats[name].calls > 0
            )
            / sum(1 for stat in stats.values() if stat.calls > 0)
            if any(stat.calls > 0 for stat in stats.values())
            else 0.0,
            "calls_with_known_cost": known_calls,
            "total_calls": total_calls,
            "usage_weighted_coverage_rate": known_calls / total_calls
            if total_calls
            else 0.0,
            "exposure_weighted_coverage_rate": sum(
                stats[name].definition_tokens is not None
                for session in exposure_sessions
                for name in session.exposed_tools
            )
            / exposure_rows
            if exposure_rows
            else 0.0,
        },
        "flat_baseline_known_tokens": baseline,
        "unassigned_known_tokens_after_partition": statistics.fmean(
            sum(
                stats[name].definition_tokens or 0
                for name in session.exposed_tools
                if name in parent_tools
            )
            for session in exposure_sessions
        )
        if exposure_sessions
        else 0.0,
        "expected_known_tokens_per_session_after_partition": expected,
        "expected_known_tokens_saved_per_session": baseline - expected,
        "expected_known_token_savings_rate": (baseline - expected) / baseline
        if baseline
        else None,
        "delegation_overhead_tokens_per_activated_specialist": delegation_overhead_tokens,
        "median_specialists_activated_per_session": statistics.median(specialist_counts)
        if specialist_counts
        else 0,
        "sessions_requiring_multiple_specialists_rate": sum(
            count > 1 for count in specialist_counts
        )
        / len(specialist_counts)
        if specialist_counts
        else 0.0,
        "cost_scenarios": expected_token_cost_scenarios(
            sessions,
            stats,
            global_tools,
            candidate_agents,
            delegation_overhead_tokens,
            exposure_sessions=exposure_sessions,
        ),
        "cost_scenarios_by_exposure_model": scenarios,
        "interpretation": "Known-token estimate using directly observed exposure only. Unknown tool-definition costs are excluded. Recovered telemetry costs use a chars/4 approximation. Shared tools are charged once per activated agent context; unassigned tools remain conservatively available to the flat surface. Counterfactual exposure-model results are reported separately.",
    }


def sensitivity_summary(
    scenarios_by_exposure_model: dict[str, dict[str, dict[str, float | None]]],
) -> dict[str, Any]:
    values = {
        model: scenarios["mid"]["relative_token_reduction"]
        for model, scenarios in scenarios_by_exposure_model.items()
    }
    available = {model: value for model, value in values.items() if value is not None}
    decision = [
        value
        for model in ("provider_scoped", "all_runtime_tools")
        if (value := values.get(model)) is not None
    ]
    minimum, maximum = (
        (min(available.values()), max(available.values()))
        if available
        else (None, None)
    )
    stable = len(decision) == 2 and (
        all(value > 0 for value in decision) or all(value < 0 for value in decision)
    )
    return {
        "min_mid_reduction": minimum,
        "max_mid_reduction": maximum,
        "exposure_model_at_min": min(
            (model for model, value in available.items() if value == minimum),
            key=EXPOSURE_MODELS.index,
        )
        if available
        else None,
        "exposure_model_at_max": max(
            (model for model, value in available.items() if value == maximum),
            key=EXPOSURE_MODELS.index,
        )
        if available
        else None,
        "sign_stable": stable,
    }


def reduction_metrics(
    baseline_tokens_per_session: float, proposed_tokens_per_session: float
) -> dict[str, float | None]:
    reduction = baseline_tokens_per_session - proposed_tokens_per_session
    return {
        "baseline_tokens_per_session": baseline_tokens_per_session,
        "proposed_tokens_per_session": proposed_tokens_per_session,
        "absolute_token_reduction_per_session": reduction,
        "relative_token_reduction": reduction / baseline_tokens_per_session
        if baseline_tokens_per_session
        else 0.0,
    }


def build_architecture_variants(
    candidate_agents: list[dict[str, Any]],
    boundary_by_tool: dict[str, dict[str, float]],
    global_tools: set[str],
) -> list[dict[str, Any]]:
    variants = [
        {
            "variant_id": "pruned_flat_baseline",
            "variant_type": "pruned_flat_baseline",
            "cluster_id": None,
            "specialist_tools": [],
            "pruned_tools": [],
        }
    ]
    for agent in candidate_agents:
        candidate_id = str(agent["candidate_id"])
        tools = sorted(set(agent["tools"]) - global_tools)
        if len(tools) < 2:
            continue
        variants.append(
            {
                "variant_id": candidate_id,
                "variant_type": "raw_cluster",
                "cluster_id": str(agent.get("cluster_id", candidate_id)),
                "specialist_tools": tools,
                "pruned_tools": [],
            }
        )
        retained = sorted(
            tool
            for tool in tools
            if boundary_by_tool.get(tool, {}).get("boundary_margin", 0.0) > 0
        )
        if len(retained) >= 2:
            variants.append(
                {
                    "variant_id": f"{candidate_id}_boundary_pruned",
                    "variant_type": "boundary_pruned",
                    "cluster_id": str(agent.get("cluster_id", candidate_id)),
                    "specialist_tools": retained,
                    "pruned_tools": sorted(set(tools) - set(retained)),
                }
            )
    return variants


def _scenario_sessions(
    sessions: list[Session], exposure_sessions: list[Session] | None
) -> list[Session]:
    indexed = {session.session_id: session for session in sessions}
    for session in exposure_sessions or []:
        indexed.setdefault(session.session_id, session)
    return list(indexed.values())


def expected_token_cost_scenarios(
    sessions: list[Session],
    stats: dict[str, ToolStat],
    global_tools: set[str],
    candidate_agents: list[dict[str, Any]],
    delegation_overhead_tokens: int,
    *,
    exposure_sessions: list[Session] | None = None,
    exposure_model: str = "observed_only",
    baseline_tools: set[str] | None = None,
) -> dict[str, dict[str, float | None]]:
    scenario_sessions = _scenario_sessions(sessions, exposure_sessions)
    states = baseline_exposure_states(scenario_sessions, exposure_model)
    membership = {
        tool: agent["candidate_id"]
        for agent in candidate_agents
        for tool in agent["tools"]
    }
    agents = {agent["candidate_id"]: agent for agent in candidate_agents}
    baseline_surface = set(stats) if baseline_tools is None else set(baseline_tools)
    shared_surface = global_tools & baseline_surface
    parent_tools = baseline_surface - set(membership) - shared_surface

    def total_cost(names: Iterable[str], scenario: str) -> float | None:
        costs = []
        for name in names:
            stat = stats.get(name)
            if stat is None:
                continue
            cost = scenario_cost(stat, scenario)
            if cost is None:
                return None
            costs.append(cost)
        return sum(costs)

    result = {}
    for scenario in COST_SCENARIOS:
        baseline_costs, proposed_costs = [], []
        for session in scenario_sessions:
            exposure = states[session.session_id]
            baseline = total_cost(exposure.exposed_tools & baseline_surface, scenario)
            if baseline is None:
                continue
            proposed = total_cost(exposure.exposed_tools & parent_tools, scenario)
            activated = {
                membership[tool] for tool in exposure.actual_calls if tool in membership
            }
            for candidate_id in activated:
                specialist_cost = total_cost(
                    set(agents[candidate_id]["tools"]) | shared_surface,
                    scenario,
                )
                if specialist_cost is None:
                    proposed = None
                    break
                proposed = (
                    (proposed or 0.0) + specialist_cost + delegation_overhead_tokens
                )
            if proposed is not None:
                baseline_costs.append(baseline)
                proposed_costs.append(proposed)
        result[scenario] = (
            reduction_metrics(
                statistics.fmean(baseline_costs), statistics.fmean(proposed_costs)
            )
            if baseline_costs
            else {
                "baseline_tokens_per_session": None,
                "proposed_tokens_per_session": None,
                "absolute_token_reduction_per_session": None,
                "relative_token_reduction": None,
            }
        )
    return result


def evaluate_architecture_variants(
    sessions: list[Session],
    stats: dict[str, ToolStat],
    global_tools: set[str],
    candidate_agents: list[dict[str, Any]],
    boundary_by_tool: dict[str, dict[str, float]],
    delegation_overhead_tokens: int,
    *,
    exposure_sessions: list[Session] | None = None,
    baseline_tools: set[str] | None = None,
) -> list[dict[str, Any]]:
    scenario_sessions = _scenario_sessions(sessions, exposure_sessions)
    called_tools = {tool for session in scenario_sessions for tool in session.tool_set}
    evaluated: list[dict[str, Any]] = []
    for variant in build_architecture_variants(
        candidate_agents, boundary_by_tool, global_tools
    ):
        specialist = set(variant["specialist_tools"])
        candidate = (
            [{"candidate_id": variant["variant_id"], "tools": sorted(specialist)}]
            if specialist
            else []
        )
        model_scenarios = {
            model: expected_token_cost_scenarios(
                sessions,
                stats,
                global_tools,
                candidate,
                delegation_overhead_tokens,
                exposure_sessions=exposure_sessions,
                exposure_model=model,
                baseline_tools=baseline_tools,
            )
            for model in EXPOSURE_MODELS
        }
        activation_count = sum(
            bool(session.tool_set & specialist) for session in scenario_sessions
        )
        activation_rate = (
            activation_count / len(scenario_sessions) if scenario_sessions else 0.0
        )
        coverage = (
            len(called_tools & ((set(stats) - specialist) | specialist | global_tools))
            / len(called_tools)
            if called_tools
            else 1.0
        )
        scenarios = {
            scenario: {
                **model_scenarios["observed_only"][scenario],
                "specialist_activation_rate": activation_rate,
                "average_specialist_activations_per_session": activation_rate,
                "sessions_requiring_specialist": activation_count,
            }
            for scenario in COST_SCENARIOS
        }
        evaluated.append(
            {
                **variant,
                "baseline_architecture_id": "pruned_flat_baseline",
                "historical_called_tool_coverage_rate": coverage,
                "scenarios": scenarios,
                "sensitivity": sensitivity_summary(model_scenarios),
                "exposure_economics": cluster_exposure_economics(
                    scenario_sessions, stats, specialist, delegation_overhead_tokens
                )
                if specialist
                else None,
                "scenarios_by_exposure_model": {
                    model: {
                        scenario: {
                            **metrics,
                            "specialist_activation_rate": activation_rate,
                            "average_specialist_activations_per_session": activation_rate,
                            "sessions_requiring_specialist": activation_count,
                        }
                        for scenario, metrics in metrics_by_scenario.items()
                    }
                    for model, metrics_by_scenario in model_scenarios.items()
                },
            }
        )

    def ranking_key(item: dict[str, Any]) -> tuple[float, str]:
        reduction = item["scenarios"]["mid"]["relative_token_reduction"]
        return (
            -(float(reduction) if reduction is not None else float("-inf")),
            str(item["variant_id"]),
        )

    evaluated.sort(key=ranking_key)
    for rank, variant in enumerate(evaluated, 1):
        variant["rank"] = rank
    return evaluated


def source_summary(sessions: list[Session]) -> dict[str, int]:
    return dict(sorted(Counter(session.source for session in sessions).items()))


def definition_cost_completeness(
    stats: dict[str, ToolStat], required_tools: Iterable[str] | None = None
) -> dict[str, Any]:
    """Separate exact supplied costs from approximations and unknown costs."""
    names = set(stats) if required_tools is None else set(required_tools)
    names &= set(stats)
    exact = {
        name
        for name in names
        if stats[name].definition_tokens is not None
        and stats[name].definition_cost_source == "explicit"
    }
    estimated = {
        name
        for name in names
        if name not in exact
        and (
            stats[name].definition_tokens is not None
            or stats[name].estimated_cost_mid is not None
        )
    }
    unknown = names - exact - estimated
    return {
        "status": (
            "exact"
            if len(exact) == len(names)
            else "estimated"
            if not unknown
            else "incomplete"
        ),
        "exact_complete": len(exact) == len(names),
        "tools_total": len(names),
        "tools_with_exact_cost": len(exact),
        "tools_with_estimated_cost": len(estimated),
        "tools_without_cost": len(unknown),
        "exact_coverage_rate": len(exact) / len(names) if names else 1.0,
        "exact_cost_tools": sorted(exact),
        "estimated_cost_tools": sorted(estimated),
        "unknown_cost_tools": sorted(unknown),
    }


def frontier_measurement_summary(
    sessions: list[Session],
    stats: dict[str, ToolStat],
    retained_tools: Iterable[str],
    exposure_model: str,
    search_provenance: dict[str, Any],
) -> dict[str, Any]:
    exposure = exposure_evidence_summary(sessions)
    costs = {
        "catalog": definition_cost_completeness(stats),
        "retained_baseline": definition_cost_completeness(stats, retained_tools),
    }
    counterfactual = exposure_model != "observed_only"
    directional_only = (
        counterfactual
        or not exposure["sufficient_for_empirical_frontier"]
        or not costs["retained_baseline"]["exact_complete"]
    )
    return {
        "frontier_kind": "counterfactual" if counterfactual else "empirical",
        "directional_only": directional_only,
        "exposure_model": exposure_model,
        "exposure_evidence_sufficient": exposure["sufficient_for_empirical_frontier"],
        "cost_completeness": costs["retained_baseline"],
        "assumptions": [
            "Direct exposure is distinct from actual calls.",
            "Unknown exposure is not treated as zero exposure.",
            "Recovered chars/4 costs are estimates, not exact definition costs.",
        ],
        "search_provenance": dict(search_provenance),
        "exposure_evidence": exposure,
        "definition_costs": costs,
    }


def classify_specialist_recommendation(
    *,
    pareto_candidates: Iterable[Mapping[str, Any]],
    candidate_agents: Iterable[Mapping[str, Any]],
    directional_variants: Iterable[Mapping[str, Any]],
    exposure_evidence_sufficient: bool,
    cost_complete: bool,
    search_complete: bool,
    quality_gate_passed: bool = False,
) -> dict[str, Any]:
    """Classify recommendation strength without erasing directional evidence.

    A quality gate is intentionally explicit: telemetry and modeled economics
    can make a recommendation provisional, but cannot make it proven.
    """
    candidates = list(pareto_candidates)
    agents = list(candidate_agents)
    variants = list(directional_variants)
    complete_candidates = [
        candidate for candidate in candidates if candidate.get("is_cost_complete", True)
    ]
    if complete_candidates and exposure_evidence_sufficient and cost_complete:
        selected = min(
            complete_candidates,
            key=lambda candidate: (
                candidate.get("expected_context_cost_after_communication") is None,
                candidate.get("expected_context_cost_after_communication")
                or float("inf"),
                candidate.get("agent_count", 1),
                candidate.get("architecture_id", ""),
            ),
        )
        agent_count = int(selected.get("agent_count", 1))
        status = "proven" if quality_gate_passed else "provisional"
        return {
            "status": status,
            "direction": f"{agent_count}-agent architecture",
            "confidence": "high" if status == "proven" else "moderate",
            "best_guess_architecture": (
                "two_agents"
                if agent_count == 2
                else f"{agent_count}_agent_architecture"
            ),
            "best_guess_candidate_id": selected.get("architecture_id"),
            "why": [
                "cost-complete candidate retained on the empirical Pareto frontier",
                "lowest modeled context cost among retained complete candidates",
                "quality gate passed"
                if quality_gate_passed
                else "quality preservation remains unvalidated",
            ],
            "required_validation": (
                "none beyond ongoing monitoring"
                if quality_gate_passed
                else "optional advanced replay or A/B against the pruned flat baseline, including routing and quality"
            ),
            "search_complete": search_complete,
            "evidence_status": "complete",
        }

    positive_variants = []
    contradictory = False
    for variant in variants:
        sensitivity = variant.get("sensitivity") or {}
        minimum_value = sensitivity.get("min_mid_reduction")
        maximum_value = sensitivity.get("max_mid_reduction")
        if (
            minimum_value is not None and not isinstance(minimum_value, (int, float))
        ) or (
            maximum_value is not None and not isinstance(maximum_value, (int, float))
        ):
            continue
        if minimum_value is None:
            minimum_value = maximum_value
        if maximum_value is None:
            maximum_value = minimum_value
        if minimum_value is None or maximum_value is None:
            continue
        minimum = float(minimum_value)
        maximum = float(maximum_value)
        if minimum < 0 < maximum:
            contradictory = True
        if minimum >= 0 and maximum > 0:
            positive_variants.append(variant)

    if not contradictory and len(agents) >= 2 and len(positive_variants) >= 2:
        return {
            "status": "provisional",
            "direction": "2-agent architecture",
            "confidence": "moderate-low",
            "best_guess_architecture": "two_agents",
            "best_guess_candidate_id": None,
            "why": [
                "strong structural separation across multiple candidate tool families",
                "directional sensitivity favors specialist exposure",
                "prefer the smallest multi-agent split because higher fragmentation is not validated",
                "no empirical evidence yet that the split preserves or improves quality",
            ],
            "required_validation": "optional advanced replay or A/B against the pruned flat baseline, including routing and quality",
            "search_complete": search_complete,
            "evidence_status": "inconclusive_directional",
        }

    return {
        "status": "none",
        "direction": None,
        "confidence": "low",
        "best_guess_architecture": None,
        "best_guess_candidate_id": None,
        "why": [
            "evidence is contradictory, too sparse, or does not directionally favor one architecture"
        ],
        "required_validation": "none for this advisory output; optional advanced validation can test a user-selected option",
        "search_complete": search_complete,
        "evidence_status": "inconclusive",
    }


def materialize_provisional_architecture(
    *,
    recommendation: Mapping[str, Any],
    candidate_agents: Iterable[Mapping[str, Any]],
    directional_variants: Iterable[Mapping[str, Any]],
    retained_tools: Iterable[str],
    global_tools: Iterable[str],
    search_provenance: Mapping[str, Any],
    dependencies: Mapping[str, Iterable[str]] | None = None,
    search_candidates: Iterable[Mapping[str, Any]] | None = None,
) -> dict[str, Any] | None:
    """Materialize the strongest directional two-agent hypothesis.

    This artifact is deliberately not a partition-search finalist. It is a
    concrete, replayable hypothesis assembled from structural clusters and
    sensitivity results while their costs or exposure remain incomplete.
    """

    if recommendation.get("status") != "provisional":
        return None
    if recommendation.get("direction") != "2-agent architecture":
        return None

    searched = [
        candidate
        for candidate in (search_candidates or ())
        if int(candidate.get("agent_count", 0)) == 2
    ]
    if searched:
        selected_candidate = min(
            searched,
            key=lambda candidate: (
                candidate.get("expected_context_cost_after_communication") is None,
                candidate.get("expected_context_cost_after_communication")
                or float("inf"),
                str(candidate.get("architecture_id", "")),
            ),
        )
        raw_agents = selected_candidate.get("agents", {})
        if not raw_agents and selected_candidate.get("agent_tools"):
            shared = set(selected_candidate.get("shared_tools", ()))
            raw_agents = {
                f"agent_{index:02d}": {
                    "exclusive_tools": list(
                        selected_candidate.get("exclusive_tools", ())[index - 1]
                    ),
                    "shared_tools": sorted(shared),
                    "tools": list(tools),
                }
                for index, tools in enumerate(
                    selected_candidate["agent_tools"], start=1
                )
            }
        if not isinstance(raw_agents, Mapping) or len(raw_agents) != 2:
            return None
        shared = set(selected_candidate.get("shared_tools", ()))
        control = set(selected_candidate.get("control_tools", ()))
        return {
            "architecture_id": "provisional_two_agents",
            "topology": "peer",
            "agent_count": 2,
            "shared_tools": {str(agent_id): sorted(shared) for agent_id in raw_agents},
            "control_tools": sorted(control),
            "delegation": {
                "enabled": bool(control),
                "topology": "agent_01 <-> agent_02",
                "edges": {
                    "agent_01": ["agent_02"],
                    "agent_02": ["agent_01"],
                },
            },
            "agents": {
                str(agent_id): {
                    "exclusive_tools": sorted(set(agent.get("exclusive_tools", ()))),
                    "shared_tools": sorted(shared),
                    "tools": sorted(set(agent.get("tools", ())) | shared),
                }
                for agent_id, agent in raw_agents.items()
            },
            "provisional": True,
            "directional_only": True,
            "assumptions": [
                "membership comes from the dependency-closed partition search",
                "exposure or definition costs remain incomplete",
                "agent names, routes, and quality preservation remain hypotheses",
            ],
            "provenance": {
                "source": "partition_search_candidate",
                "candidate_id": selected_candidate.get("architecture_id"),
                "search_provenance": dict(search_provenance),
            },
        }

    agents = list(candidate_agents)
    variants = list(directional_variants)
    by_id = {str(agent.get("candidate_id")): agent for agent in agents}

    def score(agent: Mapping[str, Any]) -> tuple[float, float, str]:
        candidate_id = str(agent.get("candidate_id"))
        matching = [
            variant
            for variant in variants
            if str(variant.get("variant_id", "")).split("_boundary_pruned", 1)[0]
            == candidate_id
        ]
        maximum_reductions: list[float] = []
        for variant in matching:
            maximum_reduction = (variant.get("sensitivity") or {}).get(
                "max_mid_reduction"
            )
            if isinstance(maximum_reduction, (int, float)):
                maximum_reductions.append(float(maximum_reduction))
        maximum = max(
            maximum_reductions,
            default=float("-inf"),
        )
        return (
            maximum,
            float(agent.get("internal_affinity") or 0.0),
            candidate_id,
        )

    selected = sorted(by_id.values(), key=score, reverse=True)[:2]
    if len(selected) != 2:
        return None

    retained = set(retained_tools)
    global_set = set(global_tools)
    dependency_map = dependencies or KNOWN_DEPENDENCIES
    specialist_tools = [
        sorted((set(agent.get("tools", ())) & retained) - global_set)
        for agent in selected
    ]
    for tools in specialist_tools:
        pending = list(tools)
        while pending:
            tool = pending.pop()
            for dependency in dependency_map.get(tool, ()):
                if (
                    dependency in retained
                    and dependency not in global_set
                    and dependency not in tools
                ):
                    tools.append(dependency)
                    pending.append(dependency)
        tools.sort()
    specialist_tools = [tools for tools in specialist_tools if tools]
    if len(specialist_tools) != 2:
        return None
    shared = retained & (global_set | set(CONTROL_PLANE_TOOLS))
    assigned = set().union(*map(set, specialist_tools)) | shared
    # A peer architecture cannot strand retained capabilities on an implicit
    # parent. Preserve capability coverage by assigning any unclustered tools
    # to the first peer; the partition search remains the source of truth for
    # measured assignments.
    unassigned = sorted(retained - assigned)
    if unassigned:
        specialist_tools[0].extend(unassigned)
        specialist_tools[0].sort()
    architecture_id = "provisional_two_agents"
    assumptions = [
        "tool-family separation is inferred from structural clusters, not measured runtime routing",
        "sensitivity ranges are directional because exposure or definition costs are incomplete",
        "the pruned flat baseline retains all historically required tools and known dependencies",
        "agent names, responsibilities, activation paths, and quality preservation remain hypotheses",
    ]
    provenance = {
        "source": "directional_structure_and_sensitivity",
        "recommendation_status": recommendation.get("status"),
        "direction": recommendation.get("direction"),
        "candidate_agent_ids": [str(agent.get("candidate_id")) for agent in selected],
        "directional_variant_ids": [
            str(variant.get("variant_id"))
            for variant in variants
            if str(variant.get("variant_id", "")).split("_boundary_pruned", 1)[0]
            in {str(agent.get("candidate_id")) for agent in selected}
        ],
        "search_provenance": dict(search_provenance),
    }
    return {
        "architecture_id": architecture_id,
        "topology": "peer",
        "agent_count": 2,
        "shared_tools": {f"agent_{index:02d}": sorted(shared) for index in range(1, 3)},
        "control_tools": sorted(shared & set(CONTROL_PLANE_TOOLS)),
        "agents": {
            f"agent_{index:02d}": {
                "exclusive_tools": sorted(set(tools) - shared),
                "shared_tools": sorted(shared),
                "tools": sorted(set(tools) | shared),
            }
            for index, tools in enumerate(specialist_tools, start=1)
        },
        "provisional": True,
        "directional_only": True,
        "assumptions": assumptions,
        "provenance": provenance,
    }


def _semantic_agent_details(
    agent_id: str, tools: Iterable[str], index: int
) -> dict[str, Any]:
    """Give an anonymous tool group a readable, explicitly provisional label."""
    tool_list = sorted(set(tools))
    families = Counter(tool.split(".", 1)[0].split("_", 1)[0] for tool in tool_list)
    family = families.most_common(1)[0][0] if families else "tool"
    family_label = family.replace("-", " ").replace("_", " ").title()
    if len(families) == 1:
        name = f"{family_label} specialist"
        role = f"{family_label} tool specialist"
    else:
        name = f"Tool group {index} specialist"
        role = "Focused specialist for a structurally related tool group"
    return {
        "agent_id": agent_id,
        "name": name,
        "role": role,
        "description": (
            "Handles the tools in this inferred cluster: " + ", ".join(tool_list) + "."
        ),
        "tools": tool_list,
        "semantic_status": "provisional",
    }


def build_architecture_options(
    *,
    baseline: Mapping[str, Any],
    manifest: Mapping[str, Any],
    recommendation: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Expose a small set of concrete architectures for the user to choose."""
    manifest_architectures = {
        str(architecture.get("architecture_id")): architecture
        for architecture in manifest.get("architectures", [])
        if isinstance(architecture, Mapping)
    }
    candidate_ids = list(recommendation.get("pareto_candidate_ids", ()))
    provisional_ids = list(recommendation.get("provisional_architecture_ids", ()))
    # The normal report is a decision aid, not an exhaustive partition dump.
    # Keep empirical finalists visible, then add one concrete provisional
    # hypothesis when it is the only directional option available.
    selected_ids = [
        architecture_id
        for architecture_id in candidate_ids[:2]
        if architecture_id in manifest_architectures
    ]
    selected_ids.extend(
        architecture_id
        for architecture_id in provisional_ids[:1]
        if architecture_id in manifest_architectures
        and architecture_id not in selected_ids
    )
    selected_ids = selected_ids[:3]
    options: list[dict[str, Any]] = [
        {
            "option_id": BASELINE_ARCHITECTURE_ID,
            "architecture_id": BASELINE_ARCHITECTURE_ID,
            "label": "Pruned single agent",
            "status": "baseline",
            "parent_tools": list(baseline.get("tools_retained", [])),
            "agents": [],
            "why_choose": [
                "simplest architecture",
                "no routing or handoff complexity",
                "retains every historically used tool and known dependency",
            ],
            "tradeoffs": [
                "keeps all retained tools on one parent surface",
                "does not benefit from specialist context separation",
            ],
            "confidence": "high for pruning; quality of the unmodified architecture is not re-evaluated",
        }
    ]
    for architecture_id in selected_ids:
        architecture = manifest_architectures[architecture_id]
        is_provisional = architecture_id in provisional_ids
        agents = [
            {
                **_semantic_agent_details(
                    agent_id,
                    tools.get("tools", []) if isinstance(tools, Mapping) else tools,
                    index,
                ),
                "exclusive_tools": sorted(
                    tools.get("exclusive_tools", [])
                    if isinstance(tools, Mapping)
                    else tools
                ),
                "shared_tools": sorted(
                    tools.get("shared_tools", []) if isinstance(tools, Mapping) else []
                ),
            }
            for index, (agent_id, tools) in enumerate(
                sorted((architecture.get("agents") or {}).items()), start=1
            )
        ]
        shared_tools = architecture.get("shared_tools", {})
        if isinstance(shared_tools, Mapping):
            shared_tools = sorted(
                set().union(*(set(values) for values in shared_tools.values()))
            )
        options.append(
            {
                "option_id": architecture_id,
                "architecture_id": architecture_id,
                "label": (
                    "Two cooperating agents"
                    if architecture.get("topology") == "peer" and len(agents) == 2
                    else f"Empirical finalist {architecture_id}"
                ),
                "status": "provisional" if is_provisional else "empirical_pareto",
                "topology": architecture.get("topology", "flat"),
                "agent_count": architecture.get("agent_count", len(agents)),
                "parent_tools": sorted(architecture.get("parent_tools", [])),
                "shared_tools": list(shared_tools or []),
                "agents": agents,
                "why_choose": (
                    [
                        "strongest specialization hypothesis in the available evidence",
                        "likely lower context per agent",
                        "structural clustering supports the split",
                        "evidence is directional, not conclusive",
                    ]
                    if is_provisional
                    else [
                        "retained on the empirical Pareto frontier",
                        "offers a measured context-cost tradeoff worth considering",
                    ]
                ),
                "tradeoffs": [
                    "adds routing and handoff complexity",
                    "semantic roles and activation paths remain hypotheses",
                ],
                "confidence": (
                    recommendation.get("confidence", "unknown")
                    if is_provisional
                    else "empirical cost frontier; quality unvalidated"
                ),
                "provenance": architecture.get("provenance", {})
                if is_provisional
                else {"source": "empirical_partition_search"},
            }
        )
    return options


def apply_offline_replay_result(
    recommendation: Mapping[str, Any],
    candidate_id: str,
    comparison: Mapping[str, Any],
) -> dict[str, Any]:
    """Strengthen or reject one hypothesis using a completed offline replay."""

    updated = dict(recommendation)
    updated["replay_candidate_id"] = candidate_id
    updated["replay_comparison"] = dict(comparison)
    if comparison.get("passed") is True:
        updated.update(
            {
                "status": "replay_validated",
                "evidence_status": "replay_validated",
                "confidence": "high",
                "required_validation": "controlled production A/B before applying configuration",
            }
        )
        updated["why"] = [
            *updated.get("why", []),
            "offline recorded replay passed the frozen-baseline quality and context gate",
        ]
        updated["headline"] = (
            f"Recommend the {updated.get('direction', 'candidate')} architecture; "
            "offline replay passed the frozen-baseline gate."
        )
    else:
        updated.update(
            {
                "status": "replay_rejected",
                "evidence_status": "replay_rejected",
                "rejected_candidate_id": candidate_id,
                "direction": None,
                "best_guess_architecture": None,
                "best_guess_candidate_id": None,
                "required_validation": "collect new evidence before choosing this architecture",
            }
        )
        failure_reason = (
            "quality"
            if comparison.get("quality_delta", 0) < 0
            else "the strict historical-capability or context-cost gate"
        )
        updated["why"] = [
            *updated.get("why", []),
            f"offline replay rejected the candidate because it failed {failure_reason}",
        ]
        updated["headline"] = (
            "Offline replay rejected the current specialist hypothesis."
        )
    return updated


def definition_resolution_report(
    stats: dict[str, ToolStat], registry: DefinitionRegistry
) -> list[dict[str, Any]]:
    rows = []
    for name, stat in sorted(stats.items()):
        if stat.calls == 0:
            continue
        record = registry.resolve(name)
        rows.append(
            {
                "observed_tool": name,
                "calls": stat.calls,
                "sessions_called": stat.sessions_called,
                "definition_resolved": record is not None,
                "definition_source": record.source if record else None,
                "provider": record.provider if record else None,
                "estimated_tokens": record.estimated_tokens if record else None,
                "confidence": record.confidence if record else "unresolved",
                "evidence_type": record.evidence_type if record else "unresolved",
            }
        )
    return rows


def analyze(
    sessions: list[Session],
    vscode_definitions: dict[str, DefinitionRecord],
    codex_definitions: dict[str, DefinitionRecord],
    *,
    explicit_path: str | None,
    definition_roots: Iterable[str],
    min_tool_sessions: int,
    similarity_threshold: float,
    global_usage_threshold: float,
    min_cluster_size: int,
    min_cluster_sessions: int,
    delegation_overhead_tokens: int,
    max_agents: int = 3,
    communication_tokens_per_handoff: float = 0.0,
    max_exhaustive_units: int = 10,
    max_partition_candidates: int = 5000,
    github_exposure_rates: Iterable[float] = DEFAULT_GITHUB_EXPOSURE_RATES,
    nmf_max_factors: int = 4,
    nmf_seeds: Iterable[int] = (0, 1, 2),
    nmf_iterations: int = 160,
) -> dict[str, Any]:
    if max_agents < 1:
        raise ValueError("max_agents must be at least 1.")
    if communication_tokens_per_handoff < 0:
        raise ValueError("Communication cost cannot be negative.")
    observed_names = (
        {
            tool
            for session in sessions
            for tool in (session.tool_set | session.exposed_tools)
        }
        | set(vscode_definitions)
        | set(codex_definitions)
    )
    definitions, registry, _manifest, discovery = acquire_definitions(
        observed_names,
        vscode_definitions,
        codex_definitions,
        explicit_path,
        definition_roots,
    )
    call_sessions = [session for session in sessions if session.calls]
    exposure_sessions = [session for session in sessions if session.exposed_tools]
    stats = build_stats(
        sessions,
        definitions,
        load_explicit_tool_costs(explicit_path),
        call_sessions=call_sessions,
        exposure_sessions=exposure_sessions,
    )
    role_records = classify_tool_roles(stats)
    classifications = classify_tools(stats, global_usage_threshold)
    global_tools = choose_global_tools(stats, global_usage_threshold)
    session_index = build_session_index(call_sessions)
    pairs = all_pair_metrics(
        sorted(
            name for name, stat in stats.items() if stat.sessions >= min_tool_sessions
        ),
        session_index,
        build_adjacency_counts(call_sessions),
    )
    active_tools = sorted(
        name
        for name, stat in stats.items()
        if stat.sessions >= min_tool_sessions
        and role_records[name].role not in {"delegation", "coordination"}
    )
    nmf_screening = run_nmf_screening(
        call_sessions,
        [
            tool
            for tool, stat in stats.items()
            if stat.sessions >= min_tool_sessions
            and role_records[tool].role == "domain"
            and tool not in global_tools
        ],
        role_records,
        config=NMFConfig(
            max_factors=nmf_max_factors,
            seeds=tuple(nmf_seeds),
            iterations=nmf_iterations,
        ),
    )
    clusters = agglomerative_clusters(active_tools, pairs, similarity_threshold)
    candidates = make_candidate_agents(
        clusters,
        global_tools,
        stats,
        call_sessions,
        pairs,
        min_cluster_size,
        min_cluster_sessions,
    )
    cluster_one = next(
        (
            candidate
            for candidate in candidates
            if candidate["candidate_id"] == "cluster_01"
        ),
        None,
    )
    github_sensitivity = (
        github_exposure_sensitivity(
            sessions,
            stats,
            set(cluster_one["tools"]),
            delegation_overhead_tokens,
            github_exposure_rates,
        )
        if cluster_one
        else None
    )
    boundary_by_tool: dict[str, dict[str, float]] = {}
    cluster_reports = []
    for index, cluster in enumerate(clusters, 1):
        metrics = cluster_boundary_metrics(
            cluster, clusters, pairs, active_tools, session_index, call_sessions
        )
        cluster_reports.append(
            {"cluster_id": f"cluster_{index:02d}", "tools": sorted(cluster), **metrics}
        )
        for tool in cluster:
            boundary_by_tool[tool] = tool_boundary_metrics(
                tool, cluster, pairs, active_tools
            )
    subset_analysis = (
        evaluate_cluster_one_subsets(
            sessions,
            stats,
            cluster_one["tools"],
            pairs,
            active_tools,
            global_tools,
            delegation_overhead_tokens,
            github_exposure_rates,
        )
        if cluster_one
        else None
    )
    pruned_flat_baseline = build_pruned_flat_baseline(
        sessions,
        stats,
        global_tools=global_tools,
    )
    retained_tools = set(pruned_flat_baseline["tools_retained"])
    from .partition_search import search_partitions

    partition_result = search_partitions(
        sessions=call_sessions,
        stats=stats,
        required_tools=retained_tools,
        global_tools=global_tools,
        dependencies=KNOWN_DEPENDENCIES,
        max_agents=max_agents,
        communication_tokens_per_handoff=communication_tokens_per_handoff,
        delegation_tokens_per_activation=delegation_overhead_tokens,
        max_exhaustive_units=max_exhaustive_units,
        max_partition_candidates=max_partition_candidates,
        baseline_tools=retained_tools,
        control_tools=CONTROL_PLANE_TOOLS,
        search_hints=nmf_screening.search_hints,
        exposure_model="observed_only",
    )
    measurement = frontier_measurement_summary(
        sessions,
        stats,
        retained_tools,
        "observed_only",
        partition_result.report["search_provenance"],
    )
    partition_result.report.update(
        {
            "frontier_kind": measurement["frontier_kind"],
            "directional_only": measurement["directional_only"],
            "exposure_evidence_sufficient": measurement["exposure_evidence_sufficient"],
            "cost_completeness": measurement["cost_completeness"],
            "assumptions": measurement["assumptions"],
        }
    )
    variants = evaluate_architecture_variants(
        call_sessions,
        stats,
        global_tools,
        candidates,
        boundary_by_tool,
        delegation_overhead_tokens,
        exposure_sessions=exposure_sessions,
        baseline_tools=retained_tools,
    )
    strongest_pairs = sorted(
        ({"tool_a": a, "tool_b": b, **metrics} for (a, b), metrics in pairs.items()),
        key=lambda row: (
            -float(row["affinity"]),
            -float(row["co_sessions"]),
            row["tool_a"],
            row["tool_b"],
        ),
    )
    tools_report = []
    for name in sorted(
        stats, key=lambda value: (-stats[value].sessions, -stats[value].calls, value)
    ):
        stat, definition = stats[name], definitions.get(name)
        tools_report.append(
            {
                "name": name,
                "sessions": stat.sessions,
                "calls": stat.calls,
                "usage_rate": stat.usage_rate,
                "definition_tokens": stat.definition_tokens,
                "definition_cost_source": stat.definition_cost_source,
                "estimated_cost_low": stat.estimated_cost_low,
                "estimated_cost_mid": stat.estimated_cost_mid,
                "estimated_cost_high": stat.estimated_cost_high,
                "estimation_basis": stat.estimation_basis,
                "estimation_confidence": stat.estimation_confidence,
                "definition_provider": definition.provider if definition else None,
                "definition_runtime": definition.runtime if definition else None,
                "definition_raw_name": definition.raw_name if definition else None,
                "definition_confidence": definition.confidence
                if definition
                else "unresolved",
                "definition_evidence_type": definition.evidence_type
                if definition
                else "unresolved",
                "sessions_exposed": stat.sessions_exposed,
                "sessions_directly_observed_exposure": stat.sessions_exposed,
                "sessions_called": stat.sessions_called,
                "call_given_exposed": stat.call_given_exposed,
                "expected_unused_tokens_per_session": stat.expected_unused_tokens_per_session,
                **boundary_by_tool.get(
                    name,
                    {
                        "mean_internal_affinity": None,
                        "best_external_affinity": None,
                        "boundary_margin": None,
                    },
                ),
                "classification": classifications[name],
                "global_candidate": name in global_tools,
            }
        )
    warnings = dependency_warnings(candidates, global_tools, set(stats))
    pareto_candidate_ids = [
        candidate.architecture_id for candidate in partition_result.pareto_candidates
    ]
    specialist_classification = classify_specialist_recommendation(
        pareto_candidates=(
            {
                "architecture_id": candidate.architecture_id,
                "agent_count": candidate.agent_count,
                "expected_context_cost_after_communication": candidate.expected_context_cost_after_communication,
                "is_cost_complete": candidate.is_cost_complete,
            }
            for candidate in partition_result.pareto_candidates
        ),
        candidate_agents=candidates,
        directional_variants=variants,
        exposure_evidence_sufficient=measurement["exposure_evidence_sufficient"],
        cost_complete=measurement["cost_completeness"]["exact_complete"],
        search_complete=partition_result.search_complete,
    )
    provisional_architecture = materialize_provisional_architecture(
        recommendation=specialist_classification,
        candidate_agents=candidates,
        directional_variants=variants,
        retained_tools=retained_tools,
        global_tools=global_tools,
        search_provenance=partition_result.report["search_provenance"],
        dependencies=KNOWN_DEPENDENCIES,
        search_candidates=(
            partition_result.report.get("candidates", [])
            if specialist_classification["status"] == "provisional"
            else None
        ),
    )
    if (
        specialist_classification["status"] == "provisional"
        and provisional_architecture is None
    ):
        specialist_classification = {
            **specialist_classification,
            "status": "none",
            "direction": None,
            "confidence": "low",
            "best_guess_architecture": None,
            "best_guess_candidate_id": None,
            "why": [
                "directional evidence did not produce two concrete dependency-closed specialist assignments"
            ],
            "required_validation": "none for this advisory output; collect structural evidence before forming a specialist option",
            "evidence_status": "inconclusive",
        }
    provisional_architecture_ids = (
        [provisional_architecture["architecture_id"]]
        if provisional_architecture is not None
        else []
    )
    if provisional_architecture is not None:
        specialist_classification = {
            **specialist_classification,
            "provisional_architecture_provenance": provisional_architecture[
                "provenance"
            ],
        }
    manifest = dict(partition_result.manifest)
    manifest["provisional_architecture_ids"] = provisional_architecture_ids
    if provisional_architecture is not None:
        manifest["architectures"] = [
            *manifest["architectures"],
            provisional_architecture,
        ]
    architecture_options = build_architecture_options(
        baseline=pruned_flat_baseline,
        manifest=manifest,
        recommendation={
            **specialist_classification,
            "pareto_candidate_ids": pareto_candidate_ids,
            "provisional_architecture_ids": provisional_architecture_ids,
        },
    )
    option_ids = [option["architecture_id"] for option in architecture_options]
    multiple_options = (
        len(option_ids) > 1 and specialist_classification["status"] != "proven"
    )
    if multiple_options:
        specialist_headline = (
            "Choose between the concrete architecture options below; the available "
            "evidence does not distinguish them strongly enough to choose for you."
        )
    elif specialist_classification["status"] == "proven":
        specialist_headline = (
            f"Recommend the {specialist_classification['direction']} architecture; "
            "the quality gate passed."
        )
    elif specialist_classification["status"] == "provisional":
        specialist_headline = (
            f"Best current guess: {specialist_classification['direction']}; "
            "treat the split as experimental until replay or A/B validation."
        )
    elif pareto_candidate_ids:
        specialist_headline = (
            "Compare the pruned flat baseline with the "
            f"{len(pareto_candidate_ids)} cost-complete empirical Pareto "
            "candidate(s); no single direction is selected."
        )
    else:
        specialist_headline = (
            "No cost-complete empirical Pareto candidates or directional "
            "specialist recommendation is supported by the available evidence."
        )
    return {
        "config": {
            "min_tool_sessions": min_tool_sessions,
            "similarity_threshold": similarity_threshold,
            "global_usage_threshold": global_usage_threshold,
            "min_cluster_size": min_cluster_size,
            "min_cluster_sessions": min_cluster_sessions,
            "delegation_overhead_tokens": delegation_overhead_tokens,
            "github_exposure_rates": list(github_exposure_rates),
            "nmf_max_factors": nmf_max_factors,
            "nmf_seeds": list(nmf_seeds),
            "nmf_iterations": nmf_iterations,
        },
        "tools": tools_report,
        "exposure_matrix": build_exposure_matrix(sessions, stats),
        "exposure_matrix_summary": exposure_matrix_summary(sessions, stats),
        "exposure_consistency": exposure_consistency(sessions),
        "measurement_completeness": measurement,
        "tool_roles": [
            {
                "tool": record.tool,
                "role": record.role,
                "evidence": record.evidence,
                "confidence": record.confidence,
            }
            for record in role_records.values()
        ],
        "nmf_screening": nmf_screening.as_dict(),
        "exposure_models": exposure_model_summary(sessions),
        "github_exposure_sensitivity": github_sensitivity,
        "cluster_one_subset_analysis": subset_analysis,
        "candidate_decision_table": build_candidate_decision_table(subset_analysis),
        "pruned_flat_baseline": pruned_flat_baseline,
        "architecture_manifest": manifest,
        "architecture_options": architecture_options,
        "partition_search": partition_result.report,
        "specialist_recommendation": {
            "action": "choose_architecture_option"
            if multiple_options
            else "recommend_architecture",
            "headline": specialist_headline,
            **specialist_classification,
            "baseline_architecture_id": BASELINE_ARCHITECTURE_ID,
            "pareto_candidate_ids": pareto_candidate_ids,
            "provisional_architecture_ids": provisional_architecture_ids,
            "architecture_option_ids": option_ids,
            "decision_mode": "user_choice"
            if multiple_options
            else "single_recommendation",
            "search_complete": partition_result.search_complete,
            "search_strategy": partition_result.search_strategy,
            "pareto_scope": partition_result.pareto_scope,
            "exposure_model": "observed_only",
            "frontier_kind": measurement["frontier_kind"],
            "directional_only": measurement["directional_only"],
            "exposure_evidence_sufficient": measurement["exposure_evidence_sufficient"],
            "cost_completeness": measurement["cost_completeness"],
            "assumptions": measurement["assumptions"],
            "search_provenance": measurement["search_provenance"],
        },
        "dynamic_tool_group_inventory": dynamic_tool_group_inventory(sessions),
        "provider_availability_diagnostics": provider_availability_diagnostics(
            sessions
        ),
        "provider_scoped_session_diagnostics": provider_scoped_session_diagnostics(
            sessions
        ),
        "definition_resolution": definition_resolution_report(stats, registry),
        "definition_discovery": discovery,
        "clusters": cluster_reports,
        "global_candidates": sorted(global_tools),
        "candidate_agents": candidates,
        "architecture_variants": variants,
        "dependency_warnings": warnings,
        "overhead": expected_known_token_cost(
            call_sessions,
            stats,
            global_tools,
            [],
            delegation_overhead_tokens,
            exposure_sessions=exposure_sessions,
        ),
        "strongest_pairs": strongest_pairs[:100],
        "caveats": [
            "Historical co-usage is evidence of operational coupling, not proof that tools belong in the same agent.",
            "This script does not measure task correctness or success directly; quality preservation still requires empirical A/B or replay evaluation.",
            "Tool-definition token costs are exact only when supplied explicitly with --tool-costs. Telemetry-recovered costs use a chars/4 approximation.",
            "The known-token calculation excludes unknown tool-definition costs; scenario estimates use a global resolved-definition distribution for unresolved observed tools.",
            "A zero delegation-overhead setting is a lower-bound estimate, not a claim that delegation is free.",
            "Direct exposure, inferred baseline exposure, and actual calls are separate evidence dimensions; observed-only is an oracle lower bound and should not judge specialization.",
            "The all-runtime and provider-scoped results are counterfactual baseline assumptions, not observed exposure claims.",
            "Provider-scoped exposure requires explicit provider availability telemetry; calls and absent calls do not establish availability.",
        ],
        "corpus": {
            "sessions": len(sessions),
            **session_population_summary(sessions),
            "tool_calls": sum(len(session.calls) for session in sessions),
            "unique_tools": len(stats),
            "active_tools_for_clustering": len(active_tools),
            "sources": source_summary(sessions),
        },
    }
