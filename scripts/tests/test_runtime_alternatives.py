from optimize_agent_tools.measurement import (
    ExperimentIdentity,
    SurfaceCondition,
    SurfaceRun,
)
from optimize_agent_tools.runtime_alternatives import (
    ALTERNATIVE_IDS,
    build_alternative_plans,
    build_runtime_alternatives_report,
    evaluate_alternatives,
)
from optimize_agent_tools.runtime_metrics import (
    from_surface_run,
)


def runtime_metrics() -> object:
    return from_surface_run(
        SurfaceRun(
            identity=ExperimentIdentity(
                experiment_id="exp",
                task_id="task",
                prompt_id="prompt",
                conversation_state_id="state",
                runtime="host",
                runtime_version="1",
                model="model",
                model_version="1",
            ),
            condition=SurfaceCondition(
                "dynamic", frozenset({"exec"}), frozenset({"file"})
            ),
            actual_input_tokens=100,
            cached_input_tokens=20,
            serialized_tool_payload_chars=320,
            serialized_tool_payload_tokens=80,
            schema_measurement_method="provider_usage",
            selected_tools=("exec",),
            tool_selection_failures=0,
            tool_call_count=1,
            task_success=True,
            quality_score=0.9,
            latency_seconds=1.5,
        )
    )


def test_build_alternative_plans_always_includes_current_configuration() -> None:
    plans = build_alternative_plans(
        manifest={
            "baseline_architecture_id": "pruned_flat_baseline",
            "architectures": [
                {"architecture_id": "pruned_flat_baseline", "topology": "flat"},
                {"architecture_id": "peer_candidate", "topology": "peer"},
                {
                    "architecture_id": "coordinator_candidate",
                    "topology": "coordinator_specialists",
                },
            ],
        },
        dynamic_retrieval_supported=None,
    )

    assert tuple(plan.alternative_id for plan in plans) == ALTERNATIVE_IDS
    current = plans[0]
    assert current.supported is True
    assert current.loading_policy == "current"
    assert plans[4].supported is True
    assert plans[5].topology == "coordinator_children"
    assert plans[5].supported is True
    assert plans[2].supported is False


def test_evaluation_keeps_metric_evidence_and_does_not_choose_winner() -> None:
    plans = build_alternative_plans(
        manifest={
            "baseline_architecture_id": "pruned_flat_baseline",
            "architectures": [
                {"architecture_id": "pruned_flat_baseline", "topology": "flat"}
            ],
        }
    )
    metrics = runtime_metrics()
    evaluations = evaluate_alternatives(
        plans,
        {
            "do_nothing": metrics,
            "prune_only": metrics,
        },
    )

    current = evaluations[0]
    prune = evaluations[1]
    assert current.metric_evidence_status["loading"] == "measured"
    assert current.metric_evidence_status["occupancy"] == "partial"
    assert (
        prune.comparison["tokens.total_input"]["baseline_alternative"] == "do_nothing"
    )
    assert not any("winner" in key for key in prune.to_record())


def test_report_marks_unsupported_and_unmeasured_alternatives_explicitly() -> None:
    report = build_runtime_alternatives_report(
        manifest={
            "baseline_architecture_id": "pruned_flat_baseline",
            "architectures": [
                {"architecture_id": "pruned_flat_baseline", "topology": "flat"}
            ],
        }
    )

    assert len(report) == len(ALTERNATIVE_IDS)
    dynamic = next(
        row for row in report if row["alternative_id"] == "runtime_dynamic_retrieval"
    )
    assert dynamic["supported"] is None
    assert dynamic["metric_evidence_status"]["tokens"] == "unavailable"
    assert report[0]["alternative_id"] == "do_nothing"


def test_concrete_architecture_reports_missing_historical_capabilities() -> None:
    plans = build_alternative_plans(
        manifest={
            "baseline_architecture_id": "pruned_flat_baseline",
            "historical_tool_capability_tools": ["exec", "github.fetch_issue"],
            "architectures": [
                {
                    "architecture_id": "pruned_flat_baseline",
                    "topology": "flat",
                    "parent_tools": ["exec", "github.fetch_issue"],
                },
                {
                    "architecture_id": "peer_candidate",
                    "topology": "peer",
                    "agents": {"one": {"tools": ["exec"]}},
                },
            ],
        }
    )

    peer = next(plan for plan in plans if plan.alternative_id == "peer_specialists")
    assert peer.capability_coverage is False
    assert "github.fetch_issue" in peer.coverage_reason
