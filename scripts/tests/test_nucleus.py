"""Tests for canonical capability aliasing and nucleus detection."""

from __future__ import annotations

import pytest

from optimize_agent_tools.nucleus import (
    ALWAYS_SHARED,
    DEFAULT_NUCLEUS_THRESHOLD,
    canonical_id,
    collapsed_coverage,
    detect_nucleus,
)


class _FakeSession:
    def __init__(self, tools):
        self.calls = list(tools)
        self.tool_set = set(tools)


def test_canonical_id_collapses_provider_aliases():
    assert canonical_id("copilot_readFile") == "read"
    assert canonical_id("read_file") == "read"
    assert canonical_id("grep_search") == "find_text"
    assert canonical_id("copilot_findTextInFiles") == "find_text"
    assert canonical_id("apply_patch") == "edit"
    assert canonical_id("copilot_multiReplaceString") == "edit"
    assert canonical_id("mcp_excel-mcp_file") == "mcp_excel-mcp_file"


def test_collapsed_coverage_counts_session_once_per_capability():
    sessions = [
        _FakeSession(["copilot_readFile", "read_file", "copilot_applyPatch"]),
        _FakeSession(["read_file"]),
        _FakeSession(["mcp_excel-mcp_file"]),
    ]
    coverage = collapsed_coverage(sessions)
    read_count, read_members = coverage["read"]
    assert read_count == 2  # session 1 counted once despite two aliases
    assert read_members == {"copilot_readFile", "read_file"}
    assert coverage["edit"][0] == 1
    assert coverage["mcp_excel-mcp_file"][0] == 1


def test_detect_nucleus_includes_high_coverage_capabilities():
    sessions = [
        _FakeSession(["copilot_readFile", "copilot_applyPatch", "copilot_findFiles"]),
        _FakeSession(["read_file", "grep_search", "file_search"]),
        _FakeSession(["copilot_readFile", "copilot_findTextInFiles"]),
        _FakeSession(["read_file", "copilot_replaceString"]),
    ]
    result = detect_nucleus(sessions, threshold=0.5)
    capabilities = {cap.capability for cap in result.capabilities}
    # read: 4/4, find_text: 2/4, edit: 3/4 -> in; find_files: 2/4 at 0.5 in
    assert "read" in capabilities
    assert "edit" in capabilities
    # coordination tools are always shared
    for tool in ALWAYS_SHARED:
        assert tool in result.raw_tool_ids


def test_detect_nucleus_excludes_low_coverage_specialists():
    sessions = [
        _FakeSession(["copilot_readFile"] * 1 + ["mcp_excel-mcp_file"]),
        _FakeSession(["copilot_readFile"]),
        _FakeSession(["copilot_readFile"]),
        _FakeSession(["copilot_readFile"]),
    ]
    result = detect_nucleus(sessions, threshold=0.5)
    capabilities = {cap.capability for cap in result.capabilities}
    assert "read" in capabilities
    assert "mcp_excel-mcp_file" not in capabilities
    assert "mcp_excel-mcp_file" not in result.raw_tool_ids


def test_explicit_additions_override_threshold():
    sessions = [_FakeSession(["copilot_readFile"])]
    result = detect_nucleus(sessions, threshold=0.9, explicit=["mcp_excel-mcp_file"])
    capabilities = {cap.capability: cap.reason for cap in result.capabilities}
    assert capabilities.get("mcp_excel-mcp_file") == "explicit"


def test_threshold_validation():
    with pytest.raises(ValueError):
        detect_nucleus([], threshold=1.5)


def test_default_threshold_matches_design():
    assert DEFAULT_NUCLEUS_THRESHOLD == 0.40
