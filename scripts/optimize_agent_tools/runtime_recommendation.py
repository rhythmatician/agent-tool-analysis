"""Conservative, lexicographic policy over runtime alternative rows."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Iterable, Mapping

DEFAULT_COMPLEXITY_ORDER = (
    "do_nothing",
    "prune_only",
    "streamlined_static",
    "runtime_dynamic_retrieval",
    "peer_specialists",
    "coordinator_children",
    "hybrid",
)

_LOWER_IS_BETTER = {
    "tokens.total_input",
    "tokens.cached_input",
    "tokens.uncached_input",
    "tokens.billed_input",
    "occupancy.tool_schema",
    "occupancy.task_context",
    "occupancy.total",
    "selection.selection_failures",
    "selection.routing_failures",
    "selection.missed_activations",
    "selection.unnecessary_activations",
    "coordination.delegation_tokens",
    "coordination.inter_agent_communication_tokens",
    "coordination.activations",
    "coordination.handoffs",
    "coordination.turns",
    "coordination.latency_seconds",
}
_HIGHER_IS_BETTER = {
    "outcomes.task_success",
    "outcomes.quality",
    "outcomes.observed_capability_coverage",
    "outcomes.historical_capability_coverage",
}
_EVIDENCE_RANK = {
    "unavailable": 0,
    "partial": 1,
    "counterfactual": 2,
    "estimated": 3,
    "inferred": 4,
    "measured": 5,
}


@dataclass(frozen=True)
class RecommendationThresholds:
    """Explicit policy knobs; none are hidden in the ranking implementation."""

    material_relative_improvement: float = 0.10
    material_absolute_token_improvement: float = 50.0
    minimum_material_dimensions: int = 1
    minimum_supported_evidence_dimensions: int = 1
    supported_evidence_statuses: tuple[str, ...] = ("measured", "inferred")
    complexity_order: tuple[str, ...] = DEFAULT_COMPLEXITY_ORDER

    def __post_init__(self) -> None:
        if self.material_relative_improvement < 0:
            raise ValueError("material_relative_improvement cannot be negative")
        if self.material_absolute_token_improvement < 0:
            raise ValueError("material_absolute_token_improvement cannot be negative")
        if self.minimum_material_dimensions < 1:
            raise ValueError("minimum_material_dimensions must be positive")
        if self.minimum_supported_evidence_dimensions < 1:
            raise ValueError("minimum_supported_evidence_dimensions must be positive")
        if len(set(self.complexity_order)) != len(self.complexity_order):
            raise ValueError("complexity_order must contain unique alternatives")

    def to_record(self) -> dict[str, Any]:
        return asdict(self)


def _complexity_rank(alternative_id: str, thresholds: RecommendationThresholds) -> int:
    try:
        return thresholds.complexity_order.index(alternative_id)
    except ValueError:
        return len(thresholds.complexity_order)


def _improvements(
    row: Mapping[str, Any], thresholds: RecommendationThresholds
) -> list[dict[str, Any]]:
    improvements: list[dict[str, Any]] = []
    for key, comparison in (row.get("comparison") or {}).items():
        baseline = comparison.get("baseline_value")
        candidate = comparison.get("candidate_value")
        if not isinstance(baseline, (int, float)) or not isinstance(
            candidate, (int, float)
        ):
            continue
        if key in _LOWER_IS_BETTER:
            absolute = float(baseline) - float(candidate)
        elif key in _HIGHER_IS_BETTER:
            absolute = float(candidate) - float(baseline)
        else:
            continue
        relative = absolute / abs(float(baseline)) if baseline else 0.0
        material = relative >= thresholds.material_relative_improvement
        if (
            key.startswith("tokens.")
            and absolute >= thresholds.material_absolute_token_improvement
        ):
            material = True
        if material:
            improvements.append(
                {
                    "metric": key,
                    "absolute_improvement": absolute,
                    "relative_improvement": relative,
                }
            )
    return improvements


def _evidence_summary(
    row: Mapping[str, Any],
    baseline: Mapping[str, Any],
    improvements: Iterable[Mapping[str, Any]],
    thresholds: RecommendationThresholds,
) -> tuple[int, int, bool]:
    dimensions = {str(item["metric"]).split(".", 1)[0] for item in improvements}
    candidate_status = row.get("metric_evidence_status") or {}
    baseline_status = baseline.get("metric_evidence_status") or {}
    supported = 0
    score = 0
    for dimension in dimensions:
        candidate_value = str(candidate_status.get(dimension, "unavailable"))
        baseline_value = str(baseline_status.get(dimension, "unavailable"))
        score += min(
            _EVIDENCE_RANK.get(candidate_value, 0),
            _EVIDENCE_RANK.get(baseline_value, 0),
        )
        if (
            candidate_value in thresholds.supported_evidence_statuses
            and baseline_value in thresholds.supported_evidence_statuses
        ):
            supported += 1
    return (
        supported,
        score,
        supported >= thresholds.minimum_supported_evidence_dimensions,
    )


def _has_runtime_evidence(row: Mapping[str, Any]) -> bool:
    statuses = row.get("metric_evidence_status") or {}
    return any(status != "unavailable" for status in statuses.values())


def _no_material_reason(
    row: Mapping[str, Any], thresholds: RecommendationThresholds
) -> str:
    if not row.get("comparison"):
        return "no comparable runtime metric evidence against do_nothing"
    return "runtime deltas do not meet configured materiality thresholds"


def recommend_runtime_alternatives(
    alternatives: Iterable[Mapping[str, Any]],
    *,
    thresholds: RecommendationThresholds | None = None,
) -> dict[str, Any]:
    """Choose the simplest materially useful option without a weighted score."""
    thresholds = thresholds or RecommendationThresholds()
    rows = {str(row.get("alternative_id")): row for row in alternatives}
    baseline = rows.get("do_nothing")
    if baseline is None:
        return {
            "preferred_option": None,
            "preferred_option_label": "none",
            "recommendation_strength": "none",
            "runner_up_options": [],
            "why": ["the required do_nothing comparison alternative is missing"],
            "rejected_options": [],
            "thresholds": thresholds.to_record(),
        }

    rejected: list[dict[str, Any]] = []
    viable: list[dict[str, Any]] = []
    for alternative_id, row in rows.items():
        if alternative_id == "do_nothing":
            continue
        reasons: list[str] = []
        if row.get("supported") is False:
            reasons.append("alternative is unsupported")
        if row.get("capability_coverage") is False:
            reasons.append(
                row.get("coverage_reason", "required capability coverage is lost")
            )
        improvements = _improvements(row, thresholds)
        if len(improvements) < thresholds.minimum_material_dimensions:
            reasons.append(_no_material_reason(row, thresholds))
        supported_evidence, evidence_score, evidence_is_supported = _evidence_summary(
            row, baseline, improvements, thresholds
        )
        if reasons:
            rejected.append({"alternative_id": alternative_id, "reasons": reasons})
            continue
        viable.append(
            {
                "alternative_id": alternative_id,
                "row": row,
                "improvements": improvements,
                "supported_evidence": supported_evidence,
                "evidence_score": evidence_score,
                "evidence_is_supported": evidence_is_supported,
                "coverage_is_known": row.get("capability_coverage") is not None,
                "complexity": _complexity_rank(alternative_id, thresholds),
            }
        )

    if not viable:
        baseline_is_observed = _has_runtime_evidence(baseline)
        return {
            "preferred_option": "do_nothing",
            "preferred_option_label": "no architecture change",
            "recommendation_strength": "supported"
            if baseline_is_observed
            else "provisional",
            "runner_up_options": [],
            "why": (
                [
                    "no supported alternative has a material, evidence-backed advantage",
                    "the current runtime remains the conservative baseline",
                ]
                if baseline_is_observed
                else [
                    "no comparable runtime metrics establish a material advantage",
                    "no architecture change is the conservative fallback, not proof that current exposure is optimal",
                ]
            ),
            "rejected_options": rejected,
            "thresholds": thresholds.to_record(),
        }

    viable.sort(
        key=lambda item: (
            not item["evidence_is_supported"],
            -item["evidence_score"],
            item["complexity"],
            -max(item["improvements"][0]["relative_improvement"], 0.0),
            item["alternative_id"],
        )
    )
    best = viable[0]
    tied = [
        item
        for item in viable
        if (
            item["evidence_is_supported"],
            item["evidence_score"],
            item["complexity"],
        )
        == (
            best["evidence_is_supported"],
            best["evidence_score"],
            best["complexity"],
        )
    ]
    if len(tied) > 1 and best["improvements"] == tied[1]["improvements"]:
        return {
            "preferred_option": None,
            "preferred_option_label": "none",
            "recommendation_strength": "none",
            "runner_up_options": [item["alternative_id"] for item in tied],
            "why": [
                "multiple alternatives remain equivalent under the configured thresholds"
            ],
            "rejected_options": rejected,
            "thresholds": thresholds.to_record(),
        }

    strength = (
        "supported"
        if best["evidence_is_supported"]
        and best["row"].get("supported") is True
        and best["coverage_is_known"]
        and best["row"].get("capability_coverage") is True
        else "provisional"
    )
    why = [
        "preserves required capability coverage",
        f"has {len(best['improvements'])} material improvement dimension(s)",
    ]
    if strength == "provisional":
        why.append("the advantage depends on incomplete or modeled runtime evidence")
    return {
        "preferred_option": best["alternative_id"],
        "preferred_option_label": best["alternative_id"].replace("_", " "),
        "recommendation_strength": strength,
        "runner_up_options": [item["alternative_id"] for item in viable[1:]],
        "why": why,
        "rejected_options": rejected,
        "thresholds": thresholds.to_record(),
    }
