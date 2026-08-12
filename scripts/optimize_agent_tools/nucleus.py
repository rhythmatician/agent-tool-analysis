"""Canonical capability aliasing and shared-nucleus detection.

Telemetry providers expose the same capability under different tool IDs
(e.g. ``copilot_readFile`` vs ``read_file``). Counting raw IDs under-reports
ubiquitous core skills and lets them leak into specialist clusters. This
module collapses provider variants into canonical capabilities *before*
thresholding, then detects the shared nucleus that every agent must carry.

Design contract (decided up front, see SKILL.md "HITL nucleus design"):

1. Canonical alias collapse happens before any session counting.
2. A capability is nucleus when its collapsed session coverage meets the
   threshold (default 0.40), or it is always-shared coordination
   infrastructure, or the user explicitly adds it (HITL step).
3. Clustering runs with nucleus member tools excluded so a true specialist
   must show ``internal_affinity > max_external_affinity`` against what is
   left; leaky core families no longer absorb real clusters.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

NUCLEUS_ALIAS_VERSION = 1

# Canonical capability -> observed telemetry IDs. Hosts rename tools over
# time; extend this map when new aliases appear in telemetry, and bump
# NUCLEUS_ALIAS_VERSION.
CANONICAL_ALIASES: dict[str, str] = {
    # read
    "copilot_readFile": "read",
    "read_file": "read",
    # text search
    "copilot_findTextInFiles": "find_text",
    "grep_search": "find_text",
    # file search
    "copilot_findFiles": "find_files",
    "file_search": "find_files",
    # directory listing
    "copilot_listDirectory": "list_dir",
    "list_dir": "list_dir",
    # edit / write
    "copilot_applyPatch": "edit",
    "apply_patch": "edit",
    "copilot_createFile": "edit",
    "create_file": "edit",
    "copilot_replaceString": "edit",
    "replace_string_in_file": "edit",
    "copilot_multiReplaceString": "edit",
    "multi_replace_string_in_file": "edit",
    "insert_edit_into_file": "edit",
    "copilot_insertEdit": "edit",
    "vscode_editFile_internal": "edit",
    "copilot_createDirectory": "edit",
    "create_directory": "edit",
    # diagnostics / change review
    "copilot_getErrors": "errors",
    "get_errors": "errors",
    "get_changed_files": "errors",
    "copilot_getChangedFiles": "errors",
    "testFailure": "errors",
    "copilot_testFailure": "errors",
    # terminal
    "run_in_terminal": "terminal",
    "get_terminal_output": "terminal",
    "kill_terminal": "terminal",
    "await_terminal": "terminal",
    "send_to_terminal": "terminal",
    "terminal_last_command": "terminal",
    "terminalLastCommand": "terminal",
    "terminal_selection": "terminal",
    "terminalSelection": "terminal",
}

# Coordination infrastructure is shared regardless of measured coverage; peer
# agents need it to delegate to each other.
ALWAYS_SHARED: frozenset[str] = frozenset({"agent", "send_message", "wait"})

DEFAULT_NUCLEUS_THRESHOLD = 0.40


def canonical_id(tool: str) -> str:
    """Map a telemetry tool ID to its canonical capability ID."""
    return CANONICAL_ALIASES.get(tool, tool)


@dataclass(frozen=True)
class NucleusCapability:
    capability: str
    members: tuple[str, ...]
    session_coverage: float
    sessions: int
    reason: str  # "coverage" | "always_shared" | "explicit"


@dataclass(frozen=True)
class NucleusResult:
    capabilities: tuple[NucleusCapability, ...]
    raw_tool_ids: frozenset[str]
    threshold: float
    alias_version: int

    def to_report(self) -> dict[str, Any]:
        return {
            "threshold": self.threshold,
            "alias_version": self.alias_version,
            "raw_tool_ids": sorted(self.raw_tool_ids),
            "capabilities": [
                {
                    "capability": cap.capability,
                    "members": list(cap.members),
                    "session_coverage": cap.session_coverage,
                    "sessions": cap.sessions,
                    "reason": cap.reason,
                }
                for cap in self.capabilities
            ],
        }


def collapsed_coverage(
    sessions: Iterable[Any],
) -> dict[str, tuple[int, set[str]]]:
    """Return canonical capability -> (session count, member tools).

    A session counts once per capability no matter how many alias variants it
    used.
    """
    coverage: dict[str, tuple[int, set[str]]] = {}
    session_list = list(sessions)
    members_by_capability: dict[str, set[str]] = {}
    counts: dict[str, int] = {}
    for session in session_list:
        tools = getattr(session, "tool_set", None)
        if tools is None:
            tools = set(getattr(session, "calls", ()))
        present = {canonical_id(tool) for tool in tools}
        for capability in present:
            counts[capability] = counts.get(capability, 0) + 1
        for tool in tools:
            members_by_capability.setdefault(canonical_id(tool), set()).add(tool)
    for capability, count in counts.items():
        coverage[capability] = (count, members_by_capability.get(capability, set()))
    return coverage


def detect_nucleus(
    sessions: Iterable[Any],
    *,
    threshold: float = DEFAULT_NUCLEUS_THRESHOLD,
    explicit: Iterable[str] = (),
    always_shared: Iterable[str] = ALWAYS_SHARED,
) -> NucleusResult:
    """Detect the shared nucleus from collapsed canonical coverage.

    ``explicit`` and ``always_shared`` entries are raw telemetry IDs (or
    canonical capability IDs) that must be shared regardless of coverage.
    """
    if not 0 <= threshold <= 1:
        raise ValueError("nucleus threshold must be between 0 and 1")
    session_list = list(sessions)
    total = len(session_list)
    coverage = collapsed_coverage(session_list)

    explicit_ids = set(explicit)
    explicit_capabilities = {canonical_id(tool) for tool in explicit_ids} | (
        explicit_ids & set(coverage)
    )
    always_shared_ids = set(always_shared)

    capabilities: list[NucleusCapability] = []
    raw_ids: set[str] = set()

    for capability, (count, members) in sorted(coverage.items()):
        rate = count / total if total else 0.0
        if rate >= threshold:
            capabilities.append(
                NucleusCapability(
                    capability=capability,
                    members=tuple(sorted(members)),
                    session_coverage=rate,
                    sessions=count,
                    reason="coverage",
                )
            )
            raw_ids.update(members)

    for tool in sorted(always_shared_ids):
        capability = canonical_id(tool)
        if any(cap.capability == capability for cap in capabilities):
            continue
        count, members = coverage.get(capability, (0, set()))
        merged = tuple(sorted(set(members) | {tool}))
        capabilities.append(
            NucleusCapability(
                capability=capability,
                members=merged,
                session_coverage=count / total if total else 0.0,
                sessions=count,
                reason="always_shared",
            )
        )
        raw_ids.update(merged)

    for capability in sorted(explicit_capabilities):
        if any(cap.capability == capability for cap in capabilities):
            continue
        count, members = coverage.get(capability, (0, set()))
        merged = tuple(sorted(set(members) | (explicit_ids & set(members))))
        capabilities.append(
            NucleusCapability(
                capability=capability,
                members=merged,
                session_coverage=count / total if total else 0.0,
                sessions=count,
                reason="explicit",
            )
        )
        raw_ids.update(merged)

    return NucleusResult(
        capabilities=tuple(
            sorted(
                capabilities, key=lambda cap: (-cap.session_coverage, cap.capability)
            )
        ),
        raw_tool_ids=frozenset(raw_ids),
        threshold=threshold,
        alias_version=NUCLEUS_ALIAS_VERSION,
    )
