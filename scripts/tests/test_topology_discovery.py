from optimize_agent_tools.telemetry_ingestion import Session
from optimize_agent_tools.topology_discovery import discover_topologies


def test_topology_discovery_reports_directional_and_symmetric_evidence() -> None:
    report = discover_topologies(
        [
            Session("one", "codex", ["edit", "spawn_agent", "review"]),
            Session("two", "codex", ["review", "spawn_agent", "edit"]),
        ]
    )

    assert set(candidate["topology"] for candidate in report["candidates"]) == {
        "flat",
        "peer",
        "coordinator_children",
    }
    assert report["evidence"]["transitions"] == {
        "edit->review": 1,
        "review->edit": 1,
    }
    assert report["evidence"]["origin_symmetry"] == 1.0
    assert report["best_candidate"]["topology"] == "peer"
    assert all(
        "hypothesis" in evidence
        for candidate in report["candidates"]
        for evidence in candidate["evidence"]
    )


def test_topology_discovery_favors_flat_without_delegation() -> None:
    report = discover_topologies(
        [Session("one", "codex", ["edit", "exec"]), Session("two", "codex", ["review"])]
    )

    assert report["best_candidate"]["topology"] == "flat"
    assert report["evidence"]["delegation_events"] == 0


def test_topology_discovery_does_not_hide_directional_imbalance() -> None:
    report = discover_topologies(
        [
            Session("one", "codex", ["edit", "spawn_agent", "review"]),
            Session("two", "codex", ["edit", "spawn_agent", "review"]),
            Session("three", "codex", ["edit", "spawn_agent", "review"]),
            Session("four", "codex", ["review", "spawn_agent", "edit"]),
        ]
    )

    assert report["evidence"]["origin_symmetry"] == 0.5
