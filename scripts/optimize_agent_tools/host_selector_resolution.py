"""Evidence-based translation from telemetry capabilities to host selectors.

The post-generation validation seam deliberately accepts diagnostics from the
initial generation and the one permitted revalidation. It does not generate
files or retry a host more than once.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable, Iterable, Mapping

_UNKNOWN_REFERENCE = re.compile(
    r"(?:unknownExtensionReference|unknown extension reference)[^'\"]*['\"]([^'\"]+)['\"]",
    re.IGNORECASE,
)
_VERIFIED_SOURCES = {
    "registry",
    "local_registry",
    "mcp",
    "extension",
    "existing-agent",
    "existing_agent",
    "provider",
}


@dataclass(frozen=True)
class CapabilityBinding:
    """The explicit relationship between a capability and telemetry identity."""

    capability: str
    telemetry_id: str


@dataclass(frozen=True)
class SelectorEvidence:
    """A verified host selector for one canonical capability."""

    capability: str
    selector: str
    source: str
    confidence: str = "verified"
    telemetry_id: str | None = None


@dataclass(frozen=True)
class SelectorResolution:
    """Resolution result suitable for generation and post-generation gating."""

    selectors: Mapping[str, str]
    unresolved: tuple[str, ...]
    evidence: Mapping[str, SelectorEvidence]
    ambiguous: tuple[str, ...] = ()

    @property
    def isolation_enforced(self) -> bool:
        return not self.unresolved and not self.ambiguous


@dataclass(frozen=True)
class HostRealization:
    """Whether a host configuration realizes a canonical architecture."""

    required_capabilities: tuple[str, ...]
    excluded_capabilities: tuple[str, ...]
    selectors: Mapping[str, str]
    unresolved_capabilities: tuple[str, ...]
    reintroduced_capabilities: tuple[str, ...]
    wildcard: bool
    status: str
    reasons: tuple[str, ...] = ()

    @property
    def is_complete(self) -> bool:
        return self.status == "complete"

    def to_report(self) -> dict[str, object]:
        return {
            "status": self.status,
            "required_capabilities": list(self.required_capabilities),
            "excluded_capabilities": list(self.excluded_capabilities),
            "selectors": dict(self.selectors),
            "unresolved_capabilities": list(self.unresolved_capabilities),
            "reintroduced_capabilities": list(self.reintroduced_capabilities),
            "wildcard": self.wildcard,
            "reasons": list(self.reasons),
        }


def validate_host_realization(
    required_capabilities: Iterable[str],
    excluded_capabilities: Iterable[str] = (),
    selectors: Mapping[str, str] | None = None,
    *,
    wildcard: bool = False,
    available_capabilities: Iterable[str] | None = None,
    all_tools_verified: bool = False,
) -> HostRealization:
    """Gate host materialization against canonical required/excluded sets.

    Canonical capability names are the comparison key. Generic host aliases
    therefore cannot satisfy a telemetry capability merely by appearing in
    ``selectors``. Wildcard configuration is accepted only with an explicit
    host inventory and verification that the inventory preserves the selected
    boundary.
    """
    required = tuple(sorted(set(required_capabilities)))
    excluded = tuple(sorted(set(excluded_capabilities) - set(required)))
    selected = dict(selectors or {})
    available = set(available_capabilities or ())
    reasons: list[str] = []

    if wildcard:
        if not all_tools_verified:
            unresolved = required
            reasons.append("wildcard exposure is not verified")
        else:
            unresolved = tuple(sorted(set(required) - available))
            if unresolved:
                reasons.append("required capabilities are absent from host inventory")
    else:
        unresolved = tuple(
            capability
            for capability in required
            if not selected.get(capability)
        )
        if unresolved:
            reasons.append("required capabilities have no exact host selector")

    reintroduced = tuple(
        capability
        for capability in excluded
        if (wildcard and capability in available) or selected.get(capability)
    )
    if reintroduced:
        reasons.append("excluded capabilities would remain exposed")
    if wildcard and excluded and not all_tools_verified:
        reasons.append("wildcard cannot prove excluded-capability isolation")

    status = (
        "complete"
        if not unresolved and not reintroduced and not reasons
        else "incomplete"
    )
    return HostRealization(
        required,
        excluded,
        selected,
        unresolved,
        reintroduced,
        wildcard,
        status,
        tuple(dict.fromkeys(reasons)),
    )


@dataclass(frozen=True)
class SelectorValidation:
    """Bounded post-generation validation result for generated selectors."""

    resolution: SelectorResolution
    initial_unknown_references: tuple[str, ...]
    unknown_references: tuple[str, ...]
    diagnostics: tuple[str, ...]
    repair_attempted: bool
    status: str

    @property
    def unresolved_capabilities(self) -> tuple[str, ...]:
        return self.resolution.unresolved

    def to_report(self) -> dict[str, object]:
        """Return the stable, user-facing validation summary."""
        return {
            "status": self.status,
            "repair_attempted": self.repair_attempted,
            "isolation_enforced": self.resolution.isolation_enforced
            and not self.unknown_references,
            "unresolved_capabilities": list(self.resolution.unresolved),
            "ambiguous_capabilities": list(self.resolution.ambiguous),
            "initial_unknown_references": list(self.initial_unknown_references),
            "unknown_references": list(self.unknown_references),
            "diagnostics": list(self.diagnostics),
        }


def _is_trusted(item: SelectorEvidence) -> bool:
    source = item.source.casefold().replace(" ", "_")
    return (
        source in _VERIFIED_SOURCES
        and item.confidence in {"verified", "high"}
        and bool(item.selector)
    )


def _select_unique(
    capabilities: Iterable[str],
    evidence: Iterable[SelectorEvidence],
) -> tuple[dict[str, str], dict[str, SelectorEvidence], tuple[str, ...]]:
    requested = sorted(set(capabilities))
    by_capability: dict[str, list[SelectorEvidence]] = {}
    for item in evidence:
        if _is_trusted(item) and item.capability in requested:
            by_capability.setdefault(item.capability, []).append(item)

    selectors: dict[str, str] = {}
    resolved_evidence: dict[str, SelectorEvidence] = {}
    ambiguous: list[str] = []
    for capability in requested:
        candidates = by_capability.get(capability, [])
        selector_values = {item.selector for item in candidates}
        if len(selector_values) == 1:
            selectors[capability] = candidates[0].selector
            resolved_evidence[capability] = candidates[0]
        elif len(selector_values) > 1:
            ambiguous.append(capability)
    return selectors, resolved_evidence, tuple(ambiguous)


def resolve_host_selectors(
    capabilities: Iterable[str],
    evidence: Iterable[SelectorEvidence],
) -> SelectorResolution:
    """Resolve only exact evidence; never infer selectors from punctuation."""
    requested = sorted(set(capabilities))
    selectors, resolved_evidence, ambiguous = _select_unique(requested, evidence)
    unresolved = tuple(
        capability
        for capability in requested
        if capability not in selectors
    )
    return SelectorResolution(selectors, unresolved, resolved_evidence, ambiguous)


def resolve_telemetry_selectors(
    bindings: Iterable[CapabilityBinding],
    evidence: Iterable[SelectorEvidence],
) -> SelectorResolution:
    """Translate telemetry IDs only through exact, trusted identity evidence."""
    binding_list = tuple(bindings)
    evidence_list = tuple(evidence)
    matching = [
        item
        for item in evidence_list
        if any(
            item.capability == binding.capability
            and item.telemetry_id == binding.telemetry_id
            for binding in binding_list
        )
    ]
    return resolve_host_selectors(
        (binding.capability for binding in binding_list),
        matching,
    )


def unknown_extension_references(diagnostics: Iterable[str]) -> tuple[str, ...]:
    """Extract host-reported unknown selectors without reading user content."""
    references: set[str] = set()
    for diagnostic in diagnostics:
        references.update(_UNKNOWN_REFERENCE.findall(diagnostic))
    return tuple(sorted(references))


def bounded_selector_repair(
    resolution: SelectorResolution,
    diagnostics: Iterable[str],
    evidence: Iterable[SelectorEvidence],
) -> SelectorResolution:
    """Perform one exact-evidence repair pass for reported unknown selectors.

    The caller must not invoke this function more than once for a generation.
    Unreported unresolved capabilities remain unresolved, and a diagnostic can
    only be repaired when its exact selector is backed by local evidence.
    """
    unknown = set(unknown_extension_references(diagnostics))
    evidence_by_selector = {
        item.selector: item
        for item in evidence
        if _is_trusted(item)
    }
    selectors = dict(resolution.selectors)
    resolved_evidence = dict(resolution.evidence)
    for selector in unknown:
        item = evidence_by_selector.get(selector)
        if item is None:
            continue
        if item.capability not in resolution.unresolved:
            continue
        selectors[item.capability] = item.selector
        resolved_evidence[item.capability] = item
    unresolved = tuple(
        capability
        for capability in resolution.unresolved
        if capability not in selectors
    )
    return SelectorResolution(
        selectors, unresolved, resolved_evidence, resolution.ambiguous
    )


def post_generation_selector_validation(
    resolution: SelectorResolution,
    generation_diagnostics: Iterable[str],
    evidence: Iterable[SelectorEvidence],
    revalidation_diagnostics: Iterable[str],
) -> SelectorValidation:
    """Inspect generation diagnostics, repair once, and report revalidation.

    ``revalidation_diagnostics`` must come from the host's single validation
    after the optional repair. The function performs no implicit retries and
    retains unresolved capabilities when the host gives no trusted evidence.
    """
    initial_diagnostics = tuple(generation_diagnostics)
    final_diagnostics = tuple(revalidation_diagnostics)
    initial_unknown = unknown_extension_references(initial_diagnostics)
    repair_attempted = bool(initial_unknown)
    final_resolution = (
        bounded_selector_repair(resolution, initial_diagnostics, evidence)
        if repair_attempted
        else resolution
    )
    unknown = unknown_extension_references(final_diagnostics)
    if (
        unknown
        or final_resolution.unresolved
        or final_resolution.ambiguous
    ):
        status = "unresolved"
    elif repair_attempted:
        status = "repaired"
    else:
        status = "validated"
    return SelectorValidation(
        resolution=final_resolution,
        initial_unknown_references=initial_unknown,
        unknown_references=unknown,
        diagnostics=final_diagnostics,
        repair_attempted=repair_attempted,
        status=status,
    )


def validate_generated_selectors(
    resolution: SelectorResolution,
    generate_diagnostics: Callable[[Mapping[str, str]], Iterable[str]],
    evidence: Iterable[SelectorEvidence],
) -> SelectorValidation:
    """Run generation validation with at most one evidence-backed repair."""
    evidence_list = tuple(evidence)
    initial_diagnostics = tuple(generate_diagnostics(resolution.selectors))
    initial_unknown = unknown_extension_references(initial_diagnostics)
    if not initial_unknown:
        return post_generation_selector_validation(
            resolution, initial_diagnostics, evidence_list, ()
        )
    repaired = bounded_selector_repair(
        resolution, initial_diagnostics, evidence_list
    )
    revalidation_diagnostics = tuple(generate_diagnostics(repaired.selectors))
    return post_generation_selector_validation(
        resolution,
        initial_diagnostics,
        evidence_list,
        revalidation_diagnostics,
    )
