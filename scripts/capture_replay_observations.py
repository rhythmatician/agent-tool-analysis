#!/usr/bin/env python3
"""Capture paired replay observations through an explicitly supplied adapter.

This CLI is intentionally an orchestration shell, not a task executor. The
adapter must be a local Python module exposing ``execute(task, architecture,
activation_path)`` and returning a complete ReplayObservation. It may perform
real work, so captured bundles are never auto-consumed by the normal optimizer.
The adapter is responsible for matched task inputs, quality scoring, token
accounting, routing diagnostics, and latency measurement; this wrapper only
checks task IDs and preserves the returned fields.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

from optimize_agent_tools.capture_runner import (
    capture_paired_observations,
    load_tasks,
    paired_architecture_manifest,
    write_capture_bundle,
)
from optimize_agent_tools.replay_harness import build_architecture_manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Capture paired baseline/candidate replay observations through a local adapter."
    )
    parser.add_argument("--architecture-manifest", required=True)
    parser.add_argument("--candidate-id", required=True)
    parser.add_argument("--tasks", required=True, help="JSON list of task IDs and activation paths.")
    parser.add_argument("--adapter", required=True, help="Python file exposing execute(task, architecture, path).")
    parser.add_argument("--output", required=True)
    parser.add_argument(
        "--manifest-output",
        default=None,
        help="Optional paired manifest path; defaults to <output>.manifest.json.",
    )
    return parser.parse_args()


def _load_adapter(path: str) -> Any:
    module_path = Path(path).resolve()
    spec = importlib.util.spec_from_file_location("agent_tool_capture_adapter", module_path)
    if spec is None or spec.loader is None:
        raise ValueError(f"Cannot load capture adapter: {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    execute = getattr(module, "execute", None)
    if not callable(execute):
        raise ValueError("Capture adapter must expose callable execute(task, architecture, path).")
    return execute


def main() -> int:
    args = parse_args()
    manifest = json.loads(Path(args.architecture_manifest).read_text(encoding="utf-8"))
    parsed_manifest = build_architecture_manifest(manifest)
    tasks = load_tasks(args.tasks, parsed_manifest.architecture_ids)
    executor = _load_adapter(args.adapter)
    bundle = capture_paired_observations(tasks, manifest, args.candidate_id, executor)
    write_capture_bundle(bundle, args.output)
    manifest_output = (
        Path(args.manifest_output)
        if args.manifest_output
        else Path(f"{args.output}.manifest.json")
    )
    manifest_output.parent.mkdir(parents=True, exist_ok=True)
    manifest_output.write_text(
        json.dumps(
            paired_architecture_manifest(manifest, args.candidate_id),
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(
        f"Captured {len(tasks)} matched task(s) for {args.candidate_id!r} -> "
        f"{args.output}; paired manifest -> {manifest_output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
