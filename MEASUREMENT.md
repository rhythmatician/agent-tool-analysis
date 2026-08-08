# Controlled tool-surface measurement

This experiment layer compares two externally captured runs of the same task.
It does not change partition search, infer dynamic retrieval routes, or select a
production architecture.

## Controlled variables

Both runs must share the same:

- task and prompt identity;
- conversation-state identity;
- runtime and runtime version;
- model and model version;
- temperature and seed, where supported.

Only the `SurfaceCondition` should differ: the tools exposed immediately and
the tools deferred or retrieved later.

## Measurements

Each run records:

- actual provider input tokens;
- cached input tokens, when the provider reports them (`null` otherwise);
- serialized tool/schema payload characters and tokens, when inspectable;
- the schema measurement method;
- exposed and deferred tool names;
- selected tools, selection failures, and tool-call count;
- task success, quality score, and wall-clock latency;
- runtime/model identity and task identity.

The JSON report also includes a `runtime_metrics` record for each run. This is
the host-neutral v0.3 contract described in `RUNTIME_METRICS.md`: configured,
loaded, and deferred definitions; cached, uncached, and billed input; schema
versus task/context occupancy; selection; coordination; outcomes; and evidence
status for every value. Fields that this controlled surface cannot observe are
`unavailable`, not zero or an estimate.

The report stores only these structural measurements. It does not store prompts,
tool arguments, tool results, schemas, or model outputs.

## Run

Capture one JSON input bundle using the shape in
`measurement_input.example.json`, replacing the synthetic values with records
from the controlled runtime. Then run `measure_tool_surfaces.py` from the
`scripts` directory. The output contains per-condition records and
candidate-minus-baseline deltas.

Provider-reported token usage is preferred. If the runtime does not expose
serialized schemas, leave the schema fields `null` and record a different
measurement method rather than substituting a character estimate.

Run enough task pairs to compare distributions, not just one task. Keep the
same task order and randomization policy across conditions, and report failures
instead of dropping difficult tasks.