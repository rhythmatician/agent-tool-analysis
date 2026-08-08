from __future__ import annotations

import json

import pytest
from optimize_agent_tools.measurement import (
    ExperimentIdentity,
    SurfaceCondition,
    SurfaceRun,
    build_measurement_report,
    compare_surface_runs,
    write_measurement_report,
)


def identity(**overrides: object) -> ExperimentIdentity:
    values = {
        "experiment_id": "exp-001",
        "task_id": "task-001",
        "prompt_id": "prompt-001",
        "conversation_state_id": "state-001",
        "runtime": "controlled-runtime",
        "runtime_version": "1.2.3",
        "model": "model-x",
        "model_version": "2026-01-01",
        "temperature": 0.0,
        "seed": 7,
    }
    values.update(overrides)
    return ExperimentIdentity(**values)


def run(condition_id: str, **overrides: object) -> SurfaceRun:
    values = {
        "identity": identity(),
        "condition": SurfaceCondition(
            condition_id,
            exposed_tools=frozenset({"exec", "file"})
            if condition_id == "full"
            else frozenset({"exec"}),
            deferred_tools=frozenset(),
        ),
        "actual_input_tokens": 100 if condition_id == "full" else 70,
        "cached_input_tokens": 20 if condition_id == "full" else 15,
        "serialized_tool_payload_chars": 400 if condition_id == "full" else 180,
        "serialized_tool_payload_tokens": 100 if condition_id == "full" else 45,
        "schema_measurement_method": "provider_usage",
        "selected_tools": ("exec", "file") if condition_id == "full" else ("exec",),
        "tool_selection_failures": 0,
        "tool_call_count": 2 if condition_id == "full" else 1,
        "task_success": True,
        "quality_score": 0.9 if condition_id == "full" else 0.92,
        "latency_seconds": 2.0 if condition_id == "full" else 1.5,
    }
    values.update(overrides)
    return SurfaceRun(**values)


def test_comparison_requires_same_control_identity_and_reports_deltas() -> None:
    comparison = compare_surface_runs(run("full"), run("deferred"))

    assert comparison.condition_ids == ("full", "deferred")
    assert comparison.delta("actual_input_tokens") == -30
    assert comparison.delta("cached_input_tokens") == -5
    assert comparison.delta("serialized_tool_payload_tokens") == -55
    assert comparison.delta("latency_seconds") == pytest.approx(-0.5)
    assert comparison.delta("quality_score") == pytest.approx(0.02)
    assert comparison.exposed_tool_delta == {
        "removed": ["file"],
        "added": [],
    }
    assert comparison.selected_tool_delta == {
        "removed": ["file"],
        "added": [],
    }


def test_missing_provider_measurements_remain_unavailable() -> None:
    comparison = compare_surface_runs(
        run("full", cached_input_tokens=None, serialized_tool_payload_tokens=None),
        run("deferred", cached_input_tokens=None, serialized_tool_payload_tokens=None),
    )

    assert comparison.delta("cached_input_tokens") is None
    assert comparison.delta("serialized_tool_payload_tokens") is None


def test_comparison_rejects_uncontrolled_pairs() -> None:
    with pytest.raises(ValueError, match="same controlled identity"):
        compare_surface_runs(
            run("full"),
            run("deferred", identity=identity(model="different-model")),
        )


def test_run_validates_nonnegative_and_surface_measurements() -> None:
    with pytest.raises(ValueError, match="cannot be negative"):
        run("full", actual_input_tokens=-1)

    with pytest.raises(ValueError, match="quality_score must be between"):
        run("full", quality_score=1.1)

    with pytest.raises(ValueError, match="schema measurement method"):
        run("full", schema_measurement_method="")


def test_report_is_json_serializable_and_round_trips_to_file(tmp_path) -> None:
    report = build_measurement_report([run("full"), run("deferred")])

    assert report["experiment"]["runtime"] == "controlled-runtime"
    assert report["runs"]["full"]["exposed_tools"] == ["exec", "file"]
    assert report["comparison"]["deltas"]["actual_input_tokens"] == -30

    output = tmp_path / "measurement.json"
    write_measurement_report(output, [run("full"), run("deferred")])
    loaded = json.loads(output.read_text(encoding="utf-8"))
    assert loaded == report
