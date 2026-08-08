"""Fast, reproducible NMF screening for domain-tool workloads.

This module is deliberately a screening layer. NMF factors describe latent
workload structure; they are not agents and are never used as hard ownership.
The default input is a binary session x domain-tool call-presence matrix. Direct
exposure is intentionally excluded.
"""

from __future__ import annotations

import itertools
import math
import random
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence

from .telemetry_ingestion import EvidenceSession, ToolRoleRecord


@dataclass(frozen=True)
class NMFConfig:
    """Reproducible screening configuration."""

    max_factors: int = 4
    seeds: tuple[int, ...] = (0, 1, 2)
    iterations: int = 160
    tolerance: float = 1e-5
    matrix_mode: str = "binary_session_usage"
    dominant_loading_threshold: float = 0.55
    loading_margin_threshold: float = 0.15
    entropy_threshold: float = 0.80


@dataclass(frozen=True)
class NMFScreening:
    """Structured screening evidence and soft search hints."""

    status: str
    config: Mapping[str, Any]
    matrix: Mapping[str, Any]
    factor_counts: tuple[int, ...]
    evaluations: tuple[Mapping[str, Any], ...]
    selected_factor_count: int | None
    search_hints: Mapping[str, Any]
    control_plane: Mapping[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "config": dict(self.config),
            "matrix": dict(self.matrix),
            "factor_counts": list(self.factor_counts),
            "evaluations": [dict(item) for item in self.evaluations],
            "selected_factor_count": self.selected_factor_count,
            "search_hints": dict(self.search_hints),
            "control_plane": dict(self.control_plane),
        }


def _validate_config(config: NMFConfig) -> None:
    if config.max_factors < 1:
        raise ValueError("NMF max_factors must be at least 1.")
    if not config.seeds:
        raise ValueError("NMF seeds must not be empty.")
    if config.iterations < 1:
        raise ValueError("NMF iterations must be positive.")
    if config.matrix_mode not in {
        "binary_session_usage",
        "freshness_weighted_session_usage",
    }:
        raise ValueError("Unsupported NMF matrix mode.")
    for name, value in (
        ("dominant_loading_threshold", config.dominant_loading_threshold),
        ("loading_margin_threshold", config.loading_margin_threshold),
        ("entropy_threshold", config.entropy_threshold),
    ):
        if not 0 <= value <= 1:
            raise ValueError(f"NMF {name} must be between 0 and 1.")


def _matrix(
    sessions: Sequence[EvidenceSession],
    tools: Sequence[str],
    session_weights: Mapping[str, float] | None = None,
) -> list[list[float]]:
    return [
        [
            (session_weights or {}).get(session.session_id, 1.0)
            if tool in session.tool_set
            else 0.0
            for tool in tools
        ]
        for session in sessions
        if session.called_tools
    ]


def _frobenius(matrix: list[list[float]]) -> float:
    return math.sqrt(sum(value * value for row in matrix for value in row))


def _transpose(matrix: list[list[float]]) -> list[list[float]]:
    return [list(column) for column in zip(*matrix)] if matrix else []


def _multiply(left: list[list[float]], right: list[list[float]]) -> list[list[float]]:
    if not left or not right:
        return []
    right_t = _transpose(right)
    return [
        [sum(a * b for a, b in zip(row, column)) for column in right_t]
        for row in left
    ]


def _nmf(
    matrix: list[list[float]], rank: int, seed: int, config: NMFConfig
) -> tuple[list[list[float]], list[list[float]], float]:
    rows, columns = len(matrix), len(matrix[0])
    rng = random.Random(seed)
    epsilon = 1e-10
    w = [[0.1 + rng.random() for _ in range(rank)] for _ in range(rows)]
    h = [[0.1 + rng.random() for _ in range(columns)] for _ in range(rank)]
    previous = float("inf")
    for _ in range(config.iterations):
        wt = _transpose(w)
        numerator_h = _multiply(wt, matrix)
        denominator_h = _multiply(_multiply(wt, w), h)
        for i in range(rank):
            for j in range(columns):
                h[i][j] *= numerator_h[i][j] / (denominator_h[i][j] + epsilon)

        numerator_w = _multiply(matrix, _transpose(h))
        denominator_w = _multiply(w, _multiply(h, _transpose(h)))
        for i in range(rows):
            for j in range(rank):
                w[i][j] *= numerator_w[i][j] / (denominator_w[i][j] + epsilon)

        estimate = _multiply(w, h)
        error = _frobenius(
            [[matrix[i][j] - estimate[i][j] for j in range(columns)] for i in range(rows)]
        )
        if abs(previous - error) <= config.tolerance * max(previous, 1.0):
            break
        previous = error

    # Normalize W columns for comparable loadings; preserve WH by scaling H.
    for component in range(rank):
        scale = math.sqrt(sum(w[row][component] ** 2 for row in range(rows)))
        if scale <= epsilon:
            continue
        for row in range(rows):
            w[row][component] /= scale
        for column in range(columns):
            h[component][column] *= scale
    estimate = _multiply(w, h)
    error = _frobenius(
        [[matrix[i][j] - estimate[i][j] for j in range(columns)] for i in range(rows)]
    )
    return w, h, error


def _cosine(left: Sequence[float], right: Sequence[float]) -> float:
    numerator = sum(a * b for a, b in zip(left, right))
    denominator = math.sqrt(sum(a * a for a in left) * sum(b * b for b in right))
    return numerator / denominator if denominator else 1.0


def _stability(loadings: Sequence[list[list[float]]], rank: int) -> float:
    if len(loadings) < 2:
        return 1.0
    vectors = [
        [[run[component][tool] for tool in range(len(run[component]))] for component in range(rank)]
        for run in loadings
    ]
    scores: list[float] = []
    for left, right in itertools.combinations(vectors, 2):
        best = max(
            sum(_cosine(left[i], right[j]) for i, j in enumerate(permutation)) / rank
            for permutation in itertools.permutations(range(rank))
        )
        scores.append(best)
    return sum(scores) / len(scores) if scores else 1.0


def _entropy(values: Sequence[float]) -> float:
    total = sum(values)
    if total <= 0 or len(values) <= 1:
        return 0.0
    probabilities = [value / total for value in values if value > 0]
    raw = -sum(value * math.log(value) for value in probabilities)
    return raw / math.log(len(values))


def _diagnostics(
    h: list[list[float]], tools: Sequence[str], config: NMFConfig
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    diagnostics: list[dict[str, Any]] = []
    communities: dict[int, list[str]] = defaultdict(list)
    ambiguous: list[str] = []
    for tool_index, tool in enumerate(tools):
        values = [max(h[component][tool_index], 0.0) for component in range(len(h))]
        total = sum(values)
        normalized = [value / total for value in values] if total else [0.0] * len(values)
        ranked = sorted(enumerate(normalized), key=lambda item: (-item[1], item[0]))
        dominant, dominant_value = ranked[0]
        second_value = ranked[1][1] if len(ranked) > 1 else 0.0
        margin = dominant_value - second_value
        entropy = _entropy(values)
        weak = dominant_value < config.dominant_loading_threshold
        cross_loading = margin < config.loading_margin_threshold or entropy >= config.entropy_threshold
        diagnostics.append(
            {
                "tool": tool,
                "dominant_factor": dominant + 1,
                "dominant_loading": dominant_value,
                "second_highest_loading": second_value,
                "loading_margin": margin,
                "normalized_loading_distribution": normalized,
                "entropy": entropy,
                "classification": "weak_or_noisy" if weak else ("cross_loading" if cross_loading else "strongly_associated"),
            }
        )
        if cross_loading or weak:
            ambiguous.append(tool)
        else:
            communities[dominant].append(tool)
    return diagnostics, [{"factor": factor + 1, "tools": sorted(values), "soft_lock": True} for factor, values in sorted(communities.items()) if values], sorted(ambiguous)


def _control_summary(
    sessions: Sequence[EvidenceSession], role_records: Mapping[str, ToolRoleRecord]
) -> dict[str, Any]:
    control_tools = {name for name, record in role_records.items() if record.role != "domain"}
    sessions_used = {name: 0 for name in control_tools}
    calls = {name: 0 for name in control_tools}
    adjacency: dict[str, int] = defaultdict(int)
    role_counts: dict[str, int] = defaultdict(int)
    for name in control_tools:
        role_counts[role_records[name].role] += 1
    for session in sessions:
        seen: set[str] = set()
        for name in session.called_tools:
            if name not in control_tools:
                continue
            calls[name] += 1
            if name not in seen:
                sessions_used[name] += 1
                seen.add(name)
        for left, right in zip(session.called_tools, session.called_tools[1:]):
            if left in control_tools or right in control_tools:
                adjacency[f"{left}->{right}"] += 1
    return {
        "tool_count": len(control_tools),
        "control_plane_tool_count": sum(
            role_records[name].role in {"delegation", "coordination"}
            for name in control_tools
        ),
        "runtime_infrastructure_tool_count": sum(
            role_records[name].role == "runtime_infrastructure"
            for name in control_tools
        ),
        "tools": [
            {
                "tool": name,
                "role": role_records[name].role,
                "evidence": role_records[name].evidence,
                "confidence": role_records[name].confidence,
                "sessions_used": sessions_used[name],
                "calls": calls[name],
            }
            for name in sorted(control_tools)
        ],
        "role_counts": dict(sorted(role_counts.items())),
        "adjacency": dict(sorted(adjacency.items())),
        "delegation_calls": sum(calls[name] for name in control_tools if role_records[name].role == "delegation"),
        "coordination_calls": sum(calls[name] for name in control_tools if role_records[name].role == "coordination"),
    }


def run_nmf_screening(
    sessions: Iterable[EvidenceSession],
    domain_tools: Iterable[str],
    role_records: Mapping[str, ToolRoleRecord],
    *,
    config: NMFConfig | None = None,
    session_weights: Mapping[str, float] | None = None,
) -> NMFScreening:
    config = config or NMFConfig()
    _validate_config(config)
    session_list = [session for session in sessions if session.called_tools]
    tools = tuple(
        sorted(
            tool
            for tool in set(domain_tools)
            if role_records.get(tool) is None
            or role_records[tool].role == "domain"
        )
    )
    control = _control_summary(session_list, role_records)
    matrix_rows = _matrix(session_list, tools, session_weights) if tools else []
    matrix_sessions = [
        session.session_id for session in session_list if session.called_tools
    ]
    if not tools or not session_list:
        return NMFScreening(
            "no_matrix",
            config.__dict__,
            {
                "rows": len(matrix_rows),
                "columns": len(tools),
                "mode": config.matrix_mode,
                "session_ids": matrix_sessions if tools else [],
                "tools": list(tools),
                "values": matrix_rows,
            },
            (), (), None,
            {"strong_communities": [], "ambiguous_tools": [], "shared_candidates": [], "plausible_factor_counts": [], "search_units": []},
            control,
        )
    matrix = matrix_rows
    max_rank = min(config.max_factors, len(tools), len(matrix))
    counts = tuple(range(1, max_rank + 1))
    evaluations: list[dict[str, Any]] = []
    best_by_rank: dict[int, tuple[float, list[list[float]], list[list[float]], float]] = {}
    for rank in counts:
        runs = [_nmf(matrix, rank, seed, config) for seed in config.seeds]
        best = min(runs, key=lambda item: item[2])
        h_runs = [item[1] for item in runs]
        stability = _stability(
            [
                [
                    [run[component][tool] for tool in range(len(tools))]
                    for component in range(rank)
                ]
                for _w, run, _error in runs
            ],
            rank,
        )
        w, h, error = best
        diagnostics, communities, ambiguous = _diagnostics(h, tools, config)
        populated = len(communities)
        evaluations.append(
            {
                "factor_count": rank,
                "reconstruction_error": error,
                "relative_reconstruction_error": error / max(_frobenius(matrix), 1e-10),
                "factor_stability": stability,
                "materially_populated_factors": populated,
                "factor_tool_loadings": [dict(zip(tools, row)) for row in h],
                "session_factor_loadings": [dict(zip(range(1, rank + 1), row)) for row in w],
                "tool_diagnostics": diagnostics,
                "strong_communities": communities,
                "ambiguous_tools": ambiguous,
                "seeds": list(config.seeds),
            }
        )
        best_by_rank[rank] = (error, w, h, stability)
    selected = min(counts, key=lambda rank: (evaluations[rank - 1]["relative_reconstruction_error"], -evaluations[rank - 1]["factor_stability"], rank))
    selected_eval = evaluations[selected - 1]
    strong = selected_eval["strong_communities"]
    ambiguous = selected_eval["ambiguous_tools"]
    shared = sorted(
        tool
        for tool in ambiguous
        if any(tool in community["tools"] for evaluation in evaluations for community in evaluation["strong_communities"])
        or next((row for row in selected_eval["tool_diagnostics"] if row["tool"] == tool), {}).get("entropy", 0.0) >= config.entropy_threshold
    )
    hints = {
        "strong_communities": strong,
        "ambiguous_tools": ambiguous,
        "shared_candidates": shared,
        "plausible_factor_counts": [evaluation["factor_count"] for evaluation in evaluations if evaluation["materially_populated_factors"] >= 2],
        "search_units": [community["tools"] for community in strong],
        "soft_lock": True,
        "selected_factor_count": selected,
        "factor_count_is_not_agent_count": True,
    }
    return NMFScreening(
        "complete",
        config.__dict__,
        {
            "rows": len(matrix),
            "columns": len(tools),
            "mode": config.matrix_mode,
            "session_ids": matrix_sessions,
            "tools": list(tools),
            "values": matrix,
        },
        counts,
        tuple(evaluations),
        selected,
        hints,
        control,
    )
