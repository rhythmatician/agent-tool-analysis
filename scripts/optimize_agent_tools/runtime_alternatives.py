"""Host-neutral construction and comparison of runtime alternatives.

Alternative identity and strategy support live outside ``RuntimeMetrics``.  The
metrics contract remains responsible only for measurements and their evidence;
this module supplies the normalized strategy table that consumes those metrics
without choosing a winner.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Iterable, Mapping

from .runtime_metrics import RuntimeMetrics

ALTERNATIVE_IDS = (
    "do_nothing",
    "prune_only",
    "streamlined_static",
    "runtime_dynamic_retrieval",
    "peer_specialists",
    "coordinator_children",
    "hybrid",
)

_METRIC_GROUPS = {
    "loading": "definitions",
    "tokens": "tokens",
    "occupancy": "occupancy",
    "selection": "selection",
    "coordination": "coordination",
    "outcomes": "outcome",
}


@dataclass(frozen=True)
class AlternativePlan:
    """Normalized strategy metadata, independent of host syntax."""

    alternative_id: str
    architecture_id: str | None
    topology: str
    loading_policy: str
    supported: bool | None
    support_reason: str
    runtime_requirements: tuple[str, ...] = ()
    assumptions: tuple[str, ...] = ()
    capability_coverage: bool | None = None
    coverage_reason: str = "capability coverage was not established"

    def __post_init__(self) -> None:
        if self.alternative_id not in ALTERNATIVE_IDS:
            raise ValueError(f"Unsupported alternative: {self.alternative_id}")
        if self.supported is True and not self.architecture_id:
            raise ValueError("Supported alternatives need an architecture ID.")


@dataclass(frozen=True)
class AlternativeEvaluation:
    """One table row; deliberately contains no recommendation decision."""

    plan: AlternativePlan
    runtime_metrics: RuntimeMetrics | None
    metric_evidence_status: Mapping[str, str]
    comparison: Mapping[str, Mapping[str, Any]]

    def to_record(self) -> dict[str, Any]:
        record = asdict(self.plan)
        record.update(
            {
                "metric_evidence_status": dict(self.metric_evidence_status),
                "runtime_metrics": (
                    self.runtime_metrics.to_record()
                    if self.runtime_metrics is not None
                    else None
                ),
                "comparison": {
                    key: dict(value) for key, value in self.comparison.items()
                },
            }
        )
        return record


def _topology_architecture_ids(
    manifest: Mapping[str, Any],
) -> dict[str, list[str]]:
    result = {"flat": [], "peer": [], "coordinator_children": []}
    for architecture in manifest.get("architectures", []):
        if not isinstance(architecture, Mapping):
            continue
        architecture_id = str(architecture.get("architecture_id", ""))
        topology = str(architecture.get("topology", ""))
        if topology == "coordinator_specialists":
            topology = "coordinator_children"
        if architecture_id and topology in result:
            result[topology].append(architecture_id)
    return result


def build_alternative_plans(
    *,
    manifest: Mapping[str, Any],
    current_architecture_id: str = "current_runtime_configuration",
    dynamic_retrieval_supported: bool | None = None,
    hybrid_supported: bool | None = None,
) -> tuple[AlternativePlan, ...]:
    """Construct the fixed normalized alternative set without ranking it."""
    topology_ids = _topology_architecture_ids(manifest)
    baseline_id = str(
        manifest.get("baseline_architecture_id", "pruned_flat_baseline")
    )
    static_ids = [
        architecture_id
        for architecture_id in topology_ids["flat"]
        if architecture_id != baseline_id
    ]
    peer_ids = topology_ids["peer"]
    coordinator_ids = topology_ids["coordinator_children"]
    historical = set(manifest.get("historical_tool_capability_tools", ()))

    def architecture_coverage(
        architecture_id: str | None,
    ) -> tuple[bool | None, str]:
        if not architecture_id or not historical:
            return None, "historical capability surface was not supplied"
        architecture = next(
            (
                item
                for item in manifest.get("architectures", ())
                if isinstance(item, Mapping)
                and str(item.get("architecture_id")) == architecture_id
            ),
            None,
        )
        if architecture is None:
            return None, "architecture membership was not supplied"
        available = set(architecture.get("parent_tools", ()))
        for agent in (architecture.get("agents", {}) or {}).values():
            if isinstance(agent, Mapping):
                available.update(agent.get("tools", ()))
            else:
                available.update(agent)
        missing = sorted(historical - available)
        if missing:
            return False, "missing required capabilities: " + ", ".join(missing)
        return True, "all historical capabilities are retained"

    def optional_plan(
        alternative_id: str,
        architecture_ids: list[str],
        topology: str,
        loading_policy: str,
        reason: str,
        requirements: tuple[str, ...] = (),
    ) -> AlternativePlan:
        architecture_id = architecture_ids[0] if architecture_ids else None
        coverage, coverage_reason = architecture_coverage(architecture_id)
        return AlternativePlan(
            alternative_id,
            architecture_id,
            topology,
            loading_policy,
            True if architecture_ids else False,
            reason if architecture_ids else f"{reason}; no concrete architecture is available",
            requirements,
            capability_coverage=coverage if architecture_ids else None,
            coverage_reason=coverage_reason,
        )

    return (
        AlternativePlan(
            "do_nothing",
            current_architecture_id,
            "current",
            "current",
            True,
            "current runtime configuration is always represented",
            assumptions=("current configuration is the comparison baseline",),
            capability_coverage=True,
            coverage_reason="current configuration is the required capability baseline",
        ),
        AlternativePlan(
            "prune_only",
            baseline_id,
            "flat",
            "static_pruned",
            True,
            "dependency-closed pruned flat baseline is available",
            capability_coverage=architecture_coverage(baseline_id)[0],
            coverage_reason=architecture_coverage(baseline_id)[1],
        ),
        optional_plan(
            "streamlined_static",
            static_ids,
            "flat",
            "static_selected",
            "a concrete static streamlined architecture is available",
            ("static tool assignment",),
        ),
        AlternativePlan(
            "runtime_dynamic_retrieval",
            "runtime_dynamic_retrieval"
            if dynamic_retrieval_supported is True
            else None,
            "flat",
            "dynamic_retrieval",
            dynamic_retrieval_supported,
            (
                "runtime loading/deferred-selection support is available"
                if dynamic_retrieval_supported is True
                else "runtime loading/deferred-selection support is not established"
            ),
            ("runtime selection telemetry", "deferred definition support"),
            coverage_reason="dynamic retrieval capability coverage requires runtime evidence",
        ),
        optional_plan(
            "peer_specialists",
            peer_ids,
            "peer",
            "static_partitioned",
            "a concrete peer partition is available",
            ("agent delegation", "peer routing"),
        ),
        optional_plan(
            "coordinator_children",
            coordinator_ids,
            "coordinator_children",
            "static_partitioned",
            "a concrete coordinator/child partition is available",
            ("coordinator routing", "child activation"),
        ),
        AlternativePlan(
            "hybrid",
            "hybrid" if hybrid_supported is True else None,
            "composed",
            "static_plus_dynamic_retrieval",
            hybrid_supported,
            (
                "static and dynamic composition is supported"
                if hybrid_supported is True
                else "static and dynamic composition is not established"
            ),
            ("static assignment", "runtime retrieval", "routing"),
            coverage_reason="hybrid capability coverage requires static and runtime evidence",
        ),
    )


def _metric_status(metrics: RuntimeMetrics | None, group: str) -> str:
    if metrics is None:
        return "unavailable"
    section = getattr(metrics, _METRIC_GROUPS[group])
    statuses = [metric.evidence.status for metric in vars(section).values()]
    if not statuses:
        return "unavailable"
    if any(status in {"unresolved", "unavailable"} for status in statuses):
        return "partial"
    if all(status == "measured" for status in statuses):
        return "measured"
    if any(status == "counterfactual" for status in statuses):
        return "counterfactual"
    if any(status == "inferred" for status in statuses):
        return "inferred"
    return "estimated"


def _numeric_metrics(metrics: RuntimeMetrics | None) -> dict[str, float]:
    if metrics is None:
        return {}
    values: dict[str, float] = {}
    for group_name, section_name in _METRIC_GROUPS.items():
        section = getattr(metrics, section_name)
        for field_name, metric in vars(section).items():
            if isinstance(metric.value, (int, float)) and not isinstance(metric.value, bool):
                values[f"{group_name}.{field_name}"] = float(metric.value)
    return values


def evaluate_alternatives(
    plans: Iterable[AlternativePlan],
    metrics_by_alternative: Mapping[str, RuntimeMetrics] | None = None,
    *,
    comparison_baseline: str = "do_nothing",
) -> tuple[AlternativeEvaluation, ...]:
    """Evaluate every plan through ``RuntimeMetrics`` without selecting one."""
    metrics_by_alternative = metrics_by_alternative or {}
    baseline = _numeric_metrics(metrics_by_alternative.get(comparison_baseline))
    evaluations = []
    for plan in plans:
        metrics = metrics_by_alternative.get(plan.alternative_id)
        comparison = {
            key: {
                "baseline_alternative": comparison_baseline,
                "baseline_value": baseline_value,
                "candidate_value": value,
                "delta": value - baseline_value,
            }
            for key, value in _numeric_metrics(metrics).items()
            if (baseline_value := baseline.get(key)) is not None
        }
        evaluations.append(
            AlternativeEvaluation(
                plan=plan,
                runtime_metrics=metrics,
                metric_evidence_status={
                    group: _metric_status(metrics, group) for group in _METRIC_GROUPS
                },
                comparison=comparison,
            )
        )
    return tuple(evaluations)


def build_runtime_alternatives_report(
    *,
    manifest: Mapping[str, Any],
    metrics_by_alternative: Mapping[str, RuntimeMetrics] | None = None,
    current_architecture_id: str = "current_runtime_configuration",
    dynamic_retrieval_supported: bool | None = None,
    hybrid_supported: bool | None = None,
) -> list[dict[str, Any]]:
    """Build the stable alternatives table consumed by reports and callers."""
    plans = build_alternative_plans(
        manifest=manifest,
        current_architecture_id=current_architecture_id,
        dynamic_retrieval_supported=dynamic_retrieval_supported,
        hybrid_supported=hybrid_supported,
    )
    return [
        evaluation.to_record()
        for evaluation in evaluate_alternatives(plans, metrics_by_alternative)
    ]
