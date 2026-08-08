# Runtime-aware metric contract (v0.3)

`runtime_metrics.py` is the host-neutral evidence contract for controlled
measurements and recorded replay. It is an adapter boundary: existing replay
and measurement inputs remain compatible, while reports can use one vocabulary
without pretending that missing fields were measured.

## Required dimensions

Every result keeps these dimensions separate:

| Dimension | Required fields | Rule |
| --- | --- | --- |
| Definition loading | configured, loaded, deferred, selected definitions | Configured is what the architecture permits; loaded is what the host actually supplied; deferred is retrievable but not loaded. Do not infer loaded definitions from calls. |
| Token accounting | total input, cached input, uncached input, billed input, output | Cached and uncached are distinct. Uncached input is derived only when total and cached input are both reported. Billed input is provider-reported billing input, not a synonym for uncached input. |
| Context occupancy | tool/schema, task/context, total | Schema occupancy must not be folded into task/context occupancy. Unknown splits remain unknown. |
| Selection | selected count, selection failures, routing failures, missed and unnecessary activations, ambiguity | Selection quality describes choosing or activating capabilities. It does not include delegation or message cost. |
| Coordination | delegation tokens, inter-agent communication tokens, activations, handoffs, turns, latency | Coordination is reported separately and may be compared with selection outcomes, but is never silently added to them. |
| Outcome and coverage | success, quality, observed replay coverage, historical coverage | Historical manifest coverage and observed replay coverage are different evidence. |

## Evidence rules

Each value is a `Metric` with `MetricEvidence` metadata:

- `measured`: directly reported by the controlled host or replay executor;
- `estimated`: calculated from an explicit estimation method and inputs;
- `inferred`: derived from evidence but not directly reported (for example,
  uncached input = total input − cached input);
- `counterfactual`: projected for an architecture or exposure that did not run;
- `unavailable`: the host did not report the value;
- `unresolved`: the value is expected but its source or interpretation is not
  established.

Evidence includes source, method, unit, and optional runtime/model identity.
`None` is permitted only with `unavailable` or `unresolved` evidence. Consumers
must not turn unavailable values into zeroes, token estimates, monetary savings,
or production-quality claims.

## Adapter boundaries

- `from_surface_run()` maps `SurfaceRun` and marks host fields that it cannot
  observe as unavailable.
- `from_replay_observation()` maps `ReplayObservation` and keeps routing and
  coordination fields separate from tool selection. Replay executors may
  provide `configured_definitions`, `loaded_definitions`,
  `deferred_definitions`, and `selected_tools`; omitted fields stay unavailable
  and are never inferred from calls.
- `from_replay_aggregate()` serializes aggregate replay results with the same
  evidence vocabulary.
- Telemetry and definition registries remain historical/provenance adapters;
  they are not runtime measurements.
- Architecture manifests remain topology and membership inputs.
- Recommendation policy remains responsible for the strict baseline gate and
  for preserving a valid “do nothing” result.

## Runtime alternatives

`runtime_alternatives.py` constructs the host-neutral comparison table without
adding strategy identity to `RuntimeMetrics`. It always includes the current
runtime as `do_nothing`, followed by `prune_only`, `streamlined_static`,
`runtime_dynamic_retrieval`, `peer_specialists`, `coordinator_children`, and
`hybrid`. Each row records support as `true`, `false`, or `unknown`, explains
the support boundary, lists runtime requirements and assumptions, and carries
metric evidence status for loading, tokens, occupancy, selection,
coordination, and outcomes.

This layer evaluates alternatives but does not choose a winner. A missing
runtime measurement is reported as unavailable, not as zero or evidence that a
strategy is worse. Comparison deltas are emitted only for numeric values
available for both the candidate and the selected comparison baseline.

## Recommendation policy

`runtime_recommendation.py` consumes the alternatives table with a conservative
lexicographic policy. It rejects unsupported alternatives and alternatives that
lose required capability coverage, requires a material improvement before
justifying added complexity, and prefers measured or inferred evidence over
weaker modeled evidence. The default complexity preference is configurable and
is reported with the thresholds:

1. `do_nothing`
2. `prune_only`
3. `streamlined_static`
4. `runtime_dynamic_retrieval`
5. `peer_specialists`
6. `coordinator_children`
7. `hybrid`

The result separates `preferred_option`, `recommendation_strength`,
`runner_up_options`, rejection reasons, and policy thresholds. A materially
useful option supported only by counterfactual or incomplete evidence is
`provisional`; when no alternative clears the gate, the current runtime is
returned as the supported conservative baseline.

A comparison may claim a measured token or quality delta only when both sides
have compatible measured evidence. Estimates and counterfactuals remain
explicitly labelled in reports.
