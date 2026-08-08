from optimize_agent_tools.nmf_screening import NMFConfig, run_nmf_screening
from optimize_agent_tools.telemetry_ingestion import (
    Session,
    classify_tool_role,
    classify_tool_roles,
)


def _sessions() -> list[Session]:
    return [
        Session("a1", "test", ["alpha", "shared", "send_message"]),
        Session("a2", "test", ["alpha", "shared"]),
        Session("b1", "test", ["beta", "shared", "wait_agent"]),
        Session("b2", "test", ["beta", "shared"]),
    ]


def test_roles_are_explicit_and_unknown_tools_default_to_domain() -> None:
    assert classify_tool_role("spawn_agent").role == "delegation"
    assert classify_tool_role("send_message").role == "coordination"
    assert classify_tool_role("exec").role == "runtime_infrastructure"
    unknown = classify_tool_role("vendor_specific_operation")
    assert unknown.role == "domain"
    assert unknown.evidence == "conservative_unknown_default"


def test_control_plane_is_excluded_but_statistics_are_retained() -> None:
    sessions = _sessions()
    roles = classify_tool_roles(
        {tool for session in sessions for tool in session.tool_set}
    )
    result = run_nmf_screening(
        sessions,
        ["alpha", "beta", "shared"],
        roles,
        config=NMFConfig(max_factors=2, seeds=(3, 7), iterations=80),
    )

    assert result.matrix["tools"] == ["alpha", "beta", "shared"]
    assert result.control_plane["tool_count"] == 2
    assert result.control_plane["coordination_calls"] == 2
    assert result.control_plane["tools"][0]["tool"] == "send_message"


def test_runtime_infrastructure_is_counted_separately_from_control_plane() -> None:
    sessions = _sessions()
    roles = classify_tool_roles(
        {tool for session in sessions for tool in session.tool_set} | {"exec"}
    )

    result = run_nmf_screening(sessions, ["alpha", "beta", "shared"], roles)

    assert result.control_plane["tool_count"] == 3
    assert result.control_plane["control_plane_tool_count"] == 2
    assert result.control_plane["runtime_infrastructure_tool_count"] == 1


def test_fixed_seeds_make_screening_reproducible() -> None:
    roles = classify_tool_roles(
        {tool for session in _sessions() for tool in session.tool_set}
    )
    config = NMFConfig(max_factors=3, seeds=(11, 13), iterations=80)
    first = run_nmf_screening(_sessions(), ["alpha", "beta", "shared"], roles, config=config)
    second = run_nmf_screening(_sessions(), ["alpha", "beta", "shared"], roles, config=config)

    assert first.as_dict() == second.as_dict()


def test_factor_count_is_a_search_hint_not_an_agent_count() -> None:
    roles = classify_tool_roles(
        {tool for session in _sessions() for tool in session.tool_set}
    )
    result = run_nmf_screening(
        _sessions(),
        ["alpha", "beta", "shared"],
        roles,
        config=NMFConfig(max_factors=3, seeds=(0,), iterations=60),
    )

    assert result.search_hints["factor_count_is_not_agent_count"] is True
    assert "agent_count" not in result.search_hints
    assert all("agent" not in evaluation for evaluation in result.evaluations)
