# Replay/A-B harness

The replay harness evaluates an architecture manifest with any number of architectures and agents. `pruned_flat_baseline` remains the benchmark and must retain the frozen dependency-closed flat tool surface.

The harness does not learn routes, infer exposure, or search for partitions. The manifest and replay bundle provide explicit architecture membership and explicit per-architecture activation paths.

## Architecture manifest

Use `architecture_manifest.example.json` as the schema example. Each architecture declares:

- `architecture_id`;
- `parent_tools`;
- `agents`, mapping arbitrary agent IDs to arbitrary tool lists.

`agent_count` is the total number of actual agents. Peer architectures have one
actual agent per `agents` entry and no implicit parent. A
`coordinator_specialists` architecture counts the coordinator represented by
`parent_tools` plus its specialist entries; this is the only remaining
representation mismatch. Flat baselines always have one actual agent.

The manifest also declares `baseline_architecture_id` and the historical tool-capability set. The parser rejects a drifted `pruned_flat_baseline` surface.

## Activation paths and measurements

Each task may provide an `activation_paths` object keyed by architecture ID. A path is ordered and may contain zero, one, or multiple agent IDs. This is an explicit replay route, not a routing policy.

Each recorded observation reports the executor's actual `agent_activation_path`, plus:

- task success and observed replay capability coverage;
- tool-call, routing, missed, and unnecessary activation failures;
- input and tool-definition/context tokens;
- explicit `delegation_tokens` and `inter_agent_communication_tokens`;
- turns and wall-clock time.

Historical tool capability coverage is calculated from the manifest's available tool surfaces. Observed replay capability coverage is calculated from the executor observations. They are reported separately and are not interchangeable.

## Candidate success gate

A candidate passes only when all three strict conditions hold:

- historical tool-capability coverage is exactly 100%;
- mean task quality is at least the `pruned_flat_baseline` result;
- total tool-definition/context tokens are strictly lower than `pruned_flat_baseline`.

The harness also reports agent activations, inter-agent handoffs, delegation tokens, communication tokens, total orchestration tokens, and all prior operational metrics.

## Run

Run the normal optimizer first. It writes `agent_tool_analysis/architecture_manifest.json`. Then run `replay_architectures.py` with that manifest and a real `--replay-input`; the CLI verifies that the benchmark report's retained baseline tools match the frozen manifest baseline before comparing candidates.

The example observations are synthetic schema placeholders only and are not quality or architecture evidence. Supply a real replay bundle captured by an external executor before treating results as empirical.

## Optional advanced offline replay

The normal optimizer does not discover or execute replay bundles. To request
advanced validation, supply both `--offline-replay-input` and an explicit
`--offline-replay-candidate` selected from the architecture options. Execution
is deliberately limited to recorded observations. The bundle metadata must
explicitly contain:

- `mode: "recorded_observations"`;
- `executor: "recorded_observations"`;
- `deterministic: true`;
- `side_effect_free: true`;
- an exact `architecture_manifest` equal to the optimizer's generated manifest.

The bundle must contain complete, ordered observations for every task and every
manifest architecture, and the explicitly selected option must name either a
reported Pareto finalist or an explicitly provisional manifest entry. The
frozen `pruned_flat_baseline` is always evaluated beside the candidate. A
passing comparison is reported as `replay_validated`, while a failed strict
gate is reported as `replay_rejected`; neither means production superiority.
Missing, malformed, or unsafe evidence is reported as not run.

The optimizer never launches a live model, shell, network/API action, external
write, or live A/B experiment automatically. Those require explicit user
approval and a separate controlled executor.

## Paired observation capture

Use `capture_replay_observations.py` when a real local adapter is available.
The adapter is a Python module exposing `execute(task, architecture,
activation_path)` and returning a complete `ReplayObservation` for each task.
The wrapper runs every task once under `pruned_flat_baseline` and once under
the selected provisional candidate, preserving the returned success, quality,
capability, routing, activation, token, turn, and latency fields. It writes a
paired bundle containing only those observations and task IDs.

The CLI also writes a paired manifest containing only the frozen baseline and
selected candidate. Pass that paired manifest, the analysis report containing
the matching baseline tools, and the captured bundle to
`replay_architectures.py` for the existing strict comparison. This keeps
paired capture narrow without requiring observations for unrelated candidates.

Captured bundles are marked `captured_observations`, `synthetic: false`, and
not deterministic/side-effect-free by default. That is intentional: the
capture adapter may execute real work. Run the explicit replay CLI against the
captured bundle after reviewing its task and executor provenance; the normal
optimizer will not silently auto-run it.
