from optimize_agent_tools.runtime_recommendation import (
    RecommendationThresholds,
    recommend_runtime_alternatives,
)


def row(
    alternative_id: str,
    *,
    supported: bool | None = True,
    coverage: bool | None = True,
    tokens: tuple[float, float] | None = None,
    evidence: str = "measured",
) -> dict[str, object]:
    comparison = {}
    if tokens is not None:
        baseline, candidate = tokens
        comparison["tokens.total_input"] = {
            "baseline_value": baseline,
            "candidate_value": candidate,
            "delta": candidate - baseline,
        }
    return {
        "alternative_id": alternative_id,
        "supported": supported,
        "capability_coverage": coverage,
        "coverage_reason": "missing required capabilities" if coverage is False else "ok",
        "metric_evidence_status": {
            "tokens": evidence,
            "occupancy": evidence,
            "selection": evidence,
            "coordination": evidence,
            "outcomes": evidence,
            "loading": evidence,
        },
        "comparison": comparison,
    }


def test_policy_rejects_unsupported_and_capability_losing_alternatives() -> None:
    result = recommend_runtime_alternatives(
        [
            row("do_nothing"),
            row("runtime_dynamic_retrieval", supported=False, tokens=(1000, 700)),
            row("peer_specialists", coverage=False, tokens=(1000, 700)),
        ]
    )

    assert result["preferred_option"] == "do_nothing"
    assert result["recommendation_strength"] == "supported"
    assert {item["alternative_id"] for item in result["rejected_options"]} == {
        "runtime_dynamic_retrieval",
        "peer_specialists",
    }


def test_policy_prefers_measured_simpler_option_over_weaker_modeled_gain() -> None:
    result = recommend_runtime_alternatives(
        [
            row("do_nothing", tokens=(1000, 1000)),
            row("runtime_dynamic_retrieval", tokens=(1000, 850), evidence="counterfactual"),
            row("prune_only", tokens=(1000, 880), evidence="measured"),
        ]
    )

    assert result["preferred_option"] == "prune_only"
    assert result["recommendation_strength"] == "supported"
    assert result["runner_up_options"] == ["runtime_dynamic_retrieval"]


def test_policy_returns_provisional_for_material_but_weak_evidence() -> None:
    result = recommend_runtime_alternatives(
        [
            row("do_nothing", tokens=(1000, 1000), evidence="measured"),
            row(
                "runtime_dynamic_retrieval",
                tokens=(1000, 700),
                evidence="counterfactual",
            ),
        ]
    )

    assert result["preferred_option"] == "runtime_dynamic_retrieval"
    assert result["recommendation_strength"] == "provisional"
    assert any("incomplete" in reason for reason in result["why"])


def test_policy_thresholds_are_explicit_and_configurable() -> None:
    result = recommend_runtime_alternatives(
        [
            row("do_nothing", tokens=(1000, 1000)),
            row("prune_only", tokens=(1000, 960)),
        ],
        thresholds=RecommendationThresholds(material_relative_improvement=0.20),
    )

    assert result["preferred_option"] == "do_nothing"
    assert result["thresholds"]["material_relative_improvement"] == 0.20
