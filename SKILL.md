---
name: agent-tool-analysis
description: Analyze coding-agent tool telemetry, remove dead tools, and recommend whether a simple specialist split beats one pruned agent.
---

# Agent Tool Analysis

Find actual tool usage, remove dead tools, compare a pruned flat agent with telemetry-grounded specialist candidates, and explain the simplest architecture worth considering.

This skill is advisory. Do not modify agent configuration, MCP/plugin settings, or IDE settings unless the user explicitly asks for an apply step.

## Normal workflow

Run the one public optimizer command from the skill's `scripts` directory:

```text
python -m optimize_agent_tools
```

The command discovers supported local telemetry using its defaults and writes:

- `agent_tool_analysis/agent_tool_analysis.json` — structured evidence and recommendation;
- `agent_tool_analysis/agent_tool_analysis.md` — the report to read first;
- `agent_tool_analysis/architecture_manifest.json` — candidate architectures for optional replay validation.

Read the Markdown report first. It is the compact human-facing recommendation
artifact. Do not load the full JSON report unless exact fields are needed; when
they are needed, read only `specialist_recommendation`, `candidate_agents`,
`clusters`, and the relevant `partition_search` entries. Read the architecture
manifest only for replay validation or to inspect a selected candidate's exact
parent/agent memberships.

Then classify the recommendation into exactly one strength level, with
offline replay validation recorded separately:

- **Proven recommendation:** empirical exposure/cost evidence is sufficient and
  an explicit replay or A/B quality gate has passed.
- **Provisional recommendation:** evidence is incomplete or quality is
  unvalidated, but structural and sensitivity evidence consistently favors one
  architecture. State the best current guess, confidence, reasons, and required
  validation. “Inconclusive” means do not claim the architecture is proven; it
  does not mean default to one agent forever.
- **No recommendation:** evidence is contradictory, too sparse, or does not
  directionally favor one architecture.

The normal command emits concrete `architecture_options` for the user. It
always includes the dependency-closed `pruned_flat_baseline`, and adds the
strongest concrete empirical finalist(s) or provisional specialist hypothesis
when those are coherent. When evidence is inconclusive, present the top two
or three options with their tool memberships, shared tools, semantic role
hypotheses, tradeoffs, and confidence; do not silently choose one.

Offline replay is optional advanced validation, not part of the normal happy
path. It runs only when the user supplies both `--offline-replay-input` and an
explicit `--offline-replay-candidate`. The bundle must explicitly declare
`mode: recorded_observations`, `executor: recorded_observations`, deterministic
execution, side-effect-free behavior, an exact architecture-manifest match,
complete tasks, and complete observations for the frozen baseline and selected
option. A passing bundle records `replay_validated`; a failing bundle records
`replay_rejected`. Live model calls, shell commands, network/API actions,
external writes, and live A/B experiments are never launched automatically.

Then follow the matching evidence branch:

- **Incomplete evidence:** if `specialist_recommendation.pareto_candidate_ids`
  is empty, state that there are no cost-complete empirical Pareto candidates
  under `observed_only`. If structural and sensitivity signals consistently
  favor one architecture, give a provisional best guess rather than refusing
  direction; otherwise give no recommendation. Do not call this a universal
  “no Pareto” result or infer exposure from calls. Use the controlled
  measurement layer when a decision needs missing schema, token, routing,
  latency, or quality evidence.
- **Complete evidence:** if cost coverage and exposure evidence are sufficient,
  compare the pruned flat baseline with every reported cost-complete empirical
  Pareto candidate. For each candidate, turn its anonymous tool membership into
  a **provisional** specialist name, one-sentence responsibility, and routing
  rule. Base the explanation on tool families, shared parent tools, session
  coverage, cross-agent frequency, and measured coordination costs. Mark names,
  responsibilities, and routes as semantic hypotheses rather than measured
  facts; retain multiple candidates when the trade-offs are genuinely Pareto.

In either branch, explain what is retained, removed, grouped, or left on the
parent, and stop after the advisory options. Do not generate, install, apply,
or silently select an agent configuration. Replay or a controlled runtime
experiment is required before claiming quality preservation or production
superiority. A provisional two-agent result should be phrased as “two agents
are the strongest current hypothesis,” not “the optimizer proved two agents
are best.”

When that provisional branch is selected, the normal artifact also emits a
`provisional_two_specialists` manifest entry marked `provisional` and
`directional_only`; it is separate from `pareto_candidate_ids` but replayable.
The normal report presents it beside the pruned flat option and leaves the
choice to the user. If the user later chooses validation, use the paired
capture runner to execute the frozen baseline and that candidate under matched
tasks, record the harness observation fields, and then pass the captured bundle
plus its paired manifest to the existing replay evaluator.

## Decision rule

The dependency-closed, dead-tool-pruned flat agent is the baseline to beat. Separate directly observed exposure, historical calls, inferred exposure, and unresolved exposure; missing evidence is not evidence of absence.

Specialists are worth considering only when their context savings plausibly exceed delegation and communication overhead without losing historically required capabilities. Prefer a simpler split over a larger one when the benefit is similar. A pruned flat agent is a valid recommendation.

## Escape hatches

Use these only when the normal workflow needs help:

- **Discovery repair:** use `inspect_codex_telemetry.py` to inspect supported telemetry structure when automatic discovery fails. Keep inspection structural and privacy-preserving; do not read prompts, tool arguments, command output, source code, or secrets merely to locate telemetry.
- **Empirical validation:** when the user wants quality, routing, or token validation, explicitly select an architecture option and provide an exact recorded-observation bundle to the normal command or use `replay_architectures.py` with `architecture_manifest.json`. Replay is advanced opt-in; live A/B remains explicit opt-in. Its strict frozen-baseline check still applies. Do not read the manifest during ordinary interpretation unless exact memberships are needed.
- **Controlled surface measurement:** when historical schema exposure is incomplete, use `MEASUREMENT.md`, `measurement_input.example.json`, and `measure_tool_surfaces.py` to compare two externally captured, otherwise-identical runs. This records evidence; it does not adopt dynamic retrieval or change partition search.

## Evidence and privacy

Use tool names, provider names, session counts, call order, definition metadata, and exposure indicators. Avoid reproducing user content, prompts, arguments, outputs, source code, credentials, or tokens.

Do not claim production superiority from telemetry alone. Replay or another controlled quality experiment is required before applying a specialist architecture.
