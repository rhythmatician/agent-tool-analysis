"""Safe execution of explicitly requested recorded offline replay bundles."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .replay_harness import (
    BASELINE_ARCHITECTURE_ID,
    build_architecture_manifest,
    serialize_architecture_manifest,
)


@dataclass(frozen=True)
class ReplayReadiness:
    """Whether a supplied bundle is safe and complete for offline replay."""

    ready: bool
    candidate_id: str | None
    reasons: tuple[str, ...] = ()


def assess_recorded_replay(
    report: Mapping[str, Any], bundle: Mapping[str, Any]
) -> ReplayReadiness:
    """Check readiness without invoking an executor or external process.

    Advanced replay accepts only a self-declared recorded-observation bundle.
    The declaration is deliberately explicit so a live model, shell, network,
    or API executor can never be launched by the normal optimizer path.
    """

    reasons: list[str] = []
    try:
        report_manifest = build_architecture_manifest(report["architecture_manifest"])
        report_manifest_wire = serialize_architecture_manifest(report_manifest)
    except (AttributeError, KeyError, TypeError, ValueError) as error:
        return ReplayReadiness(
            False, None, (f"analysis architecture manifest is invalid: {error}",)
        )
    metadata = bundle.get("metadata")
    if not isinstance(metadata, Mapping):
        reasons.append("replay bundle metadata is missing")
    else:
        if metadata.get("mode") != "recorded_observations":
            reasons.append("replay mode is not recorded_observations")
        if metadata.get("deterministic") is not True:
            reasons.append("replay bundle is not explicitly deterministic")
        if metadata.get("side_effect_free") is not True:
            reasons.append("replay bundle is not explicitly side-effect-free")
        if metadata.get("executor") != "recorded_observations":
            reasons.append("replay executor is not explicitly recorded_observations")
        bundle_manifest = metadata.get("architecture_manifest")
        try:
            bundle_manifest_wire = serialize_architecture_manifest(
                build_architecture_manifest(bundle_manifest)
            )
        except (AttributeError, TypeError, ValueError) as error:
            reasons.append(f"replay bundle architecture manifest is invalid: {error}")
        else:
            if bundle_manifest_wire != report_manifest_wire:
                reasons.append(
                    "replay bundle architecture manifest does not exactly match analysis"
                )

    recommendation = report.get("specialist_recommendation") or {}
    candidate_id = recommendation.get("best_guess_candidate_id")
    if not isinstance(candidate_id, str) or not candidate_id:
        reasons.append("no named candidate architecture is available for replay")
        candidate_id = None

    architecture_ids = report_manifest.architecture_ids
    if candidate_id is not None and candidate_id not in architecture_ids:
        reasons.append(
            f"candidate architecture {candidate_id!r} is absent from the manifest"
        )
    if candidate_id == BASELINE_ARCHITECTURE_ID:
        reasons.append("the frozen baseline cannot be replayed as the candidate")
    pareto_ids = set(recommendation.get("pareto_candidate_ids", ()))
    provisional_ids = set(recommendation.get("provisional_architecture_ids", ()))
    if (
        candidate_id is not None
        and candidate_id not in pareto_ids
        and candidate_id not in provisional_ids
    ):
        reasons.append(
            "candidate architecture is neither an empirical Pareto finalist nor a provisional finalist"
        )

    manifest_architecture = next(
        (
            architecture
            for architecture in report_manifest_wire.get("architectures", [])
            if isinstance(architecture, Mapping)
            and architecture.get("architecture_id") == candidate_id
        ),
        None,
    )
    if candidate_id is not None and manifest_architecture is not None:
        if manifest_architecture.get("provisional") is True:
            if manifest_architecture.get("directional_only") is not True:
                reasons.append("provisional replay candidate is not directional_only")
        elif candidate_id not in pareto_ids:
            reasons.append("replay candidate lacks provisional or empirical provenance")

    tasks = bundle.get("tasks")
    observations = bundle.get("observations")
    if not isinstance(tasks, list) or not tasks:
        reasons.append("replay tasks are missing")
    if not isinstance(observations, Mapping):
        reasons.append("recorded observations are missing")
    else:
        supplied_ids = set(observations)
        expected_ids = set(architecture_ids)
        if supplied_ids != expected_ids:
            missing = sorted(expected_ids - supplied_ids)
            extra = sorted(supplied_ids - expected_ids)
            if missing:
                reasons.append("observations are missing for: " + ", ".join(missing))
            if extra:
                reasons.append(
                    "observations name unknown architectures: " + ", ".join(extra)
                )

        if isinstance(tasks, list):
            task_ids = [
                task.get("task_id") for task in tasks if isinstance(task, Mapping)
            ]
            required_measurements = {
                "task_success",
                "observed_replay_capability_covered",
                "quality_score",
                "agent_activation_path",
                "tool_call_failures",
                "routing_failure",
                "missed_agent_activation",
                "unnecessary_agent_activation",
                "total_input_tokens",
                "tool_definition_context_tokens",
                "delegation_tokens",
                "inter_agent_communication_tokens",
                "turns",
                "wall_clock_seconds",
            }
            for architecture_id in expected_ids:
                rows = observations.get(architecture_id)
                if not isinstance(rows, list):
                    reasons.append(
                        f"observations for {architecture_id!r} must be a list"
                    )
                    continue
                if len(rows) != len(tasks):
                    reasons.append(
                        f"observations for {architecture_id!r} must contain one row per task"
                    )
                    continue
                for index, row in enumerate(rows):
                    if not isinstance(row, Mapping):
                        reasons.append(
                            f"observation {architecture_id!r}[{index}] must be an object"
                        )
                        continue
                    if row.get("task_id") != task_ids[index]:
                        reasons.append(
                            f"observation {architecture_id!r}[{index}] task_id does not match tasks"
                        )
                    missing = required_measurements - set(row)
                    if missing:
                        reasons.append(
                            f"observation {architecture_id!r}[{index}] is missing: "
                            + ", ".join(sorted(missing))
                        )

    if isinstance(tasks, list):
        task_ids = [task.get("task_id") for task in tasks if isinstance(task, Mapping)]
        if len(task_ids) != len(tasks) or any(
            not isinstance(task_id, str) or not task_id for task_id in task_ids
        ):
            reasons.append("replay tasks must have non-empty task_id values")
        if len(task_ids) != len(set(task_ids)):
            reasons.append("replay task IDs must be unique")

    return ReplayReadiness(not reasons, candidate_id, tuple(reasons))


def run_recorded_replay(
    report: Mapping[str, Any], bundle: Mapping[str, Any]
) -> dict[str, Any]:
    """Evaluate recorded observations through the existing frozen-baseline gate."""

    from replay_architectures import build_report

    benchmark = {
        "pruned_flat_baseline": report["pruned_flat_baseline"],
    }
    manifest = build_architecture_manifest(report["architecture_manifest"])
    return build_report(
        dict(bundle),
        benchmark,
        serialize_architecture_manifest(manifest),
    )
