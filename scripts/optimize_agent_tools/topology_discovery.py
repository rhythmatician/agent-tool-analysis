"""Infer a small, interpretable topology candidate set from call sequences."""

from __future__ import annotations

from collections import Counter
from typing import Any, Iterable

from .telemetry_ingestion import CONTROL_PLANE_TOOLS, EvidenceSession

TOPOLOGY_CANDIDATES = ("flat", "peer", "coordinator_children")
DELEGATION_TOOLS = frozenset({"agent", "followup_task", "spawn_agent"})


def _domain_tools(calls: Iterable[str], control_tools: frozenset[str]) -> list[str]:
    return [
        call
        for call in calls
        if call not in control_tools and call not in DELEGATION_TOOLS
    ]


def discover_topologies(
    sessions: Iterable[EvidenceSession],
    *,
    control_tools: Iterable[str] = CONTROL_PLANE_TOOLS,
) -> dict[str, Any]:
    """Return topology candidates and structural evidence from ordered calls.

    This deliberately reports hypotheses rather than assigning agent identities.
    Delegation markers divide a session into observed pre- and post-delegation
    families; the evidence is useful even when telemetry lacks nested agent IDs.
    """

    session_list = list(sessions)
    controls = frozenset(control_tools)
    delegation_sessions = 0
    delegation_events = 0
    return_events = 0
    pre_families: Counter[str] = Counter()
    post_families: Counter[str] = Counter()
    transitions: Counter[tuple[str, str]] = Counter()

    for session in session_list:
        calls = list(session.called_tools)
        indices = [
            index
            for index, call in enumerate(calls)
            if call in DELEGATION_TOOLS
        ]
        if not indices:
            continue
        delegation_sessions += 1
        delegation_events += len(indices)
        first = indices[0]
        before = _domain_tools(calls[:first], controls)
        after = _domain_tools(calls[first + 1 :], controls)
        if before:
            pre_families[before[-1]] += 1
        if after:
            post_families[after[0]] += 1
        if before and after:
            transitions[(before[-1], after[0])] += 1

        last_delegation = indices[-1]
        post_calls = calls[last_delegation + 1 :]
        if any(call in controls for call in post_calls) and len(
            _domain_tools(post_calls, controls)
        ) > 1:
            return_events += 1

    forward = sum(transitions.values())
    symmetric_mass = 0
    seen_pairs: set[tuple[str, str]] = set()
    for left, right in transitions:
        pair: tuple[str, str] = (
            (left, right) if left <= right else (right, left)
        )
        if pair in seen_pairs:
            continue
        seen_pairs.add(pair)
        if left == right:
            symmetric_mass += transitions[(left, right)]
        else:
            symmetric_mass += 2 * min(
                transitions[(left, right)],
                transitions.get((right, left), 0),
            )
    origin_symmetry = (symmetric_mass / forward) if forward else 0.0
    delegation_rate = (
        delegation_sessions / len(session_list) if session_list else 0.0
    )
    evidence_count = delegation_events + forward + return_events
    confidence = (
        "high"
        if evidence_count >= 5
        else "medium"
        if evidence_count >= 2
        else "low"
    )

    scores = {
        "flat": max(0.0, 1.0 - delegation_rate),
        "peer": delegation_rate * origin_symmetry,
        "coordinator_children": delegation_rate
        * (1.0 - origin_symmetry)
        * (1.0 + (return_events / max(delegation_events, 1))),
    }
    total = sum(scores.values())
    candidates = [
        {
            "topology": topology,
            "score": scores[topology] / total if total else 0.0,
            "confidence": confidence,
            "evidence": [
                "hypothesis uses delegation direction as structural evidence, not a semantic role",
                "candidate remains a hypothesis because telemetry has no nested agent identity",
            ],
        }
        for topology in TOPOLOGY_CANDIDATES
    ]
    return {
        "candidates": candidates,
        "best_candidate": max(candidates, key=lambda candidate: candidate["score"]),
        "evidence": {
            "sessions": len(session_list),
            "delegation_sessions": delegation_sessions,
            "delegation_events": delegation_events,
            "return_to_caller_events": return_events,
            "pre_delegation_families": dict(sorted(pre_families.items())),
            "post_delegation_families": dict(sorted(post_families.items())),
            "transitions": {
                f"{left}->{right}": count
                for (left, right), count in sorted(transitions.items())
            },
            "origin_symmetry": origin_symmetry,
            "activation_asymmetry": abs(
                sum(pre_families.values()) - sum(post_families.values())
            )
            / max(sum(pre_families.values()) + sum(post_families.values()), 1),
            "confidence": confidence,
        },
    }
