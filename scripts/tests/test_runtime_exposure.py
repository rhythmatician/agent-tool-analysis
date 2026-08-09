from optimize_agent_tools.runtime_exposure import (
    ExposureFact,
    RuntimeExposureCapabilities,
)
from optimize_agent_tools.runtime_alternatives import build_alternative_plans


def test_unknown_runtime_support_does_not_claim_dynamic_retrieval() -> None:
    runtime = RuntimeExposureCapabilities(host="copilot")

    assert runtime.dynamic_retrieval_supported is None
    dynamic = next(
        plan
        for plan in build_alternative_plans(
            manifest={"architectures": []},
            runtime_exposure=runtime,
        )
        if plan.alternative_id == "runtime_dynamic_retrieval"
    )
    assert dynamic.supported is None


def test_known_runtime_support_enables_dynamic_alternative() -> None:
    runtime = RuntimeExposureCapabilities(
        host="copilot",
        tool_search_supported=ExposureFact(True, "known", "host_adapter"),
    )

    dynamic = next(
        plan
        for plan in build_alternative_plans(
            manifest={"architectures": []},
            runtime_exposure=runtime,
        )
        if plan.alternative_id == "runtime_dynamic_retrieval"
    )
    assert dynamic.supported is True
    assert dynamic.architecture_id == "runtime_dynamic_retrieval"


def test_runtime_record_preserves_unknown_fact_provenance() -> None:
    runtime = RuntimeExposureCapabilities(
        host="codex",
        observability={
            "loaded_definitions": ExposureFact(True, "known", "adapter")
        },
    )

    record = runtime.to_record()

    assert record["host"] == "codex"
    assert record["tool_search_supported"]["status"] == "unknown"
    assert record["tool_search_supported"]["value"] is None
    assert record["observability"]["loaded_definitions"]["value"] is True
