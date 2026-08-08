from __future__ import annotations

import pytest
from optimize_agent_tools.measurement import ExperimentIdentity, SurfaceCondition, SurfaceRun
from optimize_agent_tools.replay_harness import ReplayObservation
from optimize_agent_tools.runtime_metrics import (
    Metric,
    MetricEvidence,
    from_replay_observation,
    from_surface_run,
)


def surface_run(**overrides: object) -> SurfaceRun:
    values: dict[str, object] = {
        "identity": ExperimentIdentity(
            experiment_id="exp",
            task_id="task",
            prompt_id="prompt",
            conversation_state_id="state",
            runtime="host",
            runtime_version="1",
            model="model",
            model_version="1",
        ),
        "condition": SurfaceCondition(
            "deferred", frozenset({"exec"}), frozenset({"file"})
        ),
        "actual_input_tokens": 100,
        "cached_input_tokens": 25,
        "serialized_tool_payload_chars": 400,
        "serialized_tool_payload_tokens": 100,
        "schema_measurement_method": "provider_usage",
        "selected_tools": ("exec",),
        "tool_selection_failures": 1,
        "tool_call_count": 1,
        "task_success": True,
        "quality_score": 0.9,
        "latency_seconds": 2.0,
    }
    values.update(overrides)
    return SurfaceRun(**values)


def test_surface_adapter_separates_loading_and_token_evidence() -> None:
    metrics = from_surface_run(surface_run())

    assert metrics.definitions.configured.value == ("exec", "file")
    assert metrics.definitions.loaded.value == ("exec",)
    assert metrics.definitions.deferred.value == ("file",)
    assert metrics.tokens.uncached_input.value == 75
    assert metrics.tokens.uncached_input.evidence.status == "inferred"
    assert metrics.tokens.billed_input.value is None
    assert metrics.tokens.billed_input.evidence.status == "unavailable"
    assert metrics.occupancy.tool_schema.value == 100
    assert metrics.occupancy.task_context.value is None


def test_surface_adapter_does_not_invent_uncached_input() -> None:
    metrics = from_surface_run(surface_run(cached_input_tokens=None))

    assert metrics.tokens.uncached_input.value is None
    assert metrics.tokens.uncached_input.evidence.status == "unavailable"


def test_replay_adapter_keeps_selection_and_coordination_separate() -> None:
    metrics = from_replay_observation(
        ReplayObservation(
            task_id="task",
            task_success=True,
            observed_replay_capability_covered=True,
            quality_score=1.0,
            agent_activation_path=("review", "file"),
            total_input_tokens=100,
            tool_definition_context_tokens=40,
            delegation_tokens=7,
            inter_agent_communication_tokens=3,
            turns=4,
            wall_clock_seconds=1.5,
            cached_input_tokens=20,
            billed_input_tokens=80,
            tool_selection_failures=2,
            configured_definitions=("exec", "file"),
            loaded_definitions=("exec",),
            deferred_definitions=("file",),
            selected_tools=("exec",),
        )
    )

    assert metrics.selection.selection_failures.value == 2
    assert metrics.coordination.delegation_tokens.value == 7
    assert metrics.coordination.inter_agent_communication_tokens.value == 3
    assert metrics.coordination.activations.value == 2
    assert metrics.coordination.handoffs.value == 1
    assert metrics.tokens.billed_input.value == 80
    assert metrics.tokens.uncached_input.value == 80
    assert metrics.tokens.uncached_input.evidence.status == "inferred"
    assert metrics.definitions.loaded.value == ("exec",)
    assert metrics.definitions.loaded.evidence.status == "measured"


def test_metric_rejects_missing_value_without_unavailable_evidence() -> None:
    evidence = MetricEvidence("measured", "test", "test", "tokens")

    with pytest.raises(ValueError, match="unavailable or unresolved"):
        Metric(None, evidence)


def test_runtime_metrics_record_preserves_evidence_metadata() -> None:
    record = from_surface_run(surface_run()).to_record()

    assert record["tokens"]["uncached_input"]["evidence"]["method"] == (
        "derived_total_minus_cached"
    )
    assert record["definitions"]["loaded"]["evidence"]["status"] == "measured"
