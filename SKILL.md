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

Read the Markdown report first. It is the compact evidence artifact, not a
script for the normal chat response. Interpret it through the default
user-facing response policy below rather than copying its diagnostic headings,
field names, or anonymous IDs. Do not load the full JSON report unless exact
fields are needed; when they are needed, read only
`specialist_recommendation`, `candidate_agents`, `clusters`, and the relevant
`partition_search` entries. Read the architecture manifest only for replay
validation or after a user selects an option and its exact parent/agent
memberships are needed.

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
when those are coherent.

## Host targeting

Before generating definitions after an architecture choice, resolve the
current host and destination. Use this precedence:

1. An explicit host or scope supplied by the user.
2. Reliable current-runtime context (the host in which this skill was invoked).
3. Installed host markers only as a fallback; installation alone does not prove
   which host the user wants.

Record the result internally as:

- **Detected host:** `Codex`, `GitHub Copilot`, or `unknown`;
- **Agent format:** `known`, `unsupported`, or `ambiguous`; and
- **Destination:** a resolved path or `ask user`.

For the supported hosts in this environment:

- **Codex:** use standalone `.toml` custom-agent files. Prefer the current
  workspace's `.codex/agents/` directory for project-scoped definitions; use
  `~/.codex/agents/` only when the user explicitly requests user scope. Each
  file must contain Codex's required `name`, `description`, and
  `developer_instructions` fields. Codex custom-agent files do not provide a
  Copilot-style per-agent tool list, so preserve the inferred responsibility
  and tool membership in the instructions without claiming that the TOML
  enforces tool isolation.
- **GitHub Copilot:** use `.agent.md` files with YAML frontmatter. Prefer the
  current workspace's `.github/agents/` directory for project-scoped
  definitions; use `~/.copilot/agents/` only when the user explicitly requests
  user scope. Include a meaningful `description` and the supported tool list
  for each specialist.

Create the destination directory when its parent workspace/profile is known
and the destination is otherwise unambiguous. If the active host is unknown,
more than one host is genuinely plausible, the requested format is unsupported
or ambiguous, or the destination cannot be resolved, ask one concise question:

> Which host should I generate these agents for: Codex, GitHub Copilot, or something else?

Do not ask about replay at this point.

## Default user-facing response

The normal response is a decision aid, not an implementation or telemetry
diagnostic. Keep it short and lead with a heading such as `## Recommended
setup`. Translate the evidence into plain language and present concrete,
numbered options whenever more than one architecture is reasonable. The
default response should:

- state how many tools are retained and how many appear safe to exclude, using
  the option data rather than implying that anything has already been changed;
- describe each option's simplicity, delegation, context, and coordination
  trade-offs;
- give every specialist a useful provisional name and a real responsibility
  derived only from its actual tool membership, never a raw cluster or
  candidate ID;
- state a directional favorite when one exists, with confidence in ordinary
  language; and
- end with a direct choice such as `Reply “1” for ... or “2” for ...`.

For the common provisional two-specialist result, use this shape:

1. **One streamlined agent** — the retained tools on one agent, best for
   simplicity and no delegation overhead.
2. **Two specialists — recommended, provisional** — two coherent working sets,
   named by semantic responsibility, with shared tools called out separately.

Explain limited confidence without exposing implementation fields. For
example: “Some tool-definition and exposure measurements are incomplete, so
the two-agent advantage is directional rather than proven.” Do not include
`status`, `evidence_status`, `pareto_candidate_ids`, `search_strategy`,
`exposure_evidence_sufficient`, raw cluster IDs, replay state, generated
filenames, internal field names, or an internal checklist in the default
response. Put token savings and other exact measurements under an optional
`Analysis details` section only when they help the decision or the user asks
for technical evidence.

Say “Both options exclude the tools that appear safe to remove from the active
surface,” not “Prune dead tools now.” The skill is advisory and has not applied
anything.

Replay is optional advanced validation. Do not suggest it in the normal
architecture-choice flow unless the user asks about validation. If requested,
follow the recorded-observation protocol in `REPLAY.md`; never launch live
model calls, shell commands, network/API actions, external writes, or live A/B
experiments automatically.

Then follow the matching evidence branch:

- **Incomplete evidence:** if
  `specialist_recommendation.pareto_candidate_ids` is empty, use that fact
  internally to avoid calling the specialist result proven. If structural and
  sensitivity signals consistently favor one architecture, give a provisional
  best guess rather than refusing direction; otherwise give no recommendation.
  In the default response, explain the limitation in plain language rather than
  naming the empty field or measurement model. Do not call this a universal
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
parent, and stop after the advisory options until the user chooses one. A
provisional two-agent result should be phrased as “two agents are the strongest
current hypothesis,” not “the optimizer proved two agents are best.” Do not
claim production superiority without validation.

## Explicit architecture-choice branch

When the user replies with an option number (or clearly names an option), that
choice authorizes creation of new agent-definition files for the selected
option. Do not send them to replay first. Enter the generation branch:

1. Load the selected option from the architecture manifest and inspect its
  actual parent, specialist, and shared-tool membership.
2. Detect the active host, resolve its supported agent format and default
  destination, and apply the host-targeting rules above.
3. Infer each working set's semantic responsibility from the tool families and
  metadata; replace anonymous IDs with useful names and concise routing
  descriptions. Treat these names and routes as hypotheses and flag any
  ambiguity. Names must be derived only from the selected membership; do not
  force a broader responsibility than the tools support.
4. Write the proposed agent names, routing instructions, and host-specific
  agent definitions for the selected architecture and create them directly
  when the destinations are new and unambiguous. Report exactly what was
  created and where.
5. Ask for confirmation instead of creating files only if an existing file
  would be overwritten, existing agent/MCP/plugin/IDE configuration would be
  modified, the destination is ambiguous, or the host-specific agent format
  cannot be determined safely.

For option 1, generate one streamlined definition with the retained tools. For
option 2, keep the shared/orchestration tools on the host's primary parent and
generate exactly one definition file per specialist. Do not create a separate
parent definition unless the selected host explicitly requires one. Do not
reuse `cluster_01`, `cluster_03`, or similar implementation identifiers as
user-facing names.

When that provisional branch is selected, use its manifest membership to create
the definitions; do not treat provisional status as a blocker. If the user
later asks for validation, use the replay workflow in `REPLAY.md`.

## Decision rule

The dependency-closed, dead-tool-pruned flat agent is the baseline to beat. Separate directly observed exposure, historical calls, inferred exposure, and unresolved exposure; missing evidence is not evidence of absence.

Specialists are worth considering only when their context savings plausibly exceed delegation and communication overhead without losing historically required capabilities. Prefer a simpler split over a larger one when the benefit is similar. A pruned flat agent is a valid recommendation.

## Escape hatches

Use these only when the normal workflow needs help:

- **Discovery repair:** use `inspect_codex_telemetry.py` to inspect supported telemetry structure when automatic discovery fails. Keep inspection structural and privacy-preserving; do not read prompts, tool arguments, command output, source code, or secrets merely to locate telemetry.
- **Empirical validation:** when the user asks for quality, routing, or token validation, follow `REPLAY.md` and use the recorded-observation workflow. Replay is advanced opt-in; live A/B remains explicit opt-in.
- **Controlled surface measurement:** when historical schema exposure is incomplete, use `MEASUREMENT.md`, `measurement_input.example.json`, and `measure_tool_surfaces.py` to compare two externally captured, otherwise-identical runs. This records evidence; it does not adopt dynamic retrieval or change partition search.

## Evidence and privacy

Use tool names, provider names, session counts, call order, definition metadata, and exposure indicators. Avoid reproducing user content, prompts, arguments, outputs, source code, credentials, or tokens.

Do not claim production superiority from telemetry alone. Validation is needed for that claim, not for creating a user-selected provisional architecture.
