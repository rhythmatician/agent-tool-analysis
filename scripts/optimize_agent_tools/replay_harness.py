"""Replay/A-B harness for comparing arbitrary tool architectures."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Iterable, Mapping

BASELINE_ARCHITECTURE_ID = "pruned_flat_baseline"


def _string_set(values: Iterable[str], field_name: str) -> frozenset[str]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{field_name} must contain strings, not a scalar.")
    result = frozenset(values)
    if not all(isinstance(value, str) and value for value in result):
        raise ValueError(f"{field_name} must contain non-empty strings.")
    return result


@dataclass(frozen=True)
class BenchmarkArchitecture:
    """One flat, peer, or explicitly coordinator-based architecture."""

    architecture_id: str
    parent_tools: frozenset[str]
    agent_tools: Mapping[str, frozenset[str]] = field(default_factory=dict)
    topology: str = "coordinator_specialists"
    shared_tools: Mapping[str, frozenset[str]] = field(default_factory=dict)
    control_tools: frozenset[str] = frozenset()
    delegation_edges: Mapping[str, frozenset[str]] = field(default_factory=dict)
    declared_agent_count: int | None = None
    provisional: bool = False
    directional_only: bool = False
    assumptions: tuple[Any, ...] = ()
    provenance: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.architecture_id:
            raise ValueError("Architecture IDs must be non-empty.")
        if any(not agent_id for agent_id in self.agent_tools):
            raise ValueError("Agent IDs must be non-empty.")
        if self.topology not in {"flat", "peer", "coordinator_specialists"}:
            raise ValueError(f"Unsupported architecture topology: {self.topology}")
        if (
            self.declared_agent_count is not None
            and self.declared_agent_count != self.agent_count
        ):
            raise ValueError(
                "agent_count must equal the number of actual agents for the "
                f"{self.topology} topology."
            )
        if self.topology == "peer":
            if self.parent_tools:
                raise ValueError("Peer architectures cannot have parent-owned tools.")
            if not self.agent_tools:
                raise ValueError("Peer architectures must contain actual agents.")
            if set(self.shared_tools) != set(self.agent_tools):
                raise ValueError("Peer shared_tools must name every actual agent.")
            for agent_id, tools in self.agent_tools.items():
                if not self.shared_tools[agent_id] <= tools:
                    raise ValueError(
                        f"Peer agent {agent_id!r} is missing its shared tools."
                    )
            unknown_edges = set(self.delegation_edges) - set(self.agent_tools)
            if unknown_edges:
                raise ValueError("Delegation edges must use declared peer agents.")
            if any(
                set(targets) - set(self.agent_tools)
                for targets in self.delegation_edges.values()
            ):
                raise ValueError("Delegation edges must target declared peer agents.")

    @property
    def available_tools(self) -> frozenset[str]:
        return frozenset(self.parent_tools) | frozenset(
            tool for tools in self.agent_tools.values() for tool in tools
        )

    @property
    def agent_count(self) -> int:
        if self.topology == "flat":
            return 1
        if self.topology == "coordinator_specialists" and self.parent_tools:
            return len(self.agent_tools) + 1
        return len(self.agent_tools)

    def effective_tools(self, agent_id: str) -> frozenset[str]:
        """Return direct plus explicitly reachable delegated capabilities."""
        if agent_id not in self.agent_tools:
            return frozenset()
        reached = {agent_id}
        pending = [agent_id]
        while pending:
            current = pending.pop()
            for target in self.delegation_edges.get(current, frozenset()):
                if target not in reached:
                    reached.add(target)
                    pending.append(target)
        return frozenset(
            tool for owner in reached for tool in self.agent_tools[owner]
        ) | frozenset(self.parent_tools)

    def requested_activation_path(self, task: ReplayTask) -> tuple[str, ...]:
        """Return the task's explicit route for this architecture, if any."""
        return task.activation_paths.get(self.architecture_id, ())


@dataclass(frozen=True)
class ArchitectureManifest:
    """A complete benchmark and arbitrary candidate architecture manifest."""

    baseline_architecture_id: str
    historical_tool_capability_tools: frozenset[str]
    architectures: tuple[BenchmarkArchitecture, ...]
    search_provenance: Mapping[str, Any] = field(default_factory=dict)
    provisional_architecture_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.baseline_architecture_id != BASELINE_ARCHITECTURE_ID:
            raise ValueError("The manifest baseline must be pruned_flat_baseline.")
        architecture_ids = [
            architecture.architecture_id for architecture in self.architectures
        ]
        if len(architecture_ids) != len(set(architecture_ids)):
            raise ValueError("Architecture IDs must be unique.")
        if self.baseline_architecture_id not in architecture_ids:
            raise ValueError("The manifest baseline architecture must be present.")
        if not self.historical_tool_capability_tools:
            raise ValueError("Historical tool-capability tools must not be empty.")
        if self.baseline.agent_tools:
            raise ValueError("The manifest baseline must be flat.")
        if set(self.provisional_architecture_ids) - set(architecture_ids):
            raise ValueError("Provisional architectures must be present in the manifest.")

    @property
    def architecture_ids(self) -> tuple[str, ...]:
        return tuple(
            architecture.architecture_id for architecture in self.architectures
        )

    @property
    def baseline(self) -> BenchmarkArchitecture:
        return next(
            architecture
            for architecture in self.architectures
            if architecture.architecture_id == self.baseline_architecture_id
        )


def build_architecture_manifest(raw: Mapping[str, Any]) -> ArchitectureManifest:
    """Parse an architecture manifest without inferring or optimizing routes."""
    raw_architectures = raw.get("architectures")
    if not isinstance(raw_architectures, list):
        raise ValueError("Manifest architectures must be a list.")

    architectures = []
    for raw_architecture in raw_architectures:
        if not isinstance(raw_architecture, dict):
            raise ValueError("Each manifest architecture must be an object.")
        topology = str(raw_architecture.get("topology", "coordinator_specialists"))
        raw_agents = raw_architecture.get("agents", {})
        if not isinstance(raw_agents, dict):
            raise ValueError("Architecture agents must be an object.")
        agents: dict[str, frozenset[str]] = {}
        shared_tools: dict[str, frozenset[str]] = {}
        raw_shared = raw_architecture.get("shared_tools", {})
        for agent_id, raw_tools in raw_agents.items():
            agent_name = str(agent_id)
            if isinstance(raw_tools, dict):
                tools = _string_set(
                    raw_tools.get("tools", []), f"agents.{agent_id}.tools"
                )
                shared = _string_set(
                    raw_tools.get("shared_tools", []),
                    f"agents.{agent_id}.shared_tools",
                )
                if topology == "peer":
                    exclusive = _string_set(
                        raw_tools.get("exclusive_tools", []),
                        f"agents.{agent_id}.exclusive_tools",
                    )
                    tools = tools or (exclusive | shared)
                    if not shared and isinstance(raw_shared, dict):
                        shared = _string_set(
                            raw_shared.get(agent_name, []),
                            f"shared_tools.{agent_name}",
                        )
                    shared_tools[agent_name] = shared
            else:
                tools = _string_set(raw_tools, f"agents.{agent_id}")
            agents[agent_name] = tools
        architectures.append(
            BenchmarkArchitecture(
                architecture_id=str(raw_architecture["architecture_id"]),
                parent_tools=_string_set(
                    raw_architecture.get("parent_tools", []),
                    "parent_tools",
                ),
                agent_tools=agents,
                topology=topology,
                shared_tools=shared_tools,
                control_tools=_string_set(
                    raw_architecture.get("control_tools", []),
                    "control_tools",
                ),
                delegation_edges={
                    str(agent_id): _string_set(targets, f"delegation.{agent_id}")
                    for agent_id, targets in (
                        raw_architecture.get("delegation_edges")
                        or raw_architecture.get("delegation", {}).get("edges", {})
                    ).items()
                },
                declared_agent_count=(
                    int(raw_architecture["agent_count"])
                    if "agent_count" in raw_architecture
                    else None
                ),
                provisional=raw_architecture.get("provisional") is True,
                directional_only=raw_architecture.get("directional_only") is True,
                assumptions=tuple(raw_architecture.get("assumptions", ())),
                provenance=dict(raw_architecture.get("provenance", {})),
            )
        )

    raw_provenance = raw.get("search_provenance", {})
    if not isinstance(raw_provenance, Mapping):
        raise ValueError("Manifest search_provenance must be an object.")
    raw_provisional_ids = raw.get("provisional_architecture_ids", ())
    if not isinstance(raw_provisional_ids, (list, tuple)):
        raise ValueError("Manifest provisional_architecture_ids must be a list.")
    manifest = ArchitectureManifest(
        baseline_architecture_id=str(raw["baseline_architecture_id"]),
        historical_tool_capability_tools=_string_set(
            raw["historical_tool_capability_tools"],
            "historical_tool_capability_tools",
        ),
        architectures=tuple(architectures),
        search_provenance=dict(raw_provenance),
        provisional_architecture_ids=tuple(
            _string_set(raw_provisional_ids, "provisional_architecture_ids")
        ),
    )
    missing_baseline_tools = (
        manifest.historical_tool_capability_tools - manifest.baseline.available_tools
    )
    if missing_baseline_tools:
        raise ValueError(
            "The pruned_flat_baseline does not retain historical capabilities: "
            + ", ".join(sorted(missing_baseline_tools))
        )
    return manifest


def serialize_architecture_manifest(manifest: ArchitectureManifest) -> dict[str, Any]:
    """Return the canonical JSON contract shared by replay consumers."""
    architectures: list[dict[str, Any]] = []
    for architecture in manifest.architectures:
        is_baseline = (
            architecture.architecture_id == manifest.baseline_architecture_id
        )
        topology = "flat" if is_baseline else architecture.topology
        entry: dict[str, Any] = {
            "architecture_id": architecture.architecture_id,
            "topology": topology,
            "agent_count": 1 if is_baseline else architecture.agent_count,
            "agents": {
                agent_id: {
                    "tools": sorted(tools),
                    "shared_tools": sorted(
                        architecture.shared_tools.get(agent_id, frozenset())
                    ),
                    "exclusive_tools": sorted(
                        tools - architecture.shared_tools.get(agent_id, frozenset())
                    ),
                }
                for agent_id, tools in architecture.agent_tools.items()
            },
            "control_tools": sorted(architecture.control_tools),
        }
        if topology != "peer":
            entry["parent_tools"] = sorted(architecture.parent_tools)
        else:
            entry["shared_tools"] = sorted(
                set().union(*architecture.shared_tools.values())
                if architecture.shared_tools
                else set()
            )
            entry["delegation"] = {
                "enabled": bool(architecture.delegation_edges),
                "topology": " <-> ".join(sorted(architecture.agent_tools)),
                "edges": {
                    agent_id: sorted(targets)
                    for agent_id, targets in architecture.delegation_edges.items()
                },
            }
        if architecture.provisional:
            entry["provisional"] = True
        if architecture.directional_only:
            entry["directional_only"] = True
        if architecture.assumptions:
            entry["assumptions"] = list(architecture.assumptions)
        if architecture.provenance:
            entry["provenance"] = dict(architecture.provenance)
        architectures.append(entry)
    result: dict[str, Any] = {
        "baseline_architecture_id": manifest.baseline_architecture_id,
        "historical_tool_capability_tools": sorted(
            manifest.historical_tool_capability_tools
        ),
        "architectures": architectures,
    }
    if manifest.search_provenance:
        result["search_provenance"] = dict(manifest.search_provenance)
    if manifest.provisional_architecture_ids:
        result["provisional_architecture_ids"] = list(
            manifest.provisional_architecture_ids
        )
    return result


def select_architecture_manifest(
    manifest: ArchitectureManifest, architecture_ids: Iterable[str]
) -> ArchitectureManifest:
    """Select architectures while retaining the validated contract metadata."""
    selected_ids = tuple(dict.fromkeys(architecture_ids))
    unknown = set(selected_ids) - set(manifest.architecture_ids)
    if unknown:
        raise ValueError(
            "Unknown architecture IDs: " + ", ".join(sorted(unknown))
        )
    if manifest.baseline_architecture_id not in selected_ids:
        raise ValueError("The selected manifest must include the frozen baseline.")
    selected = tuple(
        architecture
        for architecture in manifest.architectures
        if architecture.architecture_id in selected_ids
    )
    return ArchitectureManifest(
        baseline_architecture_id=manifest.baseline_architecture_id,
        historical_tool_capability_tools=manifest.historical_tool_capability_tools,
        architectures=selected,
        search_provenance=manifest.search_provenance,
        provisional_architecture_ids=tuple(
            architecture_id
            for architecture_id in manifest.provisional_architecture_ids
            if architecture_id in selected_ids
        ),
    )


@dataclass(frozen=True)
class ReplayTask:
    """A replayable task with explicit per-architecture activation paths."""

    task_id: str
    activation_paths: Mapping[str, tuple[str, ...]] = field(default_factory=dict)


@dataclass(frozen=True)
class ReplayObservation:
    """One executor result with an ordered actual agent path and measured costs."""

    task_id: str
    task_success: bool
    observed_replay_capability_covered: bool
    quality_score: float
    agent_activation_path: tuple[str, ...] = ()
    tool_call_failures: int = 0
    routing_failure: bool = False
    missed_agent_activation: bool = False
    unnecessary_agent_activation: bool = False
    total_input_tokens: int = 0
    tool_definition_context_tokens: int = 0
    delegation_tokens: int = 0
    inter_agent_communication_tokens: int = 0
    turns: int = 0
    wall_clock_seconds: float = 0.0


@dataclass(frozen=True)
class ReplayAggregate:
    """Aggregated task, capability, and orchestration measurements."""

    task_count: int
    task_success_rate: float
    historical_tool_capability_coverage_rate: float
    observed_replay_capability_coverage_rate: float
    mean_quality_score: float
    tool_call_failures: int
    routing_failures: int
    missed_agent_activations: int
    unnecessary_agent_activations: int
    total_input_tokens: int
    tool_definition_context_tokens: int
    delegation_tokens: int
    inter_agent_communication_tokens: int
    turns: int
    agent_activations: int
    delegation_count: int
    inter_agent_handoffs: int
    wall_clock_seconds: float

    @property
    def total_tool_context_tokens(self) -> int:
        """Alias matching the benchmark's public metric name."""
        return self.tool_definition_context_tokens

    @property
    def orchestration_tokens(self) -> int:
        """Total explicit delegation and inter-agent communication cost."""
        return self.delegation_tokens + self.inter_agent_communication_tokens


@dataclass(frozen=True)
class ReplayResult:
    architecture_id: str
    observations: tuple[ReplayObservation, ...]
    aggregate: ReplayAggregate


@dataclass(frozen=True)
class BenchmarkComparison:
    baseline_architecture_id: str
    candidate_architecture_id: str
    passed: bool
    historical_capability_coverage_preserved: bool
    observed_replay_capability_coverage_preserved: bool
    task_quality_preserved: bool
    context_tokens_reduced: bool
    historical_capability_coverage_delta: float
    observed_replay_capability_coverage_delta: float
    quality_delta: float
    context_tokens_delta: int

    @property
    def quality_preserved(self) -> bool:
        return self.task_quality_preserved


ReplayExecutor = Callable[
    [ReplayTask, BenchmarkArchitecture, tuple[str, ...]], ReplayObservation
]


def historical_tool_capability_coverage(
    architecture: BenchmarkArchitecture,
    historical_tools: Iterable[str],
) -> float:
    """Measure manifest tool capability independently of replay outcomes."""
    required = frozenset(historical_tools)
    return (
        len(required & architecture.available_tools) / len(required)
        if required
        else 1.0
    )


def run_replay(
    tasks: Iterable[ReplayTask],
    architecture: BenchmarkArchitecture,
    executor: ReplayExecutor,
    *,
    historical_tools: Iterable[str],
) -> ReplayResult:
    """Replay tasks through explicit manifest paths using an external executor."""
    observations: list[ReplayObservation] = []
    routed_tasks: list[tuple[ReplayTask, tuple[str, ...]]] = []
    for task in tasks:
        activation_path = architecture.requested_activation_path(task)
        routed_tasks.append((task, activation_path))
        observation = executor(task, architecture, activation_path)
        if observation.task_id != task.task_id:
            raise ValueError(
                f"Executor returned {observation.task_id!r} for {task.task_id!r}."
            )
        observations.append(observation)

    aggregate = _aggregate(
        architecture,
        routed_tasks,
        observations,
        historical_tools=frozenset(historical_tools),
    )
    return ReplayResult(architecture.architecture_id, tuple(observations), aggregate)


def _aggregate(
    architecture: BenchmarkArchitecture,
    routed_tasks: list[tuple[ReplayTask, tuple[str, ...]]],
    observations: list[ReplayObservation],
    *,
    historical_tools: frozenset[str],
) -> ReplayAggregate:
    task_count = len(observations)
    actual_paths = [observation.agent_activation_path for observation in observations]
    routing_failures = 0
    missed = 0
    unnecessary = 0
    for (_task, expected_path), observation in zip(
        routed_tasks, observations, strict=True
    ):
        unsupported = set(expected_path) - set(architecture.agent_tools)
        routing_failures += int(observation.routing_failure or bool(unsupported))
        missed += int(
            observation.missed_agent_activation
            or (
                bool(expected_path)
                and observation.agent_activation_path != expected_path
            )
        )
        unnecessary += int(observation.unnecessary_agent_activation)
        unnecessary += sum(
            agent_id not in expected_path
            for agent_id in observation.agent_activation_path
        )

    return ReplayAggregate(
        task_count=task_count,
        task_success_rate=(
            sum(observation.task_success for observation in observations) / task_count
            if task_count
            else 0.0
        ),
        historical_tool_capability_coverage_rate=historical_tool_capability_coverage(
            architecture, historical_tools
        ),
        observed_replay_capability_coverage_rate=(
            sum(
                observation.observed_replay_capability_covered
                for observation in observations
            )
            / task_count
            if task_count
            else 0.0
        ),
        mean_quality_score=(
            sum(observation.quality_score for observation in observations) / task_count
            if task_count
            else 0.0
        ),
        tool_call_failures=sum(
            observation.tool_call_failures for observation in observations
        ),
        routing_failures=routing_failures,
        missed_agent_activations=missed,
        unnecessary_agent_activations=unnecessary,
        total_input_tokens=sum(
            observation.total_input_tokens for observation in observations
        ),
        tool_definition_context_tokens=sum(
            observation.tool_definition_context_tokens for observation in observations
        ),
        delegation_tokens=sum(
            observation.delegation_tokens for observation in observations
        ),
        inter_agent_communication_tokens=sum(
            observation.inter_agent_communication_tokens for observation in observations
        ),
        turns=sum(observation.turns for observation in observations),
        agent_activations=sum(len(path) for path in actual_paths),
        delegation_count=sum(max(len(path) - 1, 0) for path in actual_paths),
        inter_agent_handoffs=sum(max(len(path) - 1, 0) for path in actual_paths),
        wall_clock_seconds=sum(
            observation.wall_clock_seconds for observation in observations
        ),
    )


def compare_to_benchmark(
    baseline: ReplayResult, candidate: ReplayResult
) -> BenchmarkComparison:
    """Apply the strict historical-coverage, quality, and context gate."""
    historical_delta = (
        candidate.aggregate.historical_tool_capability_coverage_rate
        - baseline.aggregate.historical_tool_capability_coverage_rate
    )
    observed_delta = (
        candidate.aggregate.observed_replay_capability_coverage_rate
        - baseline.aggregate.observed_replay_capability_coverage_rate
    )
    quality_delta = (
        candidate.aggregate.mean_quality_score - baseline.aggregate.mean_quality_score
    )
    context_delta = (
        candidate.aggregate.total_tool_context_tokens
        - baseline.aggregate.total_tool_context_tokens
    )
    historical_preserved = (
        candidate.aggregate.historical_tool_capability_coverage_rate == 1.0
        and historical_delta >= 0
    )
    quality_preserved = quality_delta >= 0
    context_reduced = context_delta < 0
    return BenchmarkComparison(
        baseline_architecture_id=baseline.architecture_id,
        candidate_architecture_id=candidate.architecture_id,
        passed=historical_preserved and quality_preserved and context_reduced,
        historical_capability_coverage_preserved=historical_preserved,
        observed_replay_capability_coverage_preserved=observed_delta >= 0,
        task_quality_preserved=quality_preserved,
        context_tokens_reduced=context_reduced,
        historical_capability_coverage_delta=historical_delta,
        observed_replay_capability_coverage_delta=observed_delta,
        quality_delta=quality_delta,
        context_tokens_delta=context_delta,
    )


def replay_recorded_observations(
    tasks: Iterable[ReplayTask],
    architecture: BenchmarkArchitecture,
    observations: Iterable[ReplayObservation],
    *,
    historical_tools: Iterable[str],
) -> ReplayResult:
    """Aggregate observations captured by an external replay executor."""
    task_list = list(tasks)
    observation_list = list(observations)
    expected_ids = [task.task_id for task in task_list]
    actual_ids = [observation.task_id for observation in observation_list]
    if actual_ids != expected_ids:
        raise ValueError(
            "Recorded observation task IDs must match the task order exactly."
        )
    routed_tasks = [
        (task, architecture.requested_activation_path(task)) for task in task_list
    ]
    return ReplayResult(
        architecture.architecture_id,
        tuple(observation_list),
        _aggregate(
            architecture,
            routed_tasks,
            observation_list,
            historical_tools=frozenset(historical_tools),
        ),
    )
