from optimize_agent_tools.host_selector_resolution import (
    SelectorEvidence,
    bounded_selector_repair,
    resolve_host_selectors,
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
