from optimize_agent_tools.host_selector_resolution import (
    CapabilityBinding,
    SelectorEvidence,
    bounded_selector_repair,
    post_generation_selector_validation,
    resolve_host_selectors,
    resolve_telemetry_selectors,
    validate_generated_selectors,
    validate_host_realization,
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


def test_post_generation_validation_reports_a_successful_single_repair() -> None:
    initial = resolve_host_selectors(
        ["github.fetch_issue", "github.create_issue"],
        [
            SelectorEvidence("github.fetch_issue", "github.fetch_issue", "mcp"),
        ],
    )

    result = post_generation_selector_validation(
        initial,
        ["promptValidator.unknownExtensionReference: 'github.create_issue'"],
        [
            SelectorEvidence("github.fetch_issue", "github.fetch_issue", "mcp"),
            SelectorEvidence("github.create_issue", "github.create_issue", "mcp"),
        ],
        [],
    )

    assert result.status == "repaired"
    assert result.repair_attempted is True
    assert result.resolution.isolation_enforced is True
    assert result.unresolved_capabilities == ()
    assert result.unknown_references == ()
    assert result.to_report() == {
        "status": "repaired",
        "repair_attempted": True,
        "isolation_enforced": True,
        "unresolved_capabilities": [],
        "ambiguous_capabilities": [],
        "initial_unknown_references": ["github.create_issue"],
        "unknown_references": [],
        "diagnostics": [],
    }


def test_post_generation_validation_reports_unresolved_selectors_after_revalidation() -> None:
    initial = resolve_host_selectors(
        ["github.fetch_issue"],
        [SelectorEvidence("github.fetch_issue", "github.fetch_issue", "mcp")],
    )
    diagnostics = [
        "promptValidator.unknownExtensionReference: 'github.fetch_issue'"
    ]

    result = post_generation_selector_validation(
        initial,
        diagnostics,
        [SelectorEvidence("github.fetch_issue", "github.fetch_issue", "mcp")],
        diagnostics,
    )

    assert result.status == "unresolved"
    assert result.repair_attempted is True
    assert result.resolution.isolation_enforced is True
    assert result.unknown_references == ("github.fetch_issue",)
    assert result.to_report()["diagnostics"] == diagnostics


def test_post_generation_validation_accepts_clean_generation_without_repair() -> None:
    initial = resolve_host_selectors(
        ["github.fetch_issue"],
        [SelectorEvidence("github.fetch_issue", "github.fetch_issue", "mcp")],
    )

    result = post_generation_selector_validation(initial, [], [], [])

    assert result.status == "validated"
    assert result.repair_attempted is False
    assert result.to_report()["isolation_enforced"] is True


def test_generated_selector_validation_retries_once_after_exact_repair() -> None:
    initial = resolve_host_selectors(
        ["github.create_issue"],
        [],
    )
    calls: list[dict[str, str]] = []

    def generate(selectors: dict[str, str]) -> list[str]:
        calls.append(dict(selectors))
        return (
            ["promptValidator.unknownExtensionReference: 'github.create_issue'"]
            if not selectors
            else []
        )

    result = validate_generated_selectors(
        initial,
        generate,
        [SelectorEvidence("github.create_issue", "github.create_issue", "mcp")],
    )

    assert result.status == "repaired"
    assert calls == [{}, {"github.create_issue": "github.create_issue"}]


def test_generic_host_aliases_do_not_realize_canonical_capabilities() -> None:
    result = validate_host_realization(
        ["github.fetch_issue", "github.create_issue"],
        selectors={
            "execute": "execute",
            "read": "read",
            "edit": "edit",
            "search": "search",
            "agent": "agent",
        },
    )

    assert result.status == "incomplete"
    assert result.unresolved_capabilities == (
        "github.create_issue",
        "github.fetch_issue",
    )


def test_exact_selectors_realize_required_and_exclude_architecture() -> None:
    result = validate_host_realization(
        ["github.fetch_issue"],
        ["github.delete_issue"],
        selectors={"github.fetch_issue": "github.fetch_issue"},
    )

    assert result.is_complete is True
    assert result.reintroduced_capabilities == ()


def test_wildcard_requires_verified_inventory_and_preserves_exclusions() -> None:
    unverified = validate_host_realization(
        ["github.fetch_issue"],
        wildcard=True,
        available_capabilities=["github.fetch_issue"],
    )
    unsafe = validate_host_realization(
        ["github.fetch_issue"],
        ["github.delete_issue"],
        wildcard=True,
        available_capabilities=["github.fetch_issue", "github.delete_issue"],
        all_tools_verified=True,
    )
    safe = validate_host_realization(
        ["github.fetch_issue"],
        ["github.delete_issue"],
        wildcard=True,
        available_capabilities=["github.fetch_issue"],
        all_tools_verified=True,
    )

    assert unverified.status == "incomplete"
    assert unsafe.reintroduced_capabilities == ("github.delete_issue",)
    assert unsafe.status == "incomplete"
    assert safe.is_complete is True
