"""Evidence-based translation from telemetry capabilities to host selectors."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, Mapping

_UNKNOWN_REFERENCE = re.compile(
    r"(?:unknownExtensionReference|unknown extension reference)[^'\"]*['\"]([^'\"]+)['\"]",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class SelectorEvidence:
    """A verified host selector for one canonical capability."""

    capability: str
    selector: str
    source: str
    confidence: str = "verified"


@dataclass(frozen=True)
class SelectorResolution:
    """Resolution result suitable for generation and post-generation gating."""

    selectors: Mapping[str, str]
    unresolved: tuple[str, ...]
    evidence: Mapping[str, SelectorEvidence]

    @property
    def isolation_enforced(self) -> bool:
        return not self.unresolved


def resolve_host_selectors(
    capabilities: Iterable[str],
    evidence: Iterable[SelectorEvidence],
) -> SelectorResolution:
    """Resolve only exact evidence; never infer selectors from punctuation."""
    evidence_by_capability = {
        item.capability: item
        for item in evidence
        if item.confidence in {"verified", "high"} and item.selector
    }
    selectors = {
        capability: evidence_by_capability[capability].selector
        for capability in sorted(set(capabilities))
        if capability in evidence_by_capability
    }
    unresolved = tuple(
        capability
        for capability in sorted(set(capabilities))
        if capability not in selectors
    )
    return SelectorResolution(
        selectors,
        unresolved,
        {capability: evidence_by_capability[capability] for capability in selectors},
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
        if item.confidence in {"verified", "high"} and item.selector
    }
    selectors = dict(resolution.selectors)
    resolved_evidence = dict(resolution.evidence)
    for selector in unknown:
        item = evidence_by_selector.get(selector)
        if item is None:
            continue
        selectors[item.capability] = item.selector
        resolved_evidence[item.capability] = item
    unresolved = tuple(
        capability
        for capability in resolution.unresolved
        if capability not in selectors
    )
    return SelectorResolution(selectors, unresolved, resolved_evidence)
