from optimize_agent_tools.host_selector_resolution import (
    CapabilityBinding,
    SelectorEvidence,
    bounded_selector_repair,
    resolve_host_selectors,
    resolve_telemetry_selectors,
    unknown_extension_references,
)


def test_resolution_requires_exact_verified_host_evidence() -> None:
    result = resolve_host_selectors(
        ["github.fetch_issue", "github.create_issue"],
        [
            SelectorEvidence("github.fetch_issue", "github.fetch_issue", "registry"),
            SelectorEvidence(
                "github.create_issue", "github/create_issue", "guess", "low"
            ),
        ],
    )

    assert result.selectors == {"github.fetch_issue": "github.fetch_issue"}
    assert result.unresolved == ("github.create_issue",)
    assert result.isolation_enforced is False


def test_unknown_reference_repair_is_exact_and_bounded() -> None:
    evidence = [
        SelectorEvidence("github.fetch_issue", "github.fetch_issue", "mcp"),
        SelectorEvidence("github.create_issue", "github.create_issue", "mcp"),
    ]
    initial = resolve_host_selectors(
        ["github.fetch_issue", "github.create_issue"],
        [evidence[0]],
    )

    assert unknown_extension_references(
        ["promptValidator.unknownExtensionReference: 'github.create_issue'"]
    ) == ("github.create_issue",)
    repaired = bounded_selector_repair(
        initial,
        ["promptValidator.unknownExtensionReference: 'github.create_issue'"],
        evidence,
    )
    assert repaired.isolation_enforced is True
    assert repaired.selectors["github.create_issue"] == "github.create_issue"


def test_telemetry_identity_resolves_to_canonical_capability_and_selector() -> None:
    result = resolve_telemetry_selectors(
        [
            CapabilityBinding(
                "github.create_issue", "mcp.github.createIssue"
            )
        ],
        [
            SelectorEvidence(
                "github.create_issue",
                "github.create_issue",
                "mcp",
                telemetry_id="mcp.github.createIssue",
            )
        ],
    )

    assert result.selectors == {"github.create_issue": "github.create_issue"}
    assert result.unresolved == ()
    assert result.evidence["github.create_issue"].telemetry_id == (
        "mcp.github.createIssue"
    )


def test_untrusted_or_conflicting_selector_evidence_stays_unresolved() -> None:
    result = resolve_telemetry_selectors(
        [CapabilityBinding("github.create_issue", "telemetry.create_issue")],
        [
            SelectorEvidence(
                "github.create_issue",
                "github.create_issue",
                "registry",
                telemetry_id="telemetry.create_issue",
                confidence="verified",
            ),
            SelectorEvidence(
                "github.create_issue",
                "github.create_issue_v2",
                "mcp",
                telemetry_id="telemetry.create_issue",
            ),
        ],
    )

    assert result.selectors == {}
    assert result.unresolved == ("github.create_issue",)
    assert result.isolation_enforced is False


def test_bounded_repair_cannot_resolve_a_capability_not_reported_as_unresolved() -> None:
    initial = resolve_host_selectors(
        ["github.fetch_issue"],
        [SelectorEvidence("github.fetch_issue", "github.fetch_issue", "mcp")],
    )

    repaired = bounded_selector_repair(
        initial,
        ["promptValidator.unknownExtensionReference: 'github.create_issue'"],
        [
            SelectorEvidence("github.fetch_issue", "github.fetch_issue", "mcp"),
            SelectorEvidence("github.create_issue", "github.create_issue", "mcp"),
        ],
    )

    assert repaired.selectors == {"github.fetch_issue": "github.fetch_issue"}
