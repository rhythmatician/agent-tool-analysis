"""Evidence-based translation from telemetry capabilities to host selectors."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable, Iterable, Mapping

_UNKNOWN_REFERENCE = re.compile(
    r"(?:unknownExtensionReference|unknown extension reference|unknownSelector|unknown selector)[^'\"]*['\"]([^'\"]+)['\"]",
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
class GenerationValidationReport:
    """Post-generation selector validation and bounded repair outcome."""

    resolution: SelectorResolution
    applied_selectors: Mapping[str, str]
    skipped_overwrites: tuple[str, ...]
    diagnostics: tuple[str, ...]
    unresolved_selector_references: tuple[str, ...]
    repair_attempted: bool
    repair_applied: bool
    generation_count: int

    @property
    def validation_passed(self) -> bool:
        return not self.unresolved_selector_references

    @property
    def validation_status(self) -> str:
        return "passed" if self.validation_passed else "failed"

    @property
    def unresolved_capabilities(self) -> tuple[str, ...]:
        return self.resolution.unresolved


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


def bounded_generation_selectors(
    selectors: Mapping[str, str],
    existing_selectors: Mapping[str, str] | None = None,
    *,
    allow_overwrite: bool = False,
) -> tuple[dict[str, str], tuple[str, ...]]:
    """Merge generated selectors into existing config without implicit overwrite."""
    merged = dict(existing_selectors or {})
    skipped_overwrites: list[str] = []
    for capability, selector in sorted(selectors.items()):
        if (
            capability in merged
            and merged[capability] != selector
            and not allow_overwrite
        ):
            skipped_overwrites.append(capability)
            continue
        merged[capability] = selector
    return merged, tuple(skipped_overwrites)


def run_generation_validation(
    resolution: SelectorResolution,
    evidence: Iterable[SelectorEvidence],
    generate_and_validate: Callable[[Mapping[str, str]], Iterable[str]],
    *,
    existing_selectors: Mapping[str, str] | None = None,
    allow_overwrite: bool = False,
) -> GenerationValidationReport:
    """Generate once, optionally repair once from diagnostics, then revalidate."""
    evidence_list = tuple(evidence)
    applied_selectors, skipped_overwrites = bounded_generation_selectors(
        resolution.selectors,
        existing_selectors,
        allow_overwrite=allow_overwrite,
    )
    diagnostics = tuple(generate_and_validate(applied_selectors))
    unresolved_refs = unknown_extension_references(diagnostics)
    generation_count = 1

    repaired = bounded_selector_repair(resolution, diagnostics, evidence_list)
    repair_applied = repaired.selectors != resolution.selectors
    if repair_applied:
        generation_count += 1
        applied_selectors, skipped_after_repair = bounded_generation_selectors(
            repaired.selectors,
            existing_selectors,
            allow_overwrite=allow_overwrite,
        )
        skipped_overwrites = tuple(
            sorted(set(skipped_overwrites) | set(skipped_after_repair))
        )
        diagnostics = tuple(generate_and_validate(applied_selectors))
        unresolved_refs = unknown_extension_references(diagnostics)

    return GenerationValidationReport(
        resolution=repaired if repair_applied else resolution,
        applied_selectors=applied_selectors,
        skipped_overwrites=skipped_overwrites,
        diagnostics=diagnostics,
        unresolved_selector_references=unresolved_refs,
        repair_attempted=bool(unresolved_refs) or repair_applied,
        repair_applied=repair_applied,
        generation_count=generation_count,
    )
