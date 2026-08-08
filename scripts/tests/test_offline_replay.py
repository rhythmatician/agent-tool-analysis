from __future__ import annotations

from types import SimpleNamespace
from optimize_agent_tools.analysis_pipeline import (
    apply_offline_replay_result,
)
from optimize_agent_tools.capture_runner import capture_paired_observations
from optimize_agent_tools.offline_replay import (
    assess_recorded_replay,
    run_recorded_replay,
)
from optimize_agent_tools.replay_harness import ReplayObservation, ReplayTask
from optimize_agent_tools.__main__ import _validate_args
from replay_architectures import build_report

BASELINE = "pruned_flat_baseline"
CANDIDATE = "partition_k02_0001"


def report() -> dict:
    return {
        "specialist_recommendation": {
            "status": "provisional",
            "direction": "2-agent architecture",
            "confidence": "moderate-low",
            "best_guess_architecture": "two_specialists",
            "best_guess_candidate_id": CANDIDATE,
            "why": ["directional evidence"],
            "required_validation": "replay or A/B",
            "pareto_candidate_ids": [CANDIDATE],
        },
        "architecture_manifest": {
            "baseline_architecture_id": BASELINE,
            "historical_tool_capability_tools": ["shared", "a", "b"],
            "architectures": [
                {
                    "architecture_id": BASELINE,
                    "parent_tools": ["shared", "a", "b"],
                    "agents": {},
                },
                {
                    "architecture_id": CANDIDATE,
                    "parent_tools": ["shared"],
                    "agents": {"agent_01": ["a", "b"]},
                },
            ],
        },
        "pruned_flat_baseline": {"tools_retained": ["shared", "a", "b"]},
    }


def bundle() -> dict:
    def row(path: list[str], context: int) -> dict:
        return {
            "task_id": "task-1",
            "task_success": True,
            "observed_replay_capability_covered": True,
            "quality_score": 1.0,
            "agent_activation_path": path,
            "tool_call_failures": 0,
            "routing_failure": False,
            "missed_agent_activation": False,
            "unnecessary_agent_activation": False,
            "total_input_tokens": 10,
            "tool_definition_context_tokens": context,
            "delegation_tokens": 0,
            "inter_agent_communication_tokens": 0,
            "turns": 1,
            "wall_clock_seconds": 0.1,
        }

    observations = {
        BASELINE: [row([], 100)],
        CANDIDATE: [row(["agent_01"], 80)],
    }
    return {
        "metadata": {
            "mode": "recorded_observations",
            "executor": "recorded_observations",
            "side_effect_free": True,
            "deterministic": True,
            "architecture_manifest": report()["architecture_manifest"],
        },
        "tasks": [
            {
                "task_id": "task-1",
                "activation_paths": {CANDIDATE: ["agent_01"]},
            }
        ],
        "observations": observations,
    }


def test_recorded_bundle_is_ready_only_with_explicit_safe_metadata() -> None:
    readiness = assess_recorded_replay(report(), bundle())

    assert readiness.ready is True
    assert readiness.candidate_id == CANDIDATE
    assert readiness.reasons == ()

    missing_marker = bundle()
    del missing_marker["metadata"]["side_effect_free"]
    assert assess_recorded_replay(report(), missing_marker).ready is False

    live_bundle = bundle()
    live_bundle["metadata"]["executor"] = "live_model"
    assert assess_recorded_replay(report(), live_bundle).ready is False


def test_recorded_bundle_requires_a_pareto_candidate() -> None:
    not_a_finalist = bundle()
    not_a_finalist["metadata"]["architecture_manifest"] = report()[
        "architecture_manifest"
    ]
    recommendation = report()["specialist_recommendation"]
    recommendation["best_guess_candidate_id"] = BASELINE
    not_a_finalist_report = report()
    not_a_finalist_report["specialist_recommendation"] = recommendation

    readiness = assess_recorded_replay(not_a_finalist_report, not_a_finalist)

    assert readiness.ready is False
    assert any("baseline" in reason for reason in readiness.reasons)


def test_passing_offline_replay_promotes_to_replay_validated() -> None:
    recommendation = report()["specialist_recommendation"]
    updated = apply_offline_replay_result(
        recommendation,
        CANDIDATE,
        {"passed": True, "quality_delta": 0.0, "context_tokens_delta": -10},
    )

    assert updated["status"] == "replay_validated"
    assert updated["evidence_status"] == "replay_validated"
    assert updated["replay_candidate_id"] == CANDIDATE
    assert "production" in updated["required_validation"]


def test_recorded_replay_uses_the_frozen_baseline_gate() -> None:
    replay_report = run_recorded_replay(report(), bundle())

    assert replay_report["comparisons"][CANDIDATE]["passed"] is True


def test_failing_offline_replay_rejects_the_hypothesis() -> None:
    recommendation = report()["specialist_recommendation"]
    updated = apply_offline_replay_result(
        recommendation,
        CANDIDATE,
        {"passed": False, "quality_delta": -0.2, "context_tokens_delta": -10},
    )

    assert updated["status"] == "replay_rejected"
    assert updated["evidence_status"] == "replay_rejected"
    assert updated["rejected_candidate_id"] == CANDIDATE
    assert "quality" in updated["why"][-1]


def test_captured_pairs_run_baseline_and_candidate_without_synthetic_rows() -> None:
    calls: list[str] = []

    def execute(task, architecture, path):
        calls.append(architecture.architecture_id)
        return ReplayObservation(
            task_id=task.task_id,
            task_success=True,
            observed_replay_capability_covered=True,
            quality_score=1.0,
            agent_activation_path=path,
            total_input_tokens=10,
            tool_definition_context_tokens=100,
            turns=1,
            wall_clock_seconds=0.1,
        )

    captured = capture_paired_observations(
        [ReplayTask("task-1", {CANDIDATE: ("agent_01",)})],
        report()["architecture_manifest"]
        | {"provisional_architecture_ids": [CANDIDATE]},
        CANDIDATE,
        execute,
    )

    assert calls == [BASELINE, CANDIDATE]
    assert set(captured["observations"]) == {BASELINE, CANDIDATE}
    assert captured["metadata"]["synthetic"] is False
    assert captured["metadata"]["executor"] == "caller_supplied"


def test_captured_bundle_is_explicit_replay_input_but_not_auto_replay_ready() -> None:
    captured = capture_paired_observations(
        [ReplayTask("task-1", {CANDIDATE: ("agent_01",)})],
        report()["architecture_manifest"]
        | {"provisional_architecture_ids": [CANDIDATE]},
        CANDIDATE,
        lambda task, architecture, path: ReplayObservation(
            task_id=task.task_id,
            task_success=True,
            observed_replay_capability_covered=True,
            quality_score=1.0,
            agent_activation_path=path,
            total_input_tokens=10,
            tool_definition_context_tokens=(100 if architecture.architecture_id == BASELINE else 80),
            turns=1,
            wall_clock_seconds=0.1,
        ),
    )

    assert assess_recorded_replay(report(), captured).ready is False
    assert any("recorded_observations" in reason for reason in assess_recorded_replay(report(), captured).reasons)


def test_captured_bundle_feeds_existing_replay_harness() -> None:
    captured = capture_paired_observations(
        [ReplayTask("task-1", {CANDIDATE: ("agent_01",)})],
        report()["architecture_manifest"]
        | {"provisional_architecture_ids": [CANDIDATE]},
        CANDIDATE,
        lambda task, architecture, path: ReplayObservation(
            task_id=task.task_id,
            task_success=True,
            observed_replay_capability_covered=True,
            quality_score=1.0,
            agent_activation_path=path,
            total_input_tokens=10,
            tool_definition_context_tokens=(
                100 if architecture.architecture_id == BASELINE else 80
            ),
            turns=1,
            wall_clock_seconds=0.1,
        ),
    )

    replay_report = build_report(
        captured,
        {BASELINE: report()["pruned_flat_baseline"]},
        captured["manifest"],
    )

    assert set(replay_report["architectures"]) == {BASELINE, CANDIDATE}
    assert replay_report["comparisons"][CANDIDATE]["passed"] is True


def test_advanced_replay_requires_explicit_candidate_selection() -> None:
    args = SimpleNamespace(
        min_tool_sessions=1,
        similarity_threshold=0.35,
        global_usage_threshold=0.6,
        min_cluster_size=2,
        min_cluster_sessions=1,
        delegation_overhead_tokens=0,
        max_agents=2,
        communication_tokens_per_handoff=0.0,
        offline_replay_input="bundle.json",
        offline_replay_candidate=None,
    )

    try:
        _validate_args(args, (0.5,))
    except SystemExit as error:
        assert "explicitly" in str(error)
    else:
        raise AssertionError("replay input must require an explicit candidate")
