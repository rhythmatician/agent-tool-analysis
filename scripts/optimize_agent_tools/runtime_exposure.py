"""Host-neutral runtime exposure capabilities and evidence."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal, Mapping

ExposureStatus = Literal["known", "inferred", "unsupported", "unknown"]


@dataclass(frozen=True)
class ExposureFact:
    """A runtime fact whose absence must not be interpreted as a default."""

    value: Any
    status: ExposureStatus
    source: str
    note: str | None = None

    def __post_init__(self) -> None:
        if self.status not in {"known", "inferred", "unsupported", "unknown"}:
            raise ValueError(f"Unsupported exposure status: {self.status!r}")
        if not self.source:
            raise ValueError("Exposure fact source must be non-empty.")
        if self.status in {"unsupported", "unknown"} and self.value is not None:
            raise ValueError(
                "Unsupported and unknown exposure facts must not carry a value."
            )

    @classmethod
    def unknown(cls, *, source: str, note: str) -> "ExposureFact":
        return cls(None, "unknown", source, note)

    @classmethod
    def unsupported(cls, *, source: str, note: str) -> "ExposureFact":
        return cls(None, "unsupported", source, note)


@dataclass(frozen=True)
class MCPExposure:
    """Exposure policy for one configured MCP/provider server."""

    server_id: str
    configured: ExposureFact
    defer_policy: ExposureFact
    tool_count: ExposureFact


@dataclass(frozen=True)
class RuntimeExposureCapabilities:
    """Runtime facts needed to interpret configured versus loaded tools."""

    host: str
    runtime_version: str | None = None
    model: str | None = None
    tool_search_supported: ExposureFact = ExposureFact.unknown(
        source="not_provided", note="Tool-search support was not reported."
    )
    tool_search_enabled: ExposureFact = ExposureFact.unknown(
        source="not_provided", note="Tool-search activation was not reported."
    )
    activation_threshold: ExposureFact = ExposureFact.unknown(
        source="not_provided", note="The runtime activation threshold was not reported."
    )
    builtins_always_loaded: ExposureFact = ExposureFact.unknown(
        source="not_provided", note="Built-in loading behavior was not reported."
    )
    mcp_servers: tuple[MCPExposure, ...] = ()
    custom_agent_behavior: Mapping[str, ExposureFact] = field(default_factory=dict)
    caching: Mapping[str, ExposureFact] = field(default_factory=dict)
    observability: Mapping[str, ExposureFact] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.host:
            raise ValueError("Runtime exposure host must be non-empty.")

    @property
    def dynamic_retrieval_supported(self) -> bool | None:
        fact = self.tool_search_supported
        if fact.status in {"known", "inferred"}:
            return fact.value if isinstance(fact.value, bool) else None
        return False if fact.status == "unsupported" else None

    def to_record(self) -> dict[str, Any]:
        """Serialize facts while preserving their evidence status."""
        return asdict(self)
