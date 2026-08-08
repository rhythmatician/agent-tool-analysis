"""Freshness-weighted evidence without weakening lifetime capability safety."""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Iterable, Mapping

from .telemetry_ingestion import EvidenceSession


@dataclass(frozen=True)
class FreshnessConfig:
    """Configurable half-life and reporting windows for current evidence."""

    half_life_days: float = 30.0
    current_window_days: float = 90.0
    trial_window_days: float = 14.0
    current_weight_threshold: float = 0.25

    def validate(self) -> None:
        if self.half_life_days <= 0:
            raise ValueError("Freshness half-life must be positive.")
        if self.current_window_days < 0 or self.trial_window_days < 0:
            raise ValueError("Freshness windows cannot be negative.")
        if not 0 <= self.current_weight_threshold <= 1:
            raise ValueError("Freshness current-weight threshold must be between 0 and 1.")


@dataclass(frozen=True)
class ToolFreshness:
    """Lifetime and freshness-weighted evidence for one tool."""

    tool: str
    lifetime_sessions: int
    lifetime_calls: int
    weighted_sessions: float
    weighted_calls: float
    first_seen: str | None
    last_seen: str | None
    age_days: float | None
    status: str
    trial: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "tool": self.tool,
            "lifetime_sessions": self.lifetime_sessions,
            "lifetime_calls": self.lifetime_calls,
            "weighted_sessions": self.weighted_sessions,
            "weighted_calls": self.weighted_calls,
            "first_seen": self.first_seen,
            "last_seen": self.last_seen,
            "age_days": self.age_days,
            "status": self.status,
            "trial": self.trial,
        }


def decay_weight(age_days: float, half_life_days: float = 30.0) -> float:
    """Return exponential freshness weight, where one half-life means 0.5."""

    if age_days < 0:
        raise ValueError("Freshness age cannot be negative.")
    if half_life_days <= 0:
        raise ValueError("Freshness half-life must be positive.")
    return math.pow(0.5, age_days / half_life_days)


def _utc(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def _timestamp(value: datetime | None) -> str | None:
    return _utc(value).isoformat() if value else None


def session_freshness_weight(
    session: EvidenceSession, now: datetime, half_life_days: float
) -> float:
    """Return one session's current-evidence weight."""
    if session.observed_at is None:
        return 1.0
    age_days = max(
        (now - _utc(session.observed_at)).total_seconds() / 86400,
        0.0,
    )
    return decay_weight(age_days, half_life_days)


def _effective_now(
    sessions: Iterable[EvidenceSession], as_of: datetime | None
) -> datetime:
    if as_of:
        return _utc(as_of)
    observed = [session.observed_at for session in sessions if session.observed_at]
    return max((_utc(value) for value in observed), default=datetime.now(timezone.utc))


def analyze_freshness(
    sessions: Iterable[EvidenceSession],
    *,
    config: FreshnessConfig | None = None,
    as_of: datetime | None = None,
) -> dict[str, Any]:
    """Classify tools while preserving a separate lifetime-required set.

    Sessions without timestamps are treated as equally weighted and reported as
    timestamp-unknown, rather than being silently declared old or current.
    """

    config = config or FreshnessConfig()
    config.validate()
    session_list = list(sessions)
    now = _effective_now(session_list, as_of)
    mcp_tools = {
        tool
        for session in session_list
        for tools in session.provider_tool_membership.values()
        for tool in tools
    }
    records: dict[str, ToolFreshness] = {}
    for tool in sorted({name for session in session_list for name in session.tool_set}):
        tool_sessions = [session for session in session_list if tool in session.tool_set]
        observed = [session.observed_at for session in tool_sessions if session.observed_at]
        first = min((_utc(value) for value in observed), default=None)
        last = max((_utc(value) for value in observed), default=None)
        weighted_sessions = 0.0
        weighted_calls = 0.0
        for session in tool_sessions:
            weight = session_freshness_weight(session, now, config.half_life_days)
            weighted_sessions += weight
            weighted_calls += session.calls.count(tool) * weight
        age_days = (
            max((now - last).total_seconds() / 86400, 0.0) if last else None
        )
        trial = (
            tool in mcp_tools
            and first is not None
            and max((now - first).total_seconds() / 86400, 0.0)
            <= config.trial_window_days
        )
        current = (
            age_days is not None
            and age_days <= config.current_window_days
            and weighted_sessions >= config.current_weight_threshold
        )
        status = "current" if current else "currently_low_frequency"
        if first is None:
            status = "timestamp_unknown"
        records[tool] = ToolFreshness(
            tool=tool,
            lifetime_sessions=len(tool_sessions),
            lifetime_calls=sum(session.calls.count(tool) for session in tool_sessions),
            weighted_sessions=weighted_sessions,
            weighted_calls=weighted_calls,
            first_seen=_timestamp(first),
            last_seen=_timestamp(last),
            age_days=age_days,
            status=status,
            trial=trial,
        )

    lifetime_required = sorted(name for name, record in records.items() if record.lifetime_calls)
    current = sorted(name for name, record in records.items() if record.status == "current")
    low_frequency = sorted(
        name for name, record in records.items() if record.status == "currently_low_frequency"
    )
    trial = sorted(name for name, record in records.items() if record.trial)
    return {
        "config": {
            "half_life_days": config.half_life_days,
            "current_window_days": config.current_window_days,
            "trial_window_days": config.trial_window_days,
            "current_weight_threshold": config.current_weight_threshold,
        },
        "as_of": now.isoformat(),
        "tools": {name: record.as_dict() for name, record in records.items()},
        "lifetime_required": lifetime_required,
        "current": current,
        "currently_low_frequency": low_frequency,
        "trial": trial,
        "timestamped_sessions": sum(session.observed_at is not None for session in session_list),
        "timestamp_unknown_sessions": sum(session.observed_at is None for session in session_list),
    }


def session_weights(
    sessions: Iterable[EvidenceSession],
    *,
    config: FreshnessConfig | None = None,
    as_of: datetime | None = None,
) -> dict[str, float]:
    """Return weights for current-analysis matrices and search graphs."""

    config = config or FreshnessConfig()
    config.validate()
    session_list = list(sessions)
    now = _effective_now(session_list, as_of)
    return {
        session.session_id: (
            session_freshness_weight(session, now, config.half_life_days)
        )
        for session in session_list
    }


def trial_workload_opportunities(
    sessions: Iterable[EvidenceSession],
    freshness: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Describe relevant historical workloads in which trial tools can be tested."""

    trial_tools = set(freshness.get("trial", ()))
    opportunities = []
    for session in sessions:
        matched = sorted(session.tool_set & trial_tools)
        if not matched:
            continue
        workload = sorted(session.tool_set - trial_tools)
        opportunities.append(
            {
                "session_id": session.session_id,
                "trial_tools": matched,
                "related_workload_tools": workload,
                "relevance": "historical_co_usage",
            }
        )
    return opportunities
