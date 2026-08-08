"""Paired task execution and capture for replay observations.

The runner owns orchestration and serialization only. Callers provide an
executor that performs one task under one architecture and returns a complete
``ReplayObservation``. No synthetic measurements or live executor is supplied
by this module.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping

from .replay_harness import (
    BASELINE_ARCHITECTURE_ID,
    BenchmarkArchitecture,
    ReplayObservation,
    ReplayTask,
    build_architecture_manifest,
)

CaptureExecutor = Callable[
    [ReplayTask, BenchmarkArchitecture, tuple[str, ...]], ReplayObservation
]


def load_tasks(path: str | Path, architecture_ids: Iterable[str]) -> list[ReplayTask]:
    """Load privacy-preserving task IDs and explicit activation paths."""

    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError("Capture task input must be a JSON list.")
    known = set(architecture_ids)
    tasks: list[ReplayTask] = []
    for item in raw:
        if (
            not isinstance(item, Mapping)
            or not isinstance(item.get("task_id"), str)
            or not item["task_id"]
        ):
            raise ValueError("Each capture task must contain a non-empty task_id.")
        raw_paths = item.get("activation_paths", {})
        if not isinstance(raw_paths, Mapping) or set(raw_paths) - known:
            raise ValueError("Capture task activation paths name unknown architectures.")
        paths: dict[str, tuple[str, ...]] = {}
        for architecture_id, path in raw_paths.items():
            if not isinstance(path, list) or not all(
                isinstance(agent_id, str) and agent_id for agent_id in path
            ):
                raise ValueError("Capture activation paths must be string lists.")
            paths[str(architecture_id)] = tuple(path)
        tasks.append(ReplayTask(item["task_id"], paths))
    return tasks


def write_capture_bundle(bundle: Mapping[str, Any], path: str | Path) -> None:
    """Write a captured bundle without altering executor measurements."""

    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(bundle, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def paired_architecture_manifest(
    manifest_raw: Mapping[str, Any], candidate_id: str
) -> dict[str, Any]:
    """Return the frozen baseline and one concrete candidate for paired capture."""

    manifest = build_architecture_manifest(manifest_raw)
    if candidate_id == BASELINE_ARCHITECTURE_ID:
        raise ValueError("The capture candidate must not be the frozen baseline.")
    if candidate_id not in manifest.architecture_ids:
        raise ValueError(f"Unknown capture candidate architecture: {candidate_id!r}.")
    selected = {
        architecture.architecture_id
        for architecture in manifest.architectures
        if architecture.architecture_id in {BASELINE_ARCHITECTURE_ID, candidate_id}
    }
    return {
        "baseline_architecture_id": manifest.baseline_architecture_id,
        "historical_tool_capability_tools": sorted(
            manifest.historical_tool_capability_tools
        ),
        "search_provenance": dict(manifest_raw.get("search_provenance", {})),
        "provisional_architecture_ids": [
            architecture_id
            for architecture_id in manifest_raw.get("provisional_architecture_ids", [])
            if architecture_id in selected
        ],
        "architectures": [
            {
                "architecture_id": architecture.architecture_id,
                "parent_tools": sorted(architecture.parent_tools),
                "agents": {
                    agent_id: sorted(tools)
                    for agent_id, tools in architecture.agent_tools.items()
                },
                **(
                    {
                        "provisional": True,
                        "directional_only": True,
                        "assumptions": manifest_raw["architectures"][
                            manifest.architecture_ids.index(architecture.architecture_id)
                        ].get("assumptions", []),
                        "provenance": manifest_raw["architectures"][
                            manifest.architecture_ids.index(architecture.architecture_id)
                        ].get("provenance", {}),
                    }
                    if architecture.architecture_id in manifest_raw.get(
                        "provisional_architecture_ids", []
                    )
                    else {}
                ),
            }
            for architecture in manifest.architectures
            if architecture.architecture_id in selected
        ],
    }


def capture_paired_observations(
    tasks: Iterable[ReplayTask],
    manifest_raw: Mapping[str, Any],
    candidate_id: str,
    executor: CaptureExecutor,
) -> dict[str, Any]:
    """Execute every matched task under baseline and candidate exactly once."""

    manifest = build_architecture_manifest(manifest_raw)
    architectures = {
        architecture.architecture_id: architecture
        for architecture in manifest.architectures
    }
    if candidate_id == BASELINE_ARCHITECTURE_ID:
        raise ValueError("The capture candidate must not be the frozen baseline.")
    if candidate_id not in architectures:
        raise ValueError(f"Unknown capture candidate architecture: {candidate_id!r}.")
    task_list = list(tasks)
    if not task_list:
        raise ValueError("Capture requires at least one task.")
    if len({task.task_id for task in task_list}) != len(task_list):
        raise ValueError("Capture task IDs must be unique.")

    observations: dict[str, list[dict[str, Any]]] = {}
    for architecture_id in (BASELINE_ARCHITECTURE_ID, candidate_id):
        architecture = architectures[architecture_id]
        rows: list[dict[str, Any]] = []
        for task in task_list:
            path = architecture.requested_activation_path(task)
            observation = executor(task, architecture, path)
            if observation.task_id != task.task_id:
                raise ValueError(
                    f"Capture executor returned {observation.task_id!r} for {task.task_id!r}."
                )
            row = asdict(observation)
            row["agent_activation_path"] = list(observation.agent_activation_path)
            rows.append(row)
        observations[architecture_id] = rows

    return {
        "metadata": {
            "mode": "captured_observations",
            "executor": "caller_supplied",
            "deterministic": False,
            "side_effect_free": False,
            "capture_scope": "paired_baseline_and_candidate",
            "candidate_id": candidate_id,
            "synthetic": False,
        },
        "manifest": paired_architecture_manifest(manifest_raw, candidate_id),
        "tasks": [
            {
                "task_id": task.task_id,
                "activation_paths": {
                    architecture_id: list(
                        architectures[architecture_id].requested_activation_path(task)
                    )
                    for architecture_id in (BASELINE_ARCHITECTURE_ID, candidate_id)
                },
            }
            for task in task_list
        ],
        "observations": observations,
    }