from datetime import datetime, timedelta, timezone

import pytest

from optimize_agent_tools.freshness import (
    FreshnessConfig,
    analyze_freshness,
    decay_weight,
    session_weights,
    trial_workload_opportunities,
)
from optimize_agent_tools.telemetry_ingestion import Session


def test_exponential_decay_uses_a_configurable_half_life() -> None:
    assert decay_weight(30.0, 30.0) == pytest.approx(0.5)
    assert decay_weight(60.0, 30.0) == pytest.approx(0.25)


def test_lifetime_required_tools_survive_low_current_frequency() -> None:
    now = datetime(2026, 8, 8, tzinfo=timezone.utc)
    sessions = [
        Session("old", "codex", ["historical"], observed_at=now - timedelta(days=180)),
        Session("new", "codex", ["current"], observed_at=now - timedelta(days=2)),
    ]

    report = analyze_freshness(
        sessions,
        config=FreshnessConfig(half_life_days=30, current_window_days=30),
        as_of=now,
    )

    assert report["lifetime_required"] == ["current", "historical"]
    assert report["current"] == ["current"]
    assert report["currently_low_frequency"] == ["historical"]


def test_trial_tools_expose_relevant_historical_workloads() -> None:
    now = datetime(2026, 8, 8, tzinfo=timezone.utc)
    sessions = [
        Session(
            "trial-workload",
            "codex",
            ["new_mcp", "edit", "review"],
            provider_tools={"example-mcp": {"new_mcp"}},
            observed_at=now - timedelta(days=3),
        )
    ]

    freshness = analyze_freshness(sessions, as_of=now)
    opportunities = trial_workload_opportunities(sessions, freshness)

    assert opportunities == [
        {
            "session_id": "trial-workload",
            "trial_tools": ["new_mcp"],
            "related_workload_tools": ["edit", "review"],
            "relevance": "historical_co_usage",
        }
    ]


def test_established_mcp_tools_are_not_trials_when_used_recently() -> None:
    now = datetime(2026, 8, 8, tzinfo=timezone.utc)
    sessions = [
        Session(
            "old",
            "codex",
            ["established_mcp"],
            provider_tools={"example-mcp": {"established_mcp"}},
            observed_at=now - timedelta(days=30),
        ),
        Session(
            "recent",
            "codex",
            ["established_mcp"],
            provider_tools={"example-mcp": {"established_mcp"}},
            observed_at=now - timedelta(days=1),
        ),
    ]

    report = analyze_freshness(sessions, as_of=now)

    assert report["tools"]["established_mcp"]["trial"] is False
    assert report["trial"] == []


def test_unknown_timestamps_are_not_silently_called_current() -> None:
    report = analyze_freshness([Session("legacy", "codex", ["tool"])])

    assert report["timestamp_unknown_sessions"] == 1
    assert report["tools"]["tool"]["status"] == "timestamp_unknown"
    assert session_weights([Session("legacy", "codex", ["tool"])])["legacy"] == 1.0
