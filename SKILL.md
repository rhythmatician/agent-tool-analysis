---
name: agent-tool-analysis
description: Analyze coding-agent tool telemetry, remove dead tools, and recommend whether simple peer agents beat one pruned agent.
---

# Agent Tool Analysis

Find actual tool usage, remove dead tools, compare a pruned flat agent with telemetry-grounded peer architectures, and explain the simplest architecture worth considering.

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
  strongest concrete empirical finalist(s) or provisional peer-agent hypothesis
when those are coherent.

Runtime comparisons use the host-neutral contract in `RUNTIME_METRICS.md`.
Keep configured versus loaded definitions, cached versus uncached versus billed
input, schema versus task/context occupancy, selection quality, and coordination
overhead separate. Preserve evidence status and retain the pruned flat
baseline as a valid “do nothing” recommendation when no supported benefit is
shown.

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
  for each actual agent.

Create the destination directory when its parent workspace/profile is known
and the destination is otherwise unambiguous. If the active host is unknown,
more than one host is genuinely plausible, the requested format is unsupported
or ambiguous, or the destination cannot be resolved, ask one concise question:

> Which host should I generate these agents for: Codex, GitHub Copilot, or something else?

Do not ask about replay at this point.

## HITL nucleus design (permanent step - before specialist search)

After the first `python -m optimize_agent_tools` run and Markdown review, and before proposing specialists:

1. Show the optimizer's auto-detected shared nucleus (`global_tools` at `--global-usage-threshold 0.35`, mention `0.60` if different) and its collapsed families (canonical `read` `copilot_readFile+read_file 0.93`, `findText 0.79`, `findFiles 0.60`, `edit 1.0`, `exec 0.88`, `errors 0.45` etc), plus clustering hint: coherent specialists have `int>ext` and `marg>0` (e.g. Excel `int 0.56 ext 0.47`), while file/edit/search leaks `ext>int, marg<0`. Flag that `file/edit/search` + `terminal` + `errors` and coordination `agent/send_message/wait` are domain-invariant core that telemetry splits across aliases, so raw `usage_rate` under-reports them; do not leave them as specialist exclusives.
2. Propose the corrected nucleus (typically 16-22 tools: core 7 + `read_file/grep_search/file_search/list_dir` + `copilot_applyPatch/createFile/multiReplaceString/getErrors` + `get_errors/get_changed_files/get_terminal_output` + `agent/send_message/wait`) and ask the user to confirm/edit it: what else should be shared so no specialist must delegate for core work? Note over-sharing closes `flat vs max_peer` gap, under-sharing forces delegation on every file operation - invite judgement on that trade. Example: "I'll put file/edit/search, terminal, errors in the shared nucleus so neither peer delegates for core. OK, or adjust?"
3. Once approved, re-materialize `provisional_peer.json` / `architecture_manifest.provisional.json` with that nucleus duplicated on every peer, then move to the specialist question below. Record the approved nucleus and its rationale (collapsed urs, `ext>int` evidence) in the provisional's `assumptions.nucleus_source`.

Then, *given the nucleus and proximal clustering around the nucleus, which specialist agents would be good?* Validate against expected splits (e.g. in this user's history GitHub `fetch_webpage/github-pull-request_*` and Jupyter `copilot_createNewJupyterNotebook/editNotebook/runNotebookCell` should separate - GitLab notebooks vs GitHub - not co-locate).

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
- give every agent a useful provisional name and a real responsibility
  derived only from its actual tool membership, never a raw cluster or
  candidate ID;
- state a directional favorite when one exists, with confidence in ordinary
  language; and
- end with a direct choice such as `Reply “1” for ... or “2” for ...`.

For the common provisional two-agent result, use this shape:

1. **One streamlined agent** — the retained tools on one agent, best for
   simplicity and no delegation overhead.
2. **Two cooperating agents — recommended, provisional** — two coherent
  working sets, with explicitly duplicated shared tools and delegation called
  out separately. This means two actual agents, not a parent plus two
  peer agents.

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
  a **provisional** agent name, one-sentence responsibility, and routing
  rule. Base the explanation on tool families, explicitly shared peer tools, session
  coverage, cross-agent frequency, and measured coordination costs. Mark names,
  responsibilities, and routes as semantic hypotheses rather than measured
  facts; retain multiple candidates when the trade-offs are genuinely Pareto.

In either branch, explain what is retained, removed, grouped, or shared, and
stop after the advisory options until the user chooses one. A provisional
two-agent result should be phrased as “two agents are the strongest current
hypothesis,” not “the optimizer proved two agents are best.” Do not claim
production superiority without validation.

## Explicit architecture-choice branch

When the user replies with an option number (or clearly names an option), that
choice authorizes creation of new agent-definition files for the selected
option. Do not send them to replay first. Enter the generation branch:

1. Load the selected option from the architecture manifest and inspect its
  actual topology, agent count, exclusive, shared, and control-plane
  membership.
2. Detect the active host, resolve its supported agent format and default
  destination, and apply the host-targeting rules above.
3. Infer each working set's semantic responsibility from the tool families and
  metadata; replace anonymous IDs with useful names and concise routing
  descriptions. Treat these names and routes as hypotheses and flag any
  ambiguity. Names must be derived only from the selected membership; do not
  force a broader responsibility than the tools support.
4. Write the proposed agent names, routing instructions, and host-specific
  agent definitions for the selected architecture only after validating host
  realization. Compare the canonical required and excluded capabilities with
  the host-specific selectors: every required capability needs exact verified
  coverage, and excluded capabilities must not be reintroduced where the host
  supports restriction. Generic aliases such as `execute`, `read`, `edit`,
  `search`, or `agent` do not prove coverage of telemetry capabilities such as
  `github.fetch_pr`. A wildcard or omitted `tools` setting is acceptable only
  when the host's available-tool inventory and boundary behavior are verified.
  If this check is incomplete, do not create the file and do not report
  “Created”; report materialization as incomplete with the missing or
  reintroduced capabilities instead.
5. Ask for confirmation instead of creating files only if an existing file
  would be overwritten, existing agent/MCP/plugin/IDE configuration would be
  modified, the destination is ambiguous, or the host-specific agent format
  cannot be determined safely.

For option 1, generate one streamlined definition with the retained tools. For
a peer option, `agent_count` is the exact number of actual definitions to
create. Shared tools are duplicated capabilities on each peer, not tools on an
implicit parent, and no parent definition is created. Do not reuse `cluster_01`,
`cluster_03`, or similar implementation identifiers as user-facing names.

When that provisional branch is selected, use its manifest membership to create
the definitions; do not treat provisional status as a blocker. If the user
later asks for validation, use the replay workflow in `REPLAY.md`.

## Prompt validation (permanent step — after generating `.agent.md` files)

For every generated Copilot `.agent.md` file, run the Chat Customizations
Evaluations analyzer and iterate until clean:

For programmatic consumption, the companion extension in
`vscode-prompt-validator/` exports the current diagnostic snapshot through
`vscode.languages.getDiagnostics` as the versioned JSON contract in
[`docs/prompt-validator-diagnostics.schema.json`](docs/prompt-validator-diagnostics.schema.json).
See [`docs/prompt-validator-protocol.md`](docs/prompt-validator-protocol.md)
for the producer workflow and freshness rules. The JSON bridge is a transport
for editor diagnostics; it does not make the internal `promptValidator`
service public and it must not treat a stale snapshot as a clean validation.

1. Build and enable the companion extension before expecting a structured
  export. From `vscode-prompt-validator/`, run `npm install` and `npm test`,
  then press `F5` in that folder to launch an Extension Development Host, or
  run `npm run package` and install the resulting VSIX in the target VS Code
  profile.
2. In the target workspace, save or otherwise revalidate the generated files,
  then run **Prompt Validator: Export Diagnostics as JSON**. This creates
  `.vscode/prompt-diagnostics.json`. The command exports a snapshot; its
  timestamp does not prove that validation just ran.
3. Run the VS Code command `chatCustomizationsEvaluations.analyzePrompt` with
   the file's absolute path as its argument. Repeat for each generated file.
4. Read the file's diagnostics from the Problems panel (via the error-reading
  tool), or consume a bridge export with
  `unknown_extension_references_from_json()` when structured output is
  available. Do not rely on a single read immediately after analysis; if a
  finding looks stale after an edit, verify with a file search before
  re-acting on it. The text path remains the portable fallback.
5. Fix actionable findings with focused edits. Common validator findings seen
   in practice, and how to resolve them:
   - **Ambiguous delegation boundary** — when the prompt lists shared core
     tools (file/terminal/errors) but says "delegate anything outside X," the
     model can't tell when to self-handle. Fix: scope the shared tools
     ("use shared workspace tools only in direct support of a <specialty>
     task") and define delegation by *task goal*, not tool usage ("delegate
     when the task requires code refactoring or feature implementation not
     directly tied to <specialty>").
   - **Coverage gap / no failure handling** — add concrete failure guidance
     ("if the action fails, capture a screenshot and terminal output, then
     report the error before retrying or delegating").
   - **Duplicate tools with different naming conventions** — resolve each
     selector against the active host registry and keep only the exact
     verified form. Do not retain telemetry IDs or stale aliases merely to
     preserve historical spelling.
   - **Self-doubting provenance footer** — never write "provisional /
     semantic hypothesis / not measured facts" into the operational prompt.
     Keep that rationale in `provisional_peer.json` or a separate metadata
     file; operational prompts must be assertive.
4. Re-run the analyzer after each fix pass (at most one repair pass per the
   host-realization rule; more rounds indicate a structural problem, not a
   wording problem).
5. Report each file as validated-clean or list remaining findings. Do not
   claim the agents are ready until every file has no diagnostics.

**Selector ground truth (verified against validator source):**
`promptValidator.unknownExtensionOrMcpServerReference` on nearly every entry
means the tool list was written in telemetry IDs, not host selectors. The
validator checks `languageModelToolsService.getFullReferenceNames()`
(`workbench.desktop.main.js`). Valid selector forms, verified by reading that
source and iterating against the live validator:

1. **VS Code core toolsets** — namespaced `set/tool` names found as literals
   in the workbench bundle: `read/readFile`, `read/getNotebookSummary`,
   `search/fileSearch`, `search/textSearch`, `edit/editFiles`,
   `edit/createFile`, `edit/createDirectory`, `edit/createJupyterNotebook`,
   `edit/editNotebook`. Deprecated short names produce
   `Tool or toolset 'x' has been renamed, use 'u/x' instead` diagnostics —
   always apply the suggested rename.
2. **MCP servers** — server wildcards: `github/*`, `playwright/*`
   (aliases in `githubMCPServerAliases`/`playwrightMCPServerAliases`). Do NOT
   enumerate individual `mcp_github_*` tools — the wildcard covers them.
3. **Extension-registered tools** — bare keys as they appear in the
   copilot-chat registry
   (`%APPDATA%/Code/User/globalStorage/github.copilot-chat/toolEmbeddings.json`),
   e.g. `configure_python_environment`, `install_python_packages`,
   `notebook_install_packages`, `manage_todo_list`.

Invalid on this host: telemetry tool ids (`copilot_readFile` in session logs
is an id, not a selector), `copilot_*` package.json `name` fields (selector
is the sibling `toolReferenceName`, and even those short names like
`readFile` are deprecated in favor of the namespaced core set above), bare
codex names (`read_file`, `run_in_terminal`, `apply_patch`), and stale host
variants (`navigate_page`, `click_element`).

Resolution order: validator rename diagnostics (ground truth, apply
directly) → namespaced core set in workbench bundle → `github/*`/`playwright/*`
wildcards → `toolEmbeddings.json` keys for extension tools. When the editor
shows live squiggles the agent cannot see, ask the user for the exact
offending name and its suggested replacement — each one maps a family.

## Decision rule

Architecture semantics are explicit: `agent_count` counts actual agents;
`topology: peer` is the default partition topology; peer agents carry
per-agent `exclusive_tools` and duplicated `shared_tools`; and a coordinator
exists only when `topology: coordinator_specialists` is explicitly selected.
Control-plane tools such as `spawn_agent`, `send_message`, and `wait_agent`
are coordination capabilities, not workload affinity. Exclude them from
semantic clustering while retaining their telemetry for delegation and
communication cost estimates.

The dependency-closed, dead-tool-pruned flat agent is the baseline to beat. Separate directly observed exposure, historical calls, inferred exposure, and unresolved exposure; missing evidence is not evidence of absence.

Freshness is a separate signal from lifetime safety. Session evidence uses an
exponential decay weight (default half-life 30 days, configurable through the
CLI) for current NMF and partition-search signals. The lifetime-required set
always includes every historically called tool, regardless of its current
weight. Reports distinguish lifetime-required, current, currently-low-frequency,
and trial tools. A provider-backed tool first observed within the default 14-day
trial window is not treated as useless because its usage is sparse; its co-used
historical workloads are reported as trial evaluation opportunities.

Peer agents are worth considering only when duplicated shared context plus delegation and communication overhead plausibly beats the flat baseline without losing historically required capabilities. Prefer a simpler split over a larger one when the benefit is similar. A pruned flat agent is a valid recommendation.

Host tool selectors are a separate translation problem. Never emit telemetry
names directly into Copilot `tools:` entries. Resolve telemetry identity to a
canonical capability and then to a verified host selector from local tool
registry, MCP, extension, existing-agent, or provider evidence; never guess by
changing punctuation. After generation, inspect diagnostics for
`promptValidator.unknownExtensionReference`, attempt at most one evidence-based
repair pass, validate once more, and report unresolved selectors. If selectors
remain unresolved, do not claim that tool isolation is enforced.

## Escape hatches

Use these only when the normal workflow needs help:

- **Discovery repair:** use `inspect_codex_telemetry.py` to inspect supported telemetry structure when automatic discovery fails. Keep inspection structural and privacy-preserving; do not read prompts, tool arguments, command output, source code, or secrets merely to locate telemetry.
- **Empirical validation:** when the user asks for quality, routing, or token validation, follow `REPLAY.md` and use the recorded-observation workflow. Replay is advanced opt-in; live A/B remains explicit opt-in.
- **Controlled surface measurement:** when historical schema exposure is incomplete, use `MEASUREMENT.md`, `measurement_input.example.json`, and `measure_tool_surfaces.py` to compare two externally captured, otherwise-identical runs. This records evidence; it does not adopt dynamic retrieval or change partition search.

## Evidence and privacy

Use tool names, provider names, session counts, call order, definition metadata, and exposure indicators. Avoid reproducing user content, prompts, arguments, outputs, source code, credentials, or tokens.

Do not claim production superiority from telemetry alone. Validation is needed for that claim, not for creating a user-selected provisional architecture.
