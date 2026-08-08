#!/usr/bin/env python3
"""Compare two externally captured, otherwise-identical tool-surface runs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from optimize_agent_tools.measurement import (
    ExperimentIdentity,
    SurfaceCondition,
    SurfaceRun,
    write_measurement_report,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare controlled measurements for two exposed tool surfaces."
    )
    parser.add_argument("--input", required=True, help="JSON file containing two runs.")
    parser.add_argument("--output", required=True, help="JSON report output path.")
    return parser.parse_args()


def _identity(raw: dict[str, Any]) -> ExperimentIdentity:
    return ExperimentIdentity(
        experiment_id=raw["experiment_id"],
        task_id=raw["task_id"],
        prompt_id=raw["prompt_id"],
        conversation_state_id=raw["conversation_state_id"],
        runtime=raw["runtime"],
        runtime_version=raw["runtime_version"],
        model=raw["model"],
        model_version=raw["model_version"],
        temperature=raw.get("temperature", 0.0),
        seed=raw.get("seed"),
    )


def _run(raw: dict[str, Any], identity: ExperimentIdentity) -> SurfaceRun:
    condition = SurfaceCondition(
        condition_id=raw["condition_id"],
        exposed_tools=frozenset(raw.get("exposed_tools", [])),
        deferred_tools=frozenset(raw.get("deferred_tools", [])),
    )
    return SurfaceRun(
        identity=identity,
        condition=condition,
        actual_input_tokens=raw["actual_input_tokens"],
        cached_input_tokens=raw.get("cached_input_tokens"),
        serialized_tool_payload_chars=raw.get("serialized_tool_payload_chars"),
        serialized_tool_payload_tokens=raw.get("serialized_tool_payload_tokens"),
        schema_measurement_method=raw["schema_measurement_method"],
        selected_tools=tuple(raw.get("selected_tools", [])),
        tool_selection_failures=raw["tool_selection_failures"],
        tool_call_count=raw["tool_call_count"],
        task_success=raw["task_success"],
        quality_score=raw["quality_score"],
        latency_seconds=raw["latency_seconds"],
    )


def load_runs(path: str | Path) -> list[SurfaceRun]:
    """Load two runs from a privacy-safe measurement input bundle."""
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("experiment"), dict):
        raise ValueError("Measurement input must contain an experiment object.")
    raw_runs = payload.get("runs")
    if not isinstance(raw_runs, list) or len(raw_runs) != 2:
        raise ValueError("Measurement input must contain exactly two runs.")
    identity = _identity(payload["experiment"])
    return [_run(raw_run, identity) for raw_run in raw_runs]


def main() -> int:
    args = parse_args()
    write_measurement_report(args.output, load_runs(args.input))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
