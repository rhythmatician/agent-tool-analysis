"""Controlled measurements for comparing exposed tool surfaces."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


@dataclass(frozen=True)
class ExperimentIdentity:
    """Values that must remain fixed across paired surface conditions."""

    experiment_id: str
    task_id: str
    prompt_id: str
    conversation_state_id: str
    runtime: str
    runtime_version: str
    model: str
    model_version: str
    temperature: float = 0.0
    seed: int | None = None

    def __post_init__(self) -> None:
        for field_name in (
            "experiment_id",
            "task_id",
            "prompt_id",
            "conversation_state_id",
            "runtime",
            "runtime_version",
            "model",
            "model_version",
        ):
            if not isinstance(getattr(self, field_name), str) or not getattr(
                self, field_name
            ):
                raise ValueError(f"{field_name} must be a non-empty string.")
        if self.temperature < 0:
            raise ValueError("temperature cannot be negative.")


@dataclass(frozen=True)
class SurfaceCondition:
    """The tool surface presented to one otherwise-identical run."""

    condition_id: str
    exposed_tools: frozenset[str]
    deferred_tools: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        if not self.condition_id:
            raise ValueError("condition_id must be a non-empty string.")
        _validate_tools(self.exposed_tools, "exposed_tools")
        _validate_tools(self.deferred_tools, "deferred_tools")
        overlap = self.exposed_tools & self.deferred_tools
        if overlap:
            raise ValueError(
                "exposed_tools and deferred_tools must be disjoint: "
                + ", ".join(sorted(overlap))
            )

    @property
    def available_tools(self) -> frozenset[str]:
        """Tools represented by the condition, whether exposed or deferred."""
        return self.exposed_tools | self.deferred_tools


@dataclass(frozen=True)
class SurfaceRun:
    """Privacy-safe evidence returned by one controlled runtime invocation."""

    identity: ExperimentIdentity
    condition: SurfaceCondition
    actual_input_tokens: int
    cached_input_tokens: int | None
    serialized_tool_payload_chars: int | None
    serialized_tool_payload_tokens: int | None
    schema_measurement_method: str
    selected_tools: tuple[str, ...]
    tool_selection_failures: int
    tool_call_count: int
    task_success: bool
    quality_score: float
    latency_seconds: float

    def __post_init__(self) -> None:
        _nonnegative(self.actual_input_tokens, "actual_input_tokens")
        _optional_nonnegative(self.cached_input_tokens, "cached_input_tokens")
        _optional_nonnegative(
            self.serialized_tool_payload_chars, "serialized_tool_payload_chars"
        )
        _optional_nonnegative(
            self.serialized_tool_payload_tokens, "serialized_tool_payload_tokens"
        )
        _nonnegative(self.tool_selection_failures, "tool_selection_failures")
        _nonnegative(self.tool_call_count, "tool_call_count")
        _nonnegative(self.latency_seconds, "latency_seconds")
        if not self.schema_measurement_method:
            raise ValueError("schema measurement method must be non-empty.")
        _validate_tools(self.selected_tools, "selected_tools")
        if not 0 <= self.quality_score <= 1:
            raise ValueError("quality_score must be between 0 and 1.")


@dataclass(frozen=True)
class SurfaceComparison:
    """Differential measurements for two runs sharing one control identity."""

    baseline: SurfaceRun
    candidate: SurfaceRun

    def __post_init__(self) -> None:
        if self.baseline.identity != self.candidate.identity:
            raise ValueError(
                "Paired runs must have the same controlled identity: "
                "prompt, conversation state, runtime, model, and task."
            )
        if (
            self.baseline.condition.condition_id
            == self.candidate.condition.condition_id
        ):
            raise ValueError("Paired runs must use different condition IDs.")

    @property
    def condition_ids(self) -> tuple[str, str]:
        return (
            self.baseline.condition.condition_id,
            self.candidate.condition.condition_id,
        )

    def delta(self, field_name: str) -> int | float | None:
        """Return candidate minus baseline for a numeric run measurement."""
        baseline_value = getattr(self.baseline, field_name)
        candidate_value = getattr(self.candidate, field_name)
        if baseline_value is None or candidate_value is None:
            return None
        if not isinstance(baseline_value, (int, float)) or isinstance(
            baseline_value, bool
        ):
            raise ValueError(f"{field_name} is not a numeric measurement.")
        if not isinstance(candidate_value, (int, float)) or isinstance(
            candidate_value, bool
        ):
            raise ValueError(f"{field_name} is not a numeric measurement.")
        return candidate_value - baseline_value

    @property
    def exposed_tool_delta(self) -> dict[str, list[str]]:
        return _set_delta(
            self.baseline.condition.exposed_tools,
            self.candidate.condition.exposed_tools,
        )

    @property
    def selected_tool_delta(self) -> dict[str, list[str]]:
        return _set_delta(
            set(self.baseline.selected_tools), set(self.candidate.selected_tools)
        )


NUMERIC_MEASUREMENTS = (
    "actual_input_tokens",
    "cached_input_tokens",
    "serialized_tool_payload_chars",
    "serialized_tool_payload_tokens",
    "tool_selection_failures",
    "tool_call_count",
    "quality_score",
    "latency_seconds",
)


def compare_surface_runs(
    baseline: SurfaceRun, candidate: SurfaceRun
) -> SurfaceComparison:
    """Compare otherwise-identical runs with different exposed surfaces."""
    return SurfaceComparison(baseline, candidate)


def build_measurement_report(runs: Iterable[SurfaceRun]) -> dict[str, Any]:
    """Build a privacy-safe JSON report from exactly two paired runs."""
    run_list = list(runs)
    if len(run_list) != 2:
        raise ValueError("A controlled comparison requires exactly two runs.")
    comparison = compare_surface_runs(run_list[0], run_list[1])
    baseline = comparison.baseline
    candidate = comparison.candidate
    return {
        "experiment": _identity_record(baseline.identity),
        "runs": {
            baseline.condition.condition_id: _run_record(baseline),
            candidate.condition.condition_id: _run_record(candidate),
        },
        "comparison": {
            "baseline_condition_id": baseline.condition.condition_id,
            "candidate_condition_id": candidate.condition.condition_id,
            "deltas": {
                field_name: comparison.delta(field_name)
                for field_name in NUMERIC_MEASUREMENTS
            },
            "exposed_tool_delta": comparison.exposed_tool_delta,
            "selected_tool_delta": comparison.selected_tool_delta,
        },
    }


def write_measurement_report(
    path: str | Path, runs: Iterable[SurfaceRun]
) -> dict[str, Any]:
    """Write and return a controlled measurement report as UTF-8 JSON."""
    report = build_measurement_report(runs)
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return report


def _identity_record(identity: ExperimentIdentity) -> dict[str, Any]:
    return {
        "experiment_id": identity.experiment_id,
        "task_id": identity.task_id,
        "prompt_id": identity.prompt_id,
        "conversation_state_id": identity.conversation_state_id,
        "runtime": identity.runtime,
        "runtime_version": identity.runtime_version,
        "model": identity.model,
        "model_version": identity.model_version,
        "temperature": identity.temperature,
        "seed": identity.seed,
    }


def _run_record(run: SurfaceRun) -> dict[str, Any]:
    return {
        "condition_id": run.condition.condition_id,
        "exposed_tools": sorted(run.condition.exposed_tools),
        "deferred_tools": sorted(run.condition.deferred_tools),
        "actual_input_tokens": run.actual_input_tokens,
        "cached_input_tokens": run.cached_input_tokens,
        "serialized_tool_payload_chars": run.serialized_tool_payload_chars,
        "serialized_tool_payload_tokens": run.serialized_tool_payload_tokens,
        "schema_measurement_method": run.schema_measurement_method,
        "selected_tools": list(run.selected_tools),
        "tool_selection_failures": run.tool_selection_failures,
        "tool_call_count": run.tool_call_count,
        "task_success": run.task_success,
        "quality_score": run.quality_score,
        "latency_seconds": run.latency_seconds,
    }


def _validate_tools(values: Iterable[str], field_name: str) -> None:
    if isinstance(values, (str, bytes)) or not all(
        isinstance(value, str) and value for value in values
    ):
        raise ValueError(f"{field_name} must contain non-empty strings.")


def _nonnegative(value: int | float, field_name: str) -> None:
    if value < 0:
        raise ValueError(f"{field_name} cannot be negative.")


def _optional_nonnegative(value: int | float | None, field_name: str) -> None:
    if value is not None:
        _nonnegative(value, field_name)


def _set_delta(
    baseline: set[str] | frozenset[str], candidate: set[str] | frozenset[str]
) -> dict[str, list[str]]:
    return {
        "removed": sorted(baseline - candidate),
        "added": sorted(candidate - baseline),
    }
