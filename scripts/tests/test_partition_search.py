from __future__ import annotations

from types import SimpleNamespace

import pytest
from optimize_agent_tools.analysis_pipeline import (
    AnalysisStageError,
    AnalysisWorkflowResult,
    _run_analysis,
    analyze,
    build_architecture_options,
    classify_specialist_recommendation,
)
from optimize_agent_tools.partition_search import search_partitions
from optimize_agent_tools.replay_harness import (
    build_architecture_manifest,
    materialize_provisional_architecture,
)
from optimize_agent_tools.reporting import render_markdown
from optimize_agent_tools.telemetry_ingestion import Session
from optimize_agent_tools.tool_definition_registry import DefinitionRecord


def _stats() -> dict[str, SimpleNamespace]:
    return {
        name: SimpleNamespace(definition_tokens=cost)
        for name, cost in {
            "a": 10,
            "b": 20,
            "c": 30,
            "dep_a": 5,
            "shared": 7,
        }.items()
    }


def _definition(name: str, tokens: int) -> DefinitionRecord:
    return DefinitionRecord(
        name,
        "codex",
        "test",
        name,
        None,
        None,
        tokens * 4,
        tokens,
        "test",
        "explicit",
        "recovered_definition",
    )


def test_normal_analysis_workflow_includes_generic_specialist_recommendation() -> None:
    sessions = [
        Session("one", "codex", ["a", "b"], {"a", "b"}),
        Session("two", "codex", ["a"], {"a", "b"}),
    ]
    definitions = {
        name: _definition(name, tokens) for name, tokens in {"a": 10, "b": 20}.items()
    }

    report = analyze(
        sessions,
        definitions,
        {},
        explicit_path=None,
        definition_roots=[],
        min_tool_sessions=1,
        similarity_threshold=0.35,
        global_usage_threshold=1.0,
        min_cluster_size=2,
        min_cluster_sessions=1,
        delegation_overhead_tokens=0,
        max_agents=2,
        nucleus_threshold=None,
    )

    recommendation = report["specialist_recommendation"]
    assert recommendation["action"] == "choose_architecture_option"
    assert recommendation["status"] == "none"
    assert recommendation["direction"] is None
    assert recommendation["pareto_candidate_ids"]
    assert recommendation["decision_mode"] == "user_choice"
    assert recommendation["architecture_option_ids"] == [
        "pruned_flat_baseline",
        recommendation["pareto_candidate_ids"][0],
    ]
    assert report["architecture_options"][0]["label"] == "Pruned single agent"
    assert report["architecture_options"][1]["status"] == "empirical_pareto"
    assert report["runtime_recommendation"]["preferred_option"] == "do_nothing"
    assert report["runtime_recommendation"]["recommendation_strength"] == "provisional"
    assert report["architecture_manifest"]["baseline_architecture_id"] == (
        "pruned_flat_baseline"
    )
    assert report["partition_search"]["search"]["max_agents"] == 2
    assert {
        candidate["topology"]
        for candidate in report["topology_discovery"]["candidates"]
    } == {"flat", "peer", "coordinator_children"}


def test_analysis_result_serializes_the_stable_report_shape() -> None:
    sessions = [
        Session("one", "codex", ["a"], {"a"}),
    ]
    definitions = {"a": _definition("a", 10)}

    result = _run_analysis(
        sessions,
        definitions,
        {},
        explicit_path=None,
        definition_roots=[],
        min_tool_sessions=1,
        similarity_threshold=0.35,
        global_usage_threshold=1.0,
        min_cluster_size=2,
        min_cluster_sessions=1,
        delegation_overhead_tokens=0,
        max_agents=1,
    )

    report = result.serialize()
    assert isinstance(result, AnalysisWorkflowResult)
    assert report == result.report
    assert report is not result.report


def test_normal_analysis_excludes_runtime_controls_from_decomposition() -> None:
    sessions = [
        Session("one", "codex", ["domain.alpha", "exec", "send_message"]),
        Session("two", "codex", ["domain.beta", "exec", "wait_agent"]),
    ]
    definitions = {
        name: _definition(name, 10)
        for name in (
            "domain.alpha",
            "domain.beta",
            "exec",
            "send_message",
            "wait_agent",
        )
    }

    report = analyze(
        sessions,
        definitions,
        {},
        explicit_path=None,
        definition_roots=[],
        min_tool_sessions=1,
        similarity_threshold=0.35,
        global_usage_threshold=1.0,
        min_cluster_size=1,
        min_cluster_sessions=1,
        delegation_overhead_tokens=0,
        max_agents=2,
    )

    retained = set(report["pruned_flat_baseline"]["tools_retained"])
    assert {"exec", "send_message", "wait_agent"} <= retained
    assert report["partition_search"]["search"]["control_tools"] == [
        "send_message",
        "wait",
        "wait_agent",
    ]
    assert all(
        control_tool not in unit
        for unit in report["partition_search"]["search"]["partition_units"]
        for control_tool in ("send_message", "wait", "wait_agent")
    )
    assert {
        item["tool"] for item in report["nmf_screening"]["control_plane"]["tools"]
    } == {"exec", "send_message", "wait_agent"}


def test_analysis_failure_names_the_failing_stage(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail(*args: object, **kwargs: object) -> dict[str, object]:
        raise RuntimeError("fixture failure")

    monkeypatch.setattr("optimize_agent_tools.analysis_pipeline.build_stats", fail)

    with pytest.raises(
        AnalysisStageError, match="statistics stage failed: fixture failure"
    ):
        analyze(
            [Session("one", "codex", ["a"], {"a"})],
            {"a": _definition("a", 10)},
            {},
            explicit_path=None,
            definition_roots=[],
            min_tool_sessions=1,
            similarity_threshold=0.35,
            global_usage_threshold=1.0,
            min_cluster_size=2,
            min_cluster_sessions=1,
            delegation_overhead_tokens=0,
            max_agents=1,
        )


def test_incomplete_observed_only_frontier_uses_precise_recommendation_language() -> (
    None
):
    sessions = [
        Session("one", "codex", ["a"]),
        Session("two", "codex", ["b"]),
    ]
    definitions = {name: _definition(name, 10) for name in ("a", "b")}

    report = analyze(
        sessions,
        definitions,
        {},
        explicit_path=None,
        definition_roots=[],
        min_tool_sessions=1,
        similarity_threshold=0.35,
        global_usage_threshold=1.0,
        min_cluster_size=2,
        min_cluster_sessions=1,
        delegation_overhead_tokens=0,
        max_agents=2,
    )

    recommendation = report["specialist_recommendation"]
    assert recommendation["pareto_candidate_ids"] == []
    assert recommendation["status"] == "none"
    assert "cost-complete empirical Pareto candidates" in recommendation["headline"]
    assert recommendation["exposure_model"] == "observed_only"

    markdown = render_markdown(report)
    assert "Partition search: complete" in markdown
    assert (
        "Replay: not run; no cost-complete empirical finalist architectures" in markdown
    )
    assert "bounded fallback was used" not in markdown


def test_directional_structure_gets_provisional_best_guess() -> None:
    recommendation = classify_specialist_recommendation(
        pareto_candidates=[],
        candidate_agents=[
            {
                "candidate_id": "cluster_01",
                "tools": ["github.read", "github.write"],
                "internal_affinity": 0.8,
            },
            {
                "candidate_id": "cluster_02",
                "tools": ["edit", "exec"],
                "internal_affinity": 0.7,
            },
        ],
        directional_variants=[
            {
                "variant_id": "cluster_01",
                "sensitivity": {"min_mid_reduction": 0.2, "max_mid_reduction": 0.5},
            },
            {
                "variant_id": "cluster_02",
                "sensitivity": {"min_mid_reduction": 0.1, "max_mid_reduction": 0.3},
            },
        ],
        exposure_evidence_sufficient=False,
        cost_complete=False,
        search_complete=True,
    )

    assert recommendation["status"] == "provisional"
    assert recommendation["direction"] == "2-agent architecture"
    assert recommendation["confidence"] == "moderate-low"
    assert recommendation["best_guess_architecture"] == "two_agents"
    assert "quality" in recommendation["required_validation"]


def test_zero_to_positive_counterfactual_range_is_not_supported() -> None:
    recommendation = classify_specialist_recommendation(
        pareto_candidates=[],
        candidate_agents=[
            {
                "candidate_id": "cluster_01",
                "tools": ["github.read", "github.write"],
                "internal_affinity": 0.8,
            },
            {
                "candidate_id": "cluster_02",
                "tools": ["exec", "send_message"],
                "internal_affinity": 0.7,
            },
        ],
        directional_variants=[
            {
                "variant_id": "cluster_01",
                "sensitivity": {"min_mid_reduction": 0.0, "max_mid_reduction": 0.31},
            },
            {
                "variant_id": "cluster_02",
                "sensitivity": {"min_mid_reduction": 0.0, "max_mid_reduction": 0.06},
            },
        ],
        exposure_evidence_sufficient=False,
        cost_complete=False,
        search_complete=False,
    )

    assert recommendation["status"] == "none"
    assert recommendation["direction"] is None


def test_contradictory_directional_evidence_gets_no_recommendation() -> None:
    recommendation = classify_specialist_recommendation(
        pareto_candidates=[],
        candidate_agents=[
            {
                "candidate_id": "cluster_01",
                "tools": ["a", "b"],
                "internal_affinity": 0.4,
            },
            {
                "candidate_id": "cluster_02",
                "tools": ["c", "d"],
                "internal_affinity": 0.4,
            },
        ],
        directional_variants=[
            {
                "variant_id": "cluster_01",
                "sensitivity": {"min_mid_reduction": -0.2, "max_mid_reduction": 0.2},
            },
            {
                "variant_id": "cluster_02",
                "sensitivity": {"min_mid_reduction": -0.1, "max_mid_reduction": 0.1},
            },
        ],
        exposure_evidence_sufficient=False,
        cost_complete=False,
        search_complete=True,
    )

    assert recommendation["status"] == "none"
    assert recommendation["direction"] is None


def test_complete_evidence_without_quality_gate_is_still_provisional() -> None:
    recommendation = classify_specialist_recommendation(
        pareto_candidates=[
            {
                "architecture_id": "partition_k02_0001",
                "agent_count": 2,
                "expected_context_cost_after_communication": 40.0,
            }
        ],
        candidate_agents=[],
        directional_variants=[],
        exposure_evidence_sufficient=True,
        cost_complete=True,
        search_complete=True,
    )

    assert recommendation["status"] == "provisional"
    assert recommendation["direction"] == "2-agent architecture"
    assert recommendation["confidence"] == "moderate"


def test_directional_hypothesis_without_partition_candidate_does_not_materialize() -> (
    None
):
    recommendation = {
        "status": "provisional",
        "direction": "2-agent architecture",
    }
    manifest_entry = materialize_provisional_architecture(
        recommendation=recommendation,
        search_provenance={"search_complete": False},
        dependencies={"a": {"dep_a"}},
    )

    assert manifest_entry is None


def test_incoherent_partition_candidate_does_not_materialize() -> None:
    recommendation = {
        "status": "provisional",
        "direction": "2-agent architecture",
    }
    candidate = {
        "architecture_id": "partition_k02_0001",
        "agent_count": 2,
        "agent_tools": [
            ["github.fetch_issue", "github.fetch_pr"],
            ["github.update_pull_request"],
        ],
        "exclusive_tools": [
            ["github.fetch_issue", "github.fetch_pr"],
            ["github.update_pull_request"],
        ],
        "shared_tools": [],
        "control_tools": [],
        "is_cost_complete": False,
        "is_pareto_optimal": False,
        "pareto_scope": "evaluated_subset",
    }

    assert (
        materialize_provisional_architecture(
            recommendation=recommendation,
            search_provenance={
                "search_complete": False,
                "search_strategy": "bounded",
                "pareto_scope": "evaluated_subset",
            },
            search_candidates=[candidate],
        )
        is None
    )


def test_incomplete_provisional_analysis_exposes_only_the_flat_baseline() -> None:
    sessions = [
        Session(
            "one",
            "codex",
            ["github.read", "github.write"],
            {"github.read", "github.write", "edit", "exec"},
        ),
        Session(
            "two",
            "codex",
            ["edit", "exec"],
            {"github.read", "github.write", "edit", "exec"},
        ),
        Session(
            "three",
            "codex",
            ["github.read"],
            {"github.read", "github.write", "edit", "exec"},
        ),
        Session(
            "four",
            "codex",
            ["edit"],
            {"github.read", "github.write", "edit", "exec"},
        ),
    ]
    definitions = {
        name: _definition(name, 10)
        for name in ("github.read", "github.write", "edit", "exec")
    }

    report = analyze(
        sessions,
        definitions,
        {},
        explicit_path=None,
        definition_roots=[],
        min_tool_sessions=1,
        similarity_threshold=0.35,
        global_usage_threshold=1.0,
        min_cluster_size=2,
        min_cluster_sessions=1,
        delegation_overhead_tokens=0,
        max_agents=2,
    )

    options = report["architecture_options"]
    assert [option["architecture_id"] for option in options] == ["pruned_flat_baseline"]
    assert report["specialist_recommendation"]["status"] == "none"
    markdown = render_markdown(report)
    assert "Option 1 — Pruned single agent" in markdown
    assert "Option 2 — Two cooperating agents" not in markdown


def test_architecture_options_keep_empirical_finalists_visible() -> None:
    options = build_architecture_options(
        baseline={"tools_retained": ["shared", "a", "b"]},
        manifest={
            "architectures": [
                {
                    "architecture_id": "pruned_flat_baseline",
                    "parent_tools": ["shared", "a", "b"],
                    "agents": {},
                },
                {
                    "architecture_id": "partition_k02_0001",
                    "parent_tools": ["shared"],
                    "agents": {"agent_01": ["a"], "agent_02": ["b"]},
                },
                {
                    "architecture_id": "provisional_two_specialists",
                    "parent_tools": ["shared"],
                    "agents": {"agent_01": ["a"], "agent_02": ["b"]},
                    "provisional": True,
                    "directional_only": True,
                },
            ]
        },
        recommendation={
            "pareto_candidate_ids": ["partition_k02_0001"],
            "provisional_architecture_ids": ["provisional_two_specialists"],
            "confidence": "moderate-low",
        },
    )

    assert [option["architecture_id"] for option in options] == [
        "pruned_flat_baseline",
        "partition_k02_0001",
        "provisional_two_specialists",
    ]


def test_incomplete_evidence_does_not_label_a_cost_candidate_complete() -> None:
    recommendation = classify_specialist_recommendation(
        pareto_candidates=[
            {
                "architecture_id": "partition_k02_0001",
                "agent_count": 2,
                "expected_context_cost_after_communication": 40.0,
            }
        ],
        candidate_agents=[
            {"candidate_id": "cluster_01", "tools": ["a", "b"]},
            {"candidate_id": "cluster_02", "tools": ["c", "d"]},
        ],
        directional_variants=[],
        exposure_evidence_sufficient=False,
        cost_complete=False,
        search_complete=False,
    )

    assert recommendation["status"] == "none"
    assert recommendation["evidence_status"] == "inconclusive"


def test_search_generates_closed_manifest_candidates_and_metrics() -> None:
    sessions = [
        Session("one", "codex", ["a", "b"], {"a", "b"}),
        Session("two", "codex", ["c"], {"c"}),
        Session("three", "codex", ["a", "c"], {"a", "c"}),
    ]

    result = search_partitions(
        sessions=sessions,
        stats=_stats(),
        required_tools={"a", "b", "c"},
        global_tools={"shared"},
        dependencies={"a": {"dep_a"}},
        max_agents=2,
        communication_tokens_per_handoff=4,
        delegation_tokens_per_activation=2,
    )

    assert {candidate.agent_count for candidate in result.all_candidates} == {1, 2}
    assert result.manifest["baseline_architecture_id"] == "pruned_flat_baseline"
    assert result.manifest["historical_tool_capability_tools"] == [
        "a",
        "b",
        "c",
        "dep_a",
    ]
    assert all(
        architecture["dependencies"] == {"a": ["dep_a"]}
        for architecture in result.manifest["architectures"]
    )

    for architecture in result.manifest["architectures"]:
        if architecture["architecture_id"] == "pruned_flat_baseline":
            continue
        assert architecture["topology"] == "peer"
        assert architecture["agent_count"] == len(architecture["agents"])
        assert "parent_tools" not in architecture
        assigned = set(architecture["shared_tools"])
        assigned.update(
            tool for agent in architecture["agents"].values() for tool in agent["tools"]
        )
        assert set(result.manifest["historical_tool_capability_tools"]) <= assigned
        for agent in architecture["agents"].values():
            if "a" in agent["tools"]:
                assert "dep_a" in agent["tools"]

    candidate = next(
        candidate
        for candidate in result.all_candidates
        if candidate.agent_count == 2
        and candidate.shared_tools == ("shared",)
        and any(
            set(agent) - {"shared"} == {"a", "b", "dep_a"}
            for agent in candidate.agent_tools
        )
    )
    assert candidate.agent_definition_costs == (42.0, 37.0)
    assert candidate.historical_activation_rates == (2 / 3, 2 / 3)
    assert candidate.cross_agent_session_frequency == 1 / 3
    assert candidate.expected_handoff_count == 1 / 3
    assert candidate.expected_delegation_count == 1 / 3
    assert candidate.expected_context_cost_before_communication == 100 / 3
    assert candidate.expected_context_cost_after_communication == 164 / 3
    assert candidate.dependency_closed is True


def test_search_limits_placement_choices_to_exclusive_or_shared_all() -> None:
    result = search_partitions(
        sessions=[
            Session("one", "codex", ["a"], {"a", "b", "shared"}),
            Session("two", "codex", ["b"], {"a", "b", "shared"}),
        ],
        stats=_stats(),
        required_tools={"a", "b"},
        global_tools={"shared"},
        dependencies={"a": {"dep_a"}},
        max_agents=2,
    )

    retained = {"a", "b", "dep_a", "shared"}
    two_agent = [
        candidate for candidate in result.all_candidates if candidate.agent_count == 2
    ]

    assert {candidate.placement_strategy for candidate in two_agent} == {
        "exclusive",
        "shared_all",
    }
    assert {frozenset(candidate.shared_tools) for candidate in two_agent} == {
        frozenset({"shared"}),
        frozenset(retained),
    }
    assert {
        architecture["placement_strategy"]
        for architecture in result.manifest["architectures"]
        if architecture["agent_count"] == 2
    } <= {"exclusive", "shared_all"}
    assert all(
        set().union(*(set(tools) for tools in candidate.agent_tools)) == retained
        for candidate in two_agent
    )


def test_search_retains_only_non_dominated_candidates_in_frontier() -> None:
    sessions = [
        Session("one", "codex", ["a"], {"a"}),
        Session("two", "codex", ["b"], {"b"}),
    ]
    result = search_partitions(
        sessions=sessions,
        stats={
            "a": SimpleNamespace(definition_tokens=10),
            "b": SimpleNamespace(definition_tokens=10),
        },
        required_tools={"a", "b"},
        max_agents=2,
    )

    assert result.pareto_candidates
    assert all(candidate.is_pareto_optimal for candidate in result.pareto_candidates)
    assert {candidate.architecture_id for candidate in result.pareto_candidates} <= {
        candidate.architecture_id for candidate in result.all_candidates
    }
    assert len(
        {candidate.architecture_id for candidate in result.pareto_candidates}
    ) == len(result.pareto_candidates)


def test_generated_manifest_uses_the_run_baseline() -> None:
    result = search_partitions(
        sessions=[Session("one", "codex", ["exec"], {"exec"})],
        stats={"exec": SimpleNamespace(definition_tokens=10)},
        required_tools={"exec"},
        max_agents=1,
    )

    manifest = build_architecture_manifest(result.manifest)
    assert manifest.baseline.parent_tools == frozenset({"exec"})


def test_missing_observed_exposure_is_not_treated_as_zero_context() -> None:
    result = search_partitions(
        sessions=[Session("one", "codex", ["a"], exposure_source="not_observed")],
        stats={"a": SimpleNamespace(definition_tokens=10)},
        required_tools={"a"},
        max_agents=1,
    )

    candidate = result.all_candidates[0]
    assert candidate.expected_context_cost_before_communication is None
    assert candidate.expected_context_cost_after_communication is None
    assert candidate.is_cost_complete is False


def test_delegation_excludes_initial_handling_agent_and_keeps_handoffs_separate() -> (
    None
):
    result = search_partitions(
        sessions=[Session("one", "codex", ["a", "b"], {"a", "b"})],
        stats=_stats(),
        required_tools={"a", "b"},
        max_agents=2,
        communication_tokens_per_handoff=4,
        delegation_tokens_per_activation=2,
    )

    candidate = next(
        candidate for candidate in result.all_candidates if candidate.agent_count == 2
    )
    assert candidate.expected_delegation_count == 1.0
    assert candidate.expected_handoff_count == 1.0
    assert candidate.expected_context_cost_after_communication == 36.0


def test_search_reports_pareto_scope_for_exhaustive_and_bounded_search() -> None:
    sessions = [Session("one", "codex", ["a", "b"], {"a", "b"})]
    exhaustive = search_partitions(
        sessions=sessions,
        stats=_stats(),
        required_tools={"a", "b"},
        max_agents=2,
    )
    bounded = search_partitions(
        sessions=sessions,
        stats=_stats(),
        required_tools={"a", "b"},
        max_agents=2,
        max_exhaustive_units=1,
    )

    assert exhaustive.pareto_scope == "global"
    assert exhaustive.search_strategy == "exhaustive"
    assert exhaustive.report["search"]["pareto_scope"] == "global"
    assert all(
        candidate.pareto_scope == "global" for candidate in exhaustive.pareto_candidates
    )
    assert bounded.pareto_scope == "evaluated_subset"
    assert bounded.search_strategy == "bounded"
    assert all(
        candidate.pareto_scope == "evaluated_subset"
        for candidate in bounded.pareto_candidates
    )


def test_all_runtime_exposure_model_can_evaluate_missing_direct_exposure() -> None:
    result = search_partitions(
        sessions=[Session("one", "codex", ["a"], exposure_source="not_observed")],
        stats={"a": SimpleNamespace(definition_tokens=10)},
        required_tools={"a"},
        max_agents=1,
        exposure_model="all_runtime_tools",
    )

    candidate = result.all_candidates[0]
    assert candidate.expected_context_cost_before_communication == 10.0
    assert candidate.expected_context_cost_after_communication == 10.0
    assert candidate.is_cost_complete is True


def test_global_tool_dependencies_stay_on_parent_surface() -> None:
    result = search_partitions(
        sessions=[Session("one", "codex", ["shared"], {"shared"})],
        stats={
            "shared": SimpleNamespace(definition_tokens=10),
            "shared_dep": SimpleNamespace(definition_tokens=5),
            "other": SimpleNamespace(definition_tokens=20),
        },
        required_tools={"shared", "other"},
        global_tools={"shared"},
        dependencies={"shared": {"shared_dep"}},
        max_agents=1,
    )

    candidate = next(
        candidate for candidate in result.all_candidates if candidate.agent_count == 1
    )
    assert candidate.shared_tools == ("shared", "shared_dep")
    assert candidate.agent_tools == (("other", "shared", "shared_dep"),)


def test_all_global_surface_still_emits_a_k_one_candidate() -> None:
    result = search_partitions(
        sessions=[Session("one", "codex", ["shared"], {"shared"})],
        stats={"shared": SimpleNamespace(definition_tokens=10)},
        required_tools={"shared"},
        global_tools={"shared"},
        max_agents=2,
    )

    assert [candidate.agent_count for candidate in result.all_candidates] == [1]
    assert result.all_candidates[0].agent_tools == (("shared",),)
    assert result.manifest["architectures"][0]["architecture_id"] == (
        "pruned_flat_baseline"
    )


def test_nmf_units_are_frozen_for_search_then_split_during_refinement() -> None:
    result = search_partitions(
        sessions=[
            Session("one", "codex", ["a", "c"], {"a", "c"}),
            Session("two", "codex", ["b", "d"], {"b", "d"}),
        ],
        stats={
            name: SimpleNamespace(definition_tokens=10) for name in ("a", "b", "c", "d")
        },
        required_tools={"a", "b", "c", "d"},
        max_agents=2,
        search_hints={
            "strong_communities": [
                {"factor": 1, "tools": ["a", "b"], "soft_lock": True},
                {"factor": 2, "tools": ["c", "d"], "soft_lock": True},
            ]
        },
    )

    search = result.report["search"]
    assert search["search_units_before_screening"] == 4
    assert search["search_units_after_screening"] == 2
    assert search["search_units_after_refinement"] == 4
    assert search["stages"] == [
        {"name": "screen", "effective_search_units": 4},
        {"name": "nmf", "effective_search_units": 2},
        {"name": "freeze", "effective_search_units": 2},
        {"name": "search", "effective_search_units": 2},
        {"name": "refine", "effective_search_units": 4},
    ]
    assert any(
        candidate.agent_count == 2
        and any(set(tools) == {"a", "b"} for tools in candidate.agent_tools)
        and any(set(tools) == {"c", "d"} for tools in candidate.agent_tools)
        for candidate in result.all_candidates
    )
    assert any(
        candidate.agent_count == 2
        and any(set(tools) == {"a", "c"} for tools in candidate.agent_tools)
        and any(set(tools) == {"b", "d"} for tools in candidate.agent_tools)
        for candidate in result.all_candidates
    )
    assert result.pareto_candidates
