"""Host-neutral runtime evidence metrics.

This module is deliberately an adapter boundary.  Replay and controlled
measurement retain their existing wire contracts; callers can translate either
contract into :class:`RuntimeMetrics` without treating estimates as measured
runtime costs.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Literal

EvidenceStatus = Literal[
    "measured", "estimated", "inferred", "counterfactual", "unavailable", "unresolved"
]


@dataclass(frozen=True)
class MetricEvidence:
    """Provenance for one metric value, including why it is not available."""

    status: EvidenceStatus
    source: str
    method: str
    unit: str
    runtime: str | None = None
    runtime_version: str | None = None
    model: str | None = None
    model_version: str | None = None
    note: str | None = None

    def __post_init__(self) -> None:
        if self.status not in {
            "measured",
            "estimated",
            "inferred",
            "counterfactual",
            "unavailable",
            "unresolved",
        }:
            raise ValueError(f"Unsupported evidence status: {self.status!r}")
        for field_name in ("source", "method", "unit"):
            if not getattr(self, field_name):
                raise ValueError(f"{field_name} must be a non-empty string.")

    @classmethod
    def unavailable(cls, *, source: str, unit: str, note: str) -> "MetricEvidence":
        return cls("unavailable", source, "not_reported", unit, note=note)


@dataclass(frozen=True)
class Metric:
    """A value paired with evidence; ``None`` is valid only for unavailable data."""

    value: Any
    evidence: MetricEvidence

    def __post_init__(self) -> None:
        if self.value is None and self.evidence.status not in {
            "unavailable",
            "unresolved",
        }:
            raise ValueError("None values must be marked unavailable or unresolved.")


@dataclass(frozen=True)
class DefinitionLoading:
    configured: Metric
    loaded: Metric
    deferred: Metric
    selected: Metric


@dataclass(frozen=True)
class TokenAccounting:
    total_input: Metric
    cached_input: Metric
    uncached_input: Metric
    billed_input: Metric
    output: Metric


@dataclass(frozen=True)
class ContextOccupancy:
    tool_schema: Metric
    task_context: Metric
    total: Metric


@dataclass(frozen=True)
class SelectionMetrics:
    selected_tool_count: Metric
    selection_failures: Metric
    routing_failures: Metric
    missed_activations: Metric
    unnecessary_activations: Metric
    ambiguity: Metric


@dataclass(frozen=True)
class CoordinationMetrics:
    delegation_tokens: Metric
    inter_agent_communication_tokens: Metric
    activations: Metric
    handoffs: Metric
    turns: Metric
    latency_seconds: Metric


@dataclass(frozen=True)
class OutcomeMetrics:
    task_success: Metric
    quality: Metric
    observed_capability_coverage: Metric
    historical_capability_coverage: Metric


@dataclass(frozen=True)
class RuntimeMetrics:
    """Minimum host-neutral result contract for one run or aggregate."""

    definitions: DefinitionLoading
    tokens: TokenAccounting
    occupancy: ContextOccupancy
    selection: SelectionMetrics
    coordination: CoordinationMetrics
    outcome: OutcomeMetrics

    def to_record(self) -> dict[str, Any]:
        """Return a JSON-serializable record while preserving evidence metadata."""
        return _json_safe(asdict(self))


def _json_safe(value: Any) -> Any:
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    return value


def measured(
    value: Any, *, source: str, method: str, unit: str, **identity: str
) -> Metric:
    return Metric(value, MetricEvidence("measured", source, method, unit, **identity))


def inferred(value: Any, *, source: str, method: str, unit: str) -> Metric:
    return Metric(value, MetricEvidence("inferred", source, method, unit))


def unavailable(*, source: str, unit: str, note: str) -> Metric:
    return Metric(None, MetricEvidence.unavailable(source=source, unit=unit, note=note))


def from_surface_run(run: Any) -> RuntimeMetrics:
    """Adapt a ``measurement.SurfaceRun`` without importing that module."""
    identity = run.identity
    source = "controlled_measurement"
    schema = (
        measured(
            run.serialized_tool_payload_tokens,
            source=source,
            method=run.schema_measurement_method,
            unit="tokens",
            runtime=identity.runtime,
            runtime_version=identity.runtime_version,
            model=identity.model,
            model_version=identity.model_version,
        )
        if run.serialized_tool_payload_tokens is not None
        else unavailable(
            source=source,
            unit="tokens",
            note="Serialized tool payload was not inspectable.",
        )
    )
    cached = (
        measured(
            run.cached_input_tokens,
            source=source,
            method="provider_usage",
            unit="tokens",
        )
        if run.cached_input_tokens is not None
        else unavailable(
            source=source, unit="tokens", note="Provider did not report cached input."
        )
    )
    if (
        run.cached_input_tokens is not None
        and run.cached_input_tokens > run.actual_input_tokens
    ):
        raise ValueError("cached input cannot exceed total input")
    uncached = (
        inferred(
            run.actual_input_tokens - run.cached_input_tokens,
            source=source,
            method="derived_total_minus_cached",
            unit="tokens",
        )
        if run.cached_input_tokens is not None
        else unavailable(
            source=source,
            unit="tokens",
            note="Cannot separate uncached input without cached input.",
        )
    )
    return RuntimeMetrics(
        definitions=DefinitionLoading(
            configured=measured(
                tuple(sorted(run.condition.available_tools)),
                source=source,
                method="surface_condition",
                unit="tools",
            ),
            loaded=measured(
                tuple(sorted(run.condition.exposed_tools)),
                source=source,
                method="surface_condition",
                unit="tools",
            ),
            deferred=measured(
                tuple(sorted(run.condition.deferred_tools)),
                source=source,
                method="surface_condition",
                unit="tools",
            ),
            selected=measured(
                tuple(run.selected_tools),
                source=source,
                method="runtime_selection",
                unit="tools",
            ),
        ),
        tokens=TokenAccounting(
            total_input=measured(
                run.actual_input_tokens,
                source=source,
                method="provider_usage",
                unit="tokens",
            ),
            cached_input=cached,
            uncached_input=uncached,
            billed_input=unavailable(
                source=source,
                unit="tokens",
                note="Controlled measurement does not report billed input.",
            ),
            output=unavailable(
                source=source,
                unit="tokens",
                note="Controlled measurement does not report output tokens.",
            ),
        ),
        occupancy=ContextOccupancy(
            tool_schema=schema,
            task_context=unavailable(
                source=source,
                unit="tokens",
                note="Task/context occupancy is not separately reported.",
            ),
            total=unavailable(
                source=source,
                unit="tokens",
                note="Total context occupancy is not reported.",
            ),
        ),
        selection=SelectionMetrics(
            selected_tool_count=measured(
                len(run.selected_tools),
                source=source,
                method="runtime_selection",
                unit="tools",
            ),
            selection_failures=measured(
                run.tool_selection_failures,
                source=source,
                method="runtime_selection",
                unit="failures",
            ),
            routing_failures=unavailable(
                source=source,
                unit="failures",
                note="Controlled measurement has no agent routing.",
            ),
            missed_activations=unavailable(
                source=source,
                unit="activations",
                note="Controlled measurement has no agent activation route.",
            ),
            unnecessary_activations=unavailable(
                source=source,
                unit="activations",
                note="Controlled measurement has no agent activation route.",
            ),
            ambiguity=unavailable(
                source=source,
                unit="events",
                note="Selection ambiguity was not reported.",
            ),
        ),
        coordination=CoordinationMetrics(
            delegation_tokens=unavailable(
                source=source,
                unit="tokens",
                note="Controlled measurement has no delegation channel.",
            ),
            inter_agent_communication_tokens=unavailable(
                source=source,
                unit="tokens",
                note="Controlled measurement has no inter-agent channel.",
            ),
            activations=unavailable(
                source=source,
                unit="activations",
                note="Controlled measurement has no agent activation.",
            ),
            handoffs=unavailable(
                source=source,
                unit="handoffs",
                note="Controlled measurement has no agent handoffs.",
            ),
            turns=unavailable(
                source=source, unit="turns", note="Turn count was not recorded."
            ),
            latency_seconds=measured(
                run.latency_seconds,
                source=source,
                method="runtime_clock",
                unit="seconds",
            ),
        ),
        outcome=OutcomeMetrics(
            task_success=measured(
                run.task_success, source=source, method="task_result", unit="boolean"
            ),
            quality=measured(
                run.quality_score, source=source, method="quality_score", unit="score"
            ),
            observed_capability_coverage=unavailable(
                source=source,
                unit="ratio",
                note="Controlled measurement does not replay an architecture.",
            ),
            historical_capability_coverage=unavailable(
                source=source,
                unit="ratio",
                note="Historical capability coverage is not a surface metric.",
            ),
        ),
    )


def from_replay_observation(observation: Any) -> RuntimeMetrics:
    """Adapt a ``replay_harness.ReplayObservation`` into the shared contract."""
    source = "replay_observation"
    measured_tokens = lambda value, name: measured(
        value, source=source, method=name, unit="tokens"
    )
    tool_metric = lambda value, name: (
        measured(value, source=source, method=name, unit="tools")
        if value is not None
        else unavailable(
            source=source, unit="tools", note=f"Replay did not report {name}."
        )
    )
    return RuntimeMetrics(
        definitions=DefinitionLoading(
            configured=tool_metric(
                observation.configured_definitions, "configured definitions"
            ),
            loaded=tool_metric(observation.loaded_definitions, "loaded definitions"),
            deferred=tool_metric(
                observation.deferred_definitions, "deferred definitions"
            ),
            selected=tool_metric(observation.selected_tools, "selected tools"),
        ),
        tokens=TokenAccounting(
            total_input=measured_tokens(observation.total_input_tokens, "replay_input"),
            cached_input=measured_tokens(
                observation.cached_input_tokens, "replay_cached_input"
            )
            if observation.cached_input_tokens is not None
            else unavailable(
                source=source, unit="tokens", note="Replay did not report cached input."
            ),
            uncached_input=(
                inferred(
                    observation.total_input_tokens - observation.cached_input_tokens,
                    source=source,
                    method="derived_total_minus_cached",
                    unit="tokens",
                )
                if observation.cached_input_tokens is not None
                and observation.cached_input_tokens <= observation.total_input_tokens
                else unavailable(
                    source=source,
                    unit="tokens",
                    note="Replay cannot separate uncached input from the reported values.",
                )
            ),
            billed_input=measured_tokens(
                observation.billed_input_tokens, "replay_billed_input"
            )
            if observation.billed_input_tokens is not None
            else unavailable(
                source=source, unit="tokens", note="Replay did not report billed input."
            ),
            output=unavailable(
                source=source,
                unit="tokens",
                note="Replay observation does not report output tokens.",
            ),
        ),
        occupancy=ContextOccupancy(
            tool_schema=measured_tokens(
                observation.tool_definition_context_tokens,
                "replay_tool_definition_context",
            ),
            task_context=unavailable(
                source=source,
                unit="tokens",
                note="Replay does not split task/context occupancy.",
            ),
            total=measured_tokens(observation.total_input_tokens, "replay_total_input"),
        ),
        selection=SelectionMetrics(
            selected_tool_count=unavailable(
                source=source,
                unit="tools",
                note="Replay observation does not report selected tool names.",
            ),
            selection_failures=measured(
                observation.tool_selection_failures,
                source=source,
                method="replay_selection",
                unit="failures",
            ),
            routing_failures=measured(
                int(observation.routing_failure),
                source=source,
                method="replay_routing",
                unit="failures",
            ),
            missed_activations=measured(
                int(observation.missed_agent_activation),
                source=source,
                method="replay_activation",
                unit="activations",
            ),
            unnecessary_activations=measured(
                int(observation.unnecessary_agent_activation),
                source=source,
                method="replay_activation",
                unit="activations",
            ),
            ambiguity=unavailable(
                source=source,
                unit="events",
                note="Replay does not report selection ambiguity.",
            ),
        ),
        coordination=CoordinationMetrics(
            delegation_tokens=measured_tokens(
                observation.delegation_tokens, "replay_delegation"
            ),
            inter_agent_communication_tokens=measured_tokens(
                observation.inter_agent_communication_tokens, "replay_communication"
            ),
            activations=measured(
                len(observation.agent_activation_path),
                source=source,
                method="replay_activation",
                unit="activations",
            ),
            handoffs=measured(
                max(len(observation.agent_activation_path) - 1, 0),
                source=source,
                method="replay_activation_path",
                unit="handoffs",
            ),
            turns=measured(
                observation.turns, source=source, method="replay_turns", unit="turns"
            ),
            latency_seconds=measured(
                observation.wall_clock_seconds,
                source=source,
                method="replay_clock",
                unit="seconds",
            ),
        ),
        outcome=OutcomeMetrics(
            task_success=measured(
                observation.task_success,
                source=source,
                method="replay_result",
                unit="boolean",
            ),
            quality=measured(
                observation.quality_score,
                source=source,
                method="replay_quality",
                unit="score",
            ),
            observed_capability_coverage=measured(
                observation.observed_replay_capability_covered,
                source=source,
                method="replay_capability",
                unit="boolean",
            ),
            historical_capability_coverage=unavailable(
                source=source,
                unit="ratio",
                note="Historical coverage is an architecture aggregate, not an observation field.",
            ),
        ),
    )


def from_replay_aggregate(aggregate: Any) -> RuntimeMetrics:
    """Adapt a ``replay_harness.ReplayAggregate`` for report serialization."""
    source = "replay_aggregate"
    metric_tokens = lambda value, method: measured(
        value, source=source, method=method, unit="tokens"
    )
    return RuntimeMetrics(
        definitions=DefinitionLoading(
            configured=unavailable(
                source=source,
                unit="tools",
                note="Aggregate does not include configured definitions.",
            ),
            loaded=unavailable(
                source=source,
                unit="tools",
                note="Aggregate does not include loaded definitions.",
            ),
            deferred=unavailable(
                source=source,
                unit="tools",
                note="Aggregate does not include deferred definitions.",
            ),
            selected=unavailable(
                source=source,
                unit="tools",
                note="Aggregate does not include selected definition names.",
            ),
        ),
        tokens=TokenAccounting(
            total_input=metric_tokens(
                aggregate.total_input_tokens, "replay_total_input"
            ),
            cached_input=metric_tokens(
                aggregate.cached_input_tokens, "replay_cached_input"
            )
            if aggregate.cached_input_tokens is not None
            else unavailable(
                source=source,
                unit="tokens",
                note="Every replay observation did not report cached input.",
            ),
            uncached_input=(
                inferred(
                    aggregate.total_input_tokens - aggregate.cached_input_tokens,
                    source=source,
                    method="derived_total_minus_cached",
                    unit="tokens",
                )
                if aggregate.cached_input_tokens is not None
                and aggregate.cached_input_tokens <= aggregate.total_input_tokens
                else unavailable(
                    source=source,
                    unit="tokens",
                    note="Aggregate cannot separate uncached input from the reported values.",
                )
            ),
            billed_input=metric_tokens(
                aggregate.billed_input_tokens, "replay_billed_input"
            )
            if aggregate.billed_input_tokens is not None
            else unavailable(
                source=source,
                unit="tokens",
                note="Every replay observation did not report billed input.",
            ),
            output=unavailable(
                source=source,
                unit="tokens",
                note="Replay aggregate does not report output tokens.",
            ),
        ),
        occupancy=ContextOccupancy(
            tool_schema=metric_tokens(
                aggregate.tool_definition_context_tokens,
                "replay_tool_definition_context",
            ),
            task_context=unavailable(
                source=source,
                unit="tokens",
                note="Replay aggregate does not split task/context occupancy.",
            ),
            total=metric_tokens(aggregate.total_input_tokens, "replay_total_input"),
        ),
        selection=SelectionMetrics(
            selected_tool_count=unavailable(
                source=source,
                unit="tools",
                note="Replay aggregate does not report selected tool names.",
            ),
            selection_failures=measured(
                aggregate.tool_selection_failures,
                source=source,
                method="replay_selection",
                unit="failures",
            ),
            routing_failures=measured(
                aggregate.routing_failures,
                source=source,
                method="replay_routing",
                unit="failures",
            ),
            missed_activations=measured(
                aggregate.missed_agent_activations,
                source=source,
                method="replay_activation",
                unit="activations",
            ),
            unnecessary_activations=measured(
                aggregate.unnecessary_agent_activations,
                source=source,
                method="replay_activation",
                unit="activations",
            ),
            ambiguity=unavailable(
                source=source,
                unit="events",
                note="Replay aggregate does not report selection ambiguity.",
            ),
        ),
        coordination=CoordinationMetrics(
            delegation_tokens=metric_tokens(
                aggregate.delegation_tokens, "replay_delegation"
            ),
            inter_agent_communication_tokens=metric_tokens(
                aggregate.inter_agent_communication_tokens, "replay_communication"
            ),
            activations=measured(
                aggregate.agent_activations,
                source=source,
                method="replay_activation",
                unit="activations",
            ),
            handoffs=measured(
                aggregate.inter_agent_handoffs,
                source=source,
                method="replay_handoff",
                unit="handoffs",
            ),
            turns=measured(
                aggregate.turns, source=source, method="replay_turns", unit="turns"
            ),
            latency_seconds=measured(
                aggregate.wall_clock_seconds,
                source=source,
                method="replay_clock",
                unit="seconds",
            ),
        ),
        outcome=OutcomeMetrics(
            task_success=measured(
                aggregate.task_success_rate,
                source=source,
                method="replay_result",
                unit="ratio",
            ),
            quality=measured(
                aggregate.mean_quality_score,
                source=source,
                method="replay_quality",
                unit="score",
            ),
            observed_capability_coverage=measured(
                aggregate.observed_replay_capability_coverage_rate,
                source=source,
                method="replay_capability",
                unit="ratio",
            ),
            historical_capability_coverage=measured(
                aggregate.historical_tool_capability_coverage_rate,
                source=source,
                method="replay_capability",
                unit="ratio",
            ),
        ),
    )
