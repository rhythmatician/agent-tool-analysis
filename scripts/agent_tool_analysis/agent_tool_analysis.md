# Agent Tool Exposure Analysis

This report is advisory. No agent configuration was modified.

## Recommendation

**Remove the 21 directly observed, never-used exposed tools now.**

- Observed dead-tool savings: 5098.7 known tool-definition tokens/session
- Catalog tokens removed: 7205.0
- Catalog-only safe candidates: 3 tools; exposure benefit unmeasured
- Unresolved retained runtime-tool exposure: unknown

## Specialist recommendation

**Choose between the concrete architecture options below; the available evidence does not distinguish them strongly enough to choose for you.**

- Evidence status: `inconclusive_directional`
- Recommendation strength: `provisional`
- Best current direction: 2-agent architecture
- Confidence: `moderate-low`
- Best-guess architecture: `two_specialists`
- Why: strong structural separation across multiple candidate tool families; directional sensitivity favors specialist exposure; prefer the smallest multi-agent split because higher fragmentation is not validated; no empirical evidence yet that the split preserves or improves quality
- Required validation: optional advanced replay or A/B against the pruned flat baseline, including routing and quality
- Cost-complete empirical Pareto candidates under `observed_only`: none
- Partition search: bounded; the full partition space was not evaluated
- Replay: optional advanced validation; not requested
- Frontier kind: `empirical`; directional only: yes
- Exposure evidence sufficient: no
- Agent names, responsibilities, and routing are provisional semantic interpretations; this report does not apply configuration.

## Architecture options

The evidence does not choose among plausible options. Select one; replay/A-B is an optional advanced follow-up, not part of the normal workflow.

### Option 1 — Pruned single agent

- Architecture: `pruned_flat_baseline`
- Status: `baseline`
- Parent/shared tools: `exec`, `followup_task`, `github.add_comment_to_issue`, `github.add_issue_assignees`, `github.add_review_to_pr`, `github.create_issue`, `github.create_pull_request`, `github.fetch_file`, `github.fetch_issue`, `github.fetch_issue_comments`, `github.fetch_pr`, `github.fetch_pr_comments`, `github.fetch_pr_patch`, `github.get_pr_info`, `github.get_user_login`, `github.list_pr_changed_filenames`, `github.list_pull_request_review_threads`, `github.list_pull_request_reviews`, `github.reply_to_review_comment`, `github.resolve_review_thread`, `github.search_prs`, `github.update_issue`, `github.update_pull_request`, `interrupt_agent`, `list_agents`, `send_message`, `spawn_agent`, `wait`, `wait_agent`
- Why choose this: simplest architecture; no routing or handoff complexity; retains every historically used tool and known dependency
- Tradeoffs: keeps all retained tools on one parent surface; does not benefit from specialist context separation
- Confidence: high for pruning; quality of the unmodified architecture is not re-evaluated

### Option 2 — Two specialists

- Architecture: `provisional_two_specialists`
- Status: `provisional`
- Parent/shared tools: `exec`, `followup_task`, `github.create_pull_request`, `github.get_pr_info`, `github.resolve_review_thread`, `github.update_issue`, `github.update_pull_request`, `interrupt_agent`, `list_agents`, `send_message`, `spawn_agent`, `wait`, `wait_agent`
- Why choose this: strongest specialization hypothesis in the available evidence; likely lower context per agent; structural clustering supports the split; evidence is directional, not conclusive
- Tradeoffs: adds routing and handoff complexity; semantic roles and activation paths remain hypotheses
- Confidence: moderate-low
- Github specialist (`agent_01`): `github.add_comment_to_issue`, `github.add_review_to_pr`, `github.create_issue`, `github.fetch_file`, `github.fetch_issue`, `github.fetch_issue_comments`, `github.fetch_pr`, `github.fetch_pr_comments`, `github.fetch_pr_patch`, `github.list_pr_changed_filenames`, `github.reply_to_review_comment`, `github.search_prs`
  - Role: Github tool specialist
  - Description: Handles the tools in this inferred cluster: github.add_comment_to_issue, github.add_review_to_pr, github.create_issue, github.fetch_file, github.fetch_issue, github.fetch_issue_comments, github.fetch_pr, github.fetch_pr_comments, github.fetch_pr_patch, github.list_pr_changed_filenames, github.reply_to_review_comment, github.search_prs.
- Github specialist (`agent_02`): `github.add_issue_assignees`, `github.get_user_login`, `github.list_pull_request_review_threads`, `github.list_pull_request_reviews`
  - Role: Github tool specialist
  - Description: Handles the tools in this inferred cluster: github.add_issue_assignees, github.get_user_login, github.list_pull_request_review_threads, github.list_pull_request_reviews.

## Corpus

- Sessions analyzed: 143
- sessions_total: 143
- sessions_with_calls: 141
- sessions_with_direct_exposure: 117
- sessions_with_calls_and_exposure: 115
- sessions_with_calls_without_exposure: 26
- sessions_with_exposure_without_calls: 2
- Tool calls: 6370
- Unique tools: 53
- Sources: codex=143

## Definition resolution

| Observed tool | Calls | Sessions called | Resolved | Source | Estimated tokens | Evidence |
|---|---:|---:|---|---|---:|---|
| `exec` | 2767 | 140 | no | `unresolved` | unknown | unresolved |
| `followup_task` | 120 | 19 | no | `unresolved` | unknown | unresolved |
| `github.add_comment_to_issue` | 47 | 17 | no | `unresolved` | unknown | unresolved |
| `github.add_issue_assignees` | 11 | 11 | no | `unresolved` | unknown | unresolved |
| `github.add_review_to_pr` | 28 | 15 | no | `unresolved` | unknown | unresolved |
| `github.create_issue` | 68 | 17 | no | `unresolved` | unknown | unresolved |
| `github.create_pull_request` | 1 | 1 | no | `unresolved` | unknown | unresolved |
| `github.fetch_file` | 383 | 16 | no | `unresolved` | unknown | unresolved |
| `github.fetch_issue` | 185 | 33 | no | `unresolved` | unknown | unresolved |
| `github.fetch_issue_comments` | 51 | 32 | no | `unresolved` | unknown | unresolved |
| `github.fetch_pr` | 60 | 23 | no | `unresolved` | unknown | unresolved |
| `github.fetch_pr_comments` | 116 | 21 | no | `unresolved` | unknown | unresolved |
| `github.fetch_pr_patch` | 142 | 22 | no | `unresolved` | unknown | unresolved |
| `github.get_pr_info` | 1 | 1 | no | `unresolved` | unknown | unresolved |
| `github.get_user_login` | 11 | 11 | no | `unresolved` | unknown | unresolved |
| `github.list_pr_changed_filenames` | 64 | 14 | no | `unresolved` | unknown | unresolved |
| `github.list_pull_request_review_threads` | 12 | 6 | no | `unresolved` | unknown | unresolved |
| `github.list_pull_request_reviews` | 7 | 5 | no | `unresolved` | unknown | unresolved |
| `github.reply_to_review_comment` | 87 | 15 | no | `unresolved` | unknown | unresolved |
| `github.resolve_review_thread` | 6 | 2 | no | `unresolved` | unknown | unresolved |
| `github.search_prs` | 45 | 17 | no | `unresolved` | unknown | unresolved |
| `github.update_issue` | 1 | 1 | no | `unresolved` | unknown | unresolved |
| `github.update_pull_request` | 1 | 1 | no | `unresolved` | unknown | unresolved |
| `interrupt_agent` | 11 | 8 | no | `unresolved` | unknown | unresolved |
| `list_agents` | 86 | 22 | no | `unresolved` | unknown | unresolved |
| `send_message` | 329 | 84 | no | `unresolved` | unknown | unresolved |
| `spawn_agent` | 173 | 26 | no | `unresolved` | unknown | unresolved |
| `wait` | 299 | 48 | no | `unresolved` | unknown | unresolved |
| `wait_agent` | 1258 | 30 | no | `unresolved` | unknown | unresolved |

## Measurement completeness

- Frontier kind: `empirical`
- Directional only: yes
- Exposure evidence sufficient for an empirical frontier: no
- Call-bearing sessions without direct exposure: 26/141
- Retained baseline exact definition costs: 0/29
- Retained baseline cost status: `estimated`
- Calls are never used as exposure evidence; recovered chars/4 costs remain estimates.

## Definition discovery

- Explicit records: 0
- Telemetry records: 24
- Runtime roots scanned: C:\Users\JeffHall\.codex, C:\Users\JeffHall\.config\codex, C:\Users\JeffHall\AppData\Roaming\Codex
- Manifest files scanned: 286
- Manifest definitions found: 133

## Tool inventory

| Tool | Directly observed exposure | Used | P(use|exposed) | Calls | Def tokens | Waste/session | Boundary margin | Recommendation |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| `exec` | 0 | 140 | unavailable | 2767 | unknown | unavailable | 0.0 | global-candidate: ubiquitous |
| `send_message` | 0 | 84 | unavailable | 329 | unknown | unavailable | 0.1 | specialization-candidate: cost unknown |
| `wait` | 0 | 48 | unavailable | 299 | unknown | unavailable | 0.1 | specialization-candidate: cost unknown |
| `github.fetch_issue` | 0 | 33 | unavailable | 185 | unknown | unavailable | 0.1 | specialization-candidate: cost unknown |
| `github.fetch_issue_comments` | 0 | 32 | unavailable | 51 | unknown | unavailable | 0.0 | specialization-candidate: cost unknown |
| `wait_agent` | 0 | 30 | unavailable | 1258 | unknown | unavailable | 0.4 | specialization-candidate: cost unknown |
| `spawn_agent` | 0 | 26 | unavailable | 173 | unknown | unavailable | 0.4 | specialization-candidate: cost unknown |
| `github.fetch_pr` | 0 | 23 | unavailable | 60 | unknown | unavailable | 0.2 | specialization-candidate: cost unknown |
| `github.fetch_pr_patch` | 0 | 22 | unavailable | 142 | unknown | unavailable | 0.3 | specialization-candidate: cost unknown |
| `list_agents` | 0 | 22 | unavailable | 86 | unknown | unavailable | 0.4 | specialization-candidate: cost unknown |
| `github.fetch_pr_comments` | 0 | 21 | unavailable | 116 | unknown | unavailable | 0.3 | specialization-candidate: cost unknown |
| `followup_task` | 0 | 19 | unavailable | 120 | unknown | unavailable | 0.3 | specialization-candidate: cost unknown |
| `github.create_issue` | 0 | 17 | unavailable | 68 | unknown | unavailable | 0.3 | specialization-candidate: cost unknown |
| `github.add_comment_to_issue` | 0 | 17 | unavailable | 47 | unknown | unavailable | 0.3 | specialization-candidate: cost unknown |
| `github.search_prs` | 0 | 17 | unavailable | 45 | unknown | unavailable | 0.3 | specialization-candidate: cost unknown |
| `github.fetch_file` | 0 | 16 | unavailable | 383 | unknown | unavailable | 0.3 | specialization-candidate: cost unknown |
| `github.reply_to_review_comment` | 0 | 15 | unavailable | 87 | unknown | unavailable | 0.3 | specialization-candidate: cost unknown |
| `github.add_review_to_pr` | 0 | 15 | unavailable | 28 | unknown | unavailable | 0.3 | specialization-candidate: cost unknown |
| `github.list_pr_changed_filenames` | 0 | 14 | unavailable | 64 | unknown | unavailable | 0.3 | specialization-candidate: cost unknown |
| `github.add_issue_assignees` | 0 | 11 | unavailable | 11 | unknown | unavailable | 0.1 | specialization-candidate: cost unknown |
| `github.get_user_login` | 0 | 11 | unavailable | 11 | unknown | unavailable | 0.1 | specialization-candidate: cost unknown |
| `interrupt_agent` | 0 | 8 | unavailable | 11 | unknown | unavailable | 0.3 | specialization-candidate: cost unknown |
| `github.list_pull_request_review_threads` | 0 | 6 | unavailable | 12 | unknown | unavailable | 0.1 | specialization-candidate: cost unknown |
| `github.list_pull_request_reviews` | 0 | 5 | unavailable | 7 | unknown | unavailable | 0.2 | specialization-candidate: cost unknown |
| `github.resolve_review_thread` | 0 | 2 | unavailable | 6 | unknown | unavailable | unavailable | specialization-candidate: cost unknown |
| `github.create_pull_request` | 0 | 1 | unavailable | 1 | unknown | unavailable | unavailable | specialization-candidate: cost unknown |
| `github.get_pr_info` | 0 | 1 | unavailable | 1 | unknown | unavailable | unavailable | specialization-candidate: cost unknown |
| `github.update_issue` | 0 | 1 | unavailable | 1 | unknown | unavailable | unavailable | specialization-candidate: cost unknown |
| `github.update_pull_request` | 0 | 1 | unavailable | 1 | unknown | unavailable | unavailable | specialization-candidate: cost unknown |
| `automation_update` | 99 | 0 | 0.0% | 0 | 2162 | 1829.4 | unavailable | strong-specialization-candidate: expensive and non-ubiquitous |
| `capture_screen_context` | 1 | 0 | 0.0% | 0 | 89 | 0.8 | unavailable | specialization-candidate |
| `codex_app` | 0 | 0 | unavailable | 0 | 20 | 0.0 | unavailable | specialization-candidate |
| `create_thread` | 117 | 0 | 0.0% | 0 | 1207 | 1207.0 | unavailable | strong-specialization-candidate: expensive and non-ubiquitous |
| `end_realtime_voice_call` | 1 | 0 | 0.0% | 0 | 71 | 0.6 | unavailable | specialization-candidate |
| `fork_thread` | 117 | 0 | 0.0% | 0 | 264 | 264.0 | unavailable | specialization-candidate |
| `get_handoff_status` | 99 | 0 | 0.0% | 0 | 232 | 196.3 | unavailable | specialization-candidate |
| `handoff_thread` | 99 | 0 | 0.0% | 0 | 326 | 275.8 | unavailable | strong-specialization-candidate: expensive and non-ubiquitous |
| `list_projects` | 117 | 0 | 0.0% | 0 | 90 | 90.0 | unavailable | specialization-candidate |
| `list_threads` | 117 | 0 | 0.0% | 0 | 119 | 119.0 | unavailable | specialization-candidate |
| `load_workspace_dependencies` | 99 | 0 | 0.0% | 0 | 97 | 82.1 | unavailable | specialization-candidate |
| `navigate_to_codex_page` | 117 | 0 | 0.0% | 0 | 120 | 120.0 | unavailable | specialization-candidate |
| `open_in_codex` | 99 | 0 | 0.0% | 0 | 557 | 471.3 | unavailable | strong-specialization-candidate: expensive and non-ubiquitous |
| `plugin_management` | 0 | 0 | unavailable | 0 | 25 | 0.0 | unavailable | specialization-candidate |
| `read_thread` | 117 | 0 | 0.0% | 0 | 262 | 262.0 | unavailable | specialization-candidate |
| `read_thread_terminal` | 99 | 0 | 0.0% | 0 | 76 | 64.3 | unavailable | specialization-candidate |
| `ready-for-agent` | 0 | 0 | unavailable | 0 | 22 | 0.0 | unavailable | specialization-candidate |
| `send_message_to_thread` | 117 | 0 | 0.0% | 0 | 464 | 464.0 | unavailable | strong-specialization-candidate: expensive and non-ubiquitous |
| `send_realtime_voice_feedback` | 1 | 0 | 0.0% | 0 | 149 | 1.3 | unavailable | specialization-candidate |
| `set_thread_archived` | 117 | 0 | 0.0% | 0 | 141 | 141.0 | unavailable | specialization-candidate |
| `set_thread_pinned` | 117 | 0 | 0.0% | 0 | 129 | 129.0 | unavailable | specialization-candidate |
| `set_thread_title` | 117 | 0 | 0.0% | 0 | 134 | 134.0 | unavailable | specialization-candidate |
| `uninstall_plugin` | 99 | 0 | 0.0% | 0 | 141 | 119.3 | unavailable | specialization-candidate |
| `wait_threads` | 99 | 0 | 0.0% | 0 | 308 | 260.6 | unavailable | strong-specialization-candidate: expensive and non-ubiquitous |

## Candidate specialist agents

### cluster_01 (12 tools, 24.1% session coverage)

- Internal affinity: 0.707
- Known definition tokens isolated: 0
- Tools: `github.fetch_issue`, `github.fetch_issue_comments`, `github.fetch_pr`, `github.fetch_pr_patch`, `github.fetch_pr_comments`, `github.add_comment_to_issue`, `github.create_issue`, `github.search_prs`, `github.fetch_file`, `github.add_review_to_pr`, `github.reply_to_review_comment`, `github.list_pr_changed_filenames`

### cluster_02 (7 tools, 75.2% session coverage)

- Internal affinity: 0.470
- Known definition tokens isolated: 0
- Tools: `send_message`, `wait`, `wait_agent`, `spawn_agent`, `list_agents`, `followup_task`, `interrupt_agent`

### cluster_03 (4 tools, 8.5% session coverage)

- Internal affinity: 0.643
- Known definition tokens isolated: 0
- Tools: `github.add_issue_assignees`, `github.get_user_login`, `github.list_pull_request_review_threads`, `github.list_pull_request_reviews`

## Cluster boundaries

| Cluster | Internal affinity | Max external affinity | Mean boundary margin | Session coverage | Exclusive coverage | Overlapping coverage |
|---|---:|---:|---:|---:|---:|---:|
| `cluster_01` | 0.707 | 0.579 | 0.244 | 24.1% | 0.0% | 24.1% |
| `cluster_02` | 0.489 | 0.525 | 0.265 | 100.0% | 75.9% | 24.1% |
| `cluster_03` | 0.643 | 0.579 | 0.112 | 8.5% | 0.0% | 8.5% |

## Baseline overhead context

- Tool-definition cost coverage: 24/53 (45.3%)
- Observed-tool cost coverage: 0/29 (0.0%)
- Usage-weighted cost coverage: 0/6370 (0.0%)
- Exposure-record cost coverage: 100.0%
- Flat baseline known definition tokens: 6231.8
- Parent known definition tokens after partition: 6231.8
- Expected known tokens/session after partition: 6231.8
- Expected known-token savings/session: 0.0
- Delegation overhead assumption: 0 tokens per activated specialist

Known-token estimate using directly observed exposure only. Unknown tool-definition costs are excluded. Recovered telemetry costs use a chars/4 approximation. Unclustered tools remain on the parent to make the estimate conservative. Counterfactual exposure-model results are reported separately.

## Baseline exposure models

Direct exposure is telemetry evidence. Inferred exposure is a labeled counterfactual assumption and is never derived from calls in the same session.

| Model | Description | Runtime catalog | Sessions with inferred exposure | Inferred exposure rows | Sessions with provider availability |
|---|---|---:|---:|---:|---:|
| `observed_only` | Lower bound: charge only directly observed parent exposure; never use calls as exposure evidence. | 50 | 0 | 0 | 117 |
| `all_runtime_tools` | Counterfactual: expose every observed Codex runtime tool on the parent in every applicable Codex session. | 50 | 143 | 5185 | 117 |
| `provider_scoped` | Counterfactual: expose tools in providers explicitly marked available by Codex dynamic-tool telemetry. | 50 | 116 | 474 | 117 |

## Independent architecture variants

Variants are ranked by mid-case relative reduction; negative values are reported, not selected away.

## Pruned flat baseline

The flat parent retains every historically used tool plus recursively required dependencies.
**Recommendation: Remove the 21 directly observed, never-used exposed tools now.**

- Tools removed: `automation_update`, `capture_screen_context`, `codex_app`, `create_thread`, `end_realtime_voice_call`, `fork_thread`, `get_handoff_status`, `handoff_thread`, `list_projects`, `list_threads`, `load_workspace_dependencies`, `navigate_to_codex_page`, `open_in_codex`, `plugin_management`, `read_thread`, `read_thread_terminal`, `ready-for-agent`, `send_message_to_thread`, `send_realtime_voice_feedback`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title`, `uninstall_plugin`, `wait_threads`
- Tools retained: `exec`, `followup_task`, `github.add_comment_to_issue`, `github.add_issue_assignees`, `github.add_review_to_pr`, `github.create_issue`, `github.create_pull_request`, `github.fetch_file`, `github.fetch_issue`, `github.fetch_issue_comments`, `github.fetch_pr`, `github.fetch_pr_comments`, `github.fetch_pr_patch`, `github.get_pr_info`, `github.get_user_login`, `github.list_pr_changed_filenames`, `github.list_pull_request_review_threads`, `github.list_pull_request_reviews`, `github.reply_to_review_comment`, `github.resolve_review_thread`, `github.search_prs`, `github.update_issue`, `github.update_pull_request`, `interrupt_agent`, `list_agents`, `send_message`, `spawn_agent`, `wait`, `wait_agent`
- Historical called-tool coverage: 100.0%
- Dependency-preservation warnings: none
- Directly observed, never-used tools removed: `automation_update`, `capture_screen_context`, `create_thread`, `end_realtime_voice_call`, `fork_thread`, `get_handoff_status`, `handoff_thread`, `list_projects`, `list_threads`, `load_workspace_dependencies`, `navigate_to_codex_page`, `open_in_codex`, `read_thread`, `read_thread_terminal`, `send_message_to_thread`, `send_realtime_voice_feedback`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title`, `uninstall_plugin`, `wait_threads`
- Catalog-only tools removed: `codex_app`, `plugin_management`, `ready-for-agent`
- Unresolved retained runtime-tool exposure: unknown (29 tools)

| Scenario | Catalog tokens removed | Observed exposure removed/session | Baseline before pruning | Baseline after pruning | Relative reduction |
|---|---:|---:|---:|---:|---:|
| low | 7205.0 | 5098.7 | 5098.7 | 0.0 | 100.0% |
| mid | 7205.0 | 5098.7 | 5098.7 | 0.0 | 100.0% |
| high | 7205.0 | 5098.7 | 5098.7 | 0.0 | 100.0% |

Specialist architecture variants below are rebased against `pruned_flat_baseline`.

### 1. `cluster_01`

- Baseline architecture: `pruned_flat_baseline`
- Specialist tools: `github.add_comment_to_issue`, `github.add_review_to_pr`, `github.create_issue`, `github.fetch_file`, `github.fetch_issue`, `github.fetch_issue_comments`, `github.fetch_pr`, `github.fetch_pr_comments`, `github.fetch_pr_patch`, `github.list_pr_changed_filenames`, `github.reply_to_review_comment`, `github.search_prs`
- Historical called-tool coverage: 100.0%
- Mid-case sensitivity: 0.0% to 31.5%

#### Exposure model: `observed_only`

Lower bound: charge only directly observed parent exposure; never use calls as exposure evidence.

| Metric | Low | Mid | High |
|---|---:|---:|---:|
| Baseline tokens/session | 0.0 | 0.0 | 0.0 |
| Proposed tokens/session | 256.1 | 392.3 | 784.6 |
| Absolute reduction | -256.1 | -392.3 | -784.6 |
| Relative reduction | 0.0% | 0.0% | 0.0% |
| Specialist activation rate | 0.2 | 0.2 | 0.2 |

#### Exposure model: `all_runtime_tools`

Counterfactual: expose every observed Codex runtime tool on the parent in every applicable Codex session.

| Metric | Low | Mid | High |
|---|---:|---:|---:|
| Baseline tokens/session | 2602.8 | 3987.5 | 7975.0 |
| Proposed tokens/session | 1781.8 | 2729.8 | 5459.6 |
| Absolute reduction | 820.9 | 1257.7 | 2515.4 |
| Relative reduction | 31.5% | 31.5% | 31.5% |
| Specialist activation rate | 0.2 | 0.2 | 0.2 |

#### Exposure model: `provider_scoped`

Counterfactual: expose tools in providers explicitly marked available by Codex dynamic-tool telemetry.

| Metric | Low | Mid | High |
|---|---:|---:|---:|
| Baseline tokens/session | 0.0 | 0.0 | 0.0 |
| Proposed tokens/session | 256.1 | 392.3 | 784.6 |
| Absolute reduction | -256.1 | -392.3 | -784.6 |
| Relative reduction | 0.0% | 0.0% | 0.0% |
| Specialist activation rate | 0.2 | 0.2 | 0.2 |

### 2. `cluster_01_boundary_pruned`

- Baseline architecture: `pruned_flat_baseline`
- Specialist tools: `github.add_comment_to_issue`, `github.add_review_to_pr`, `github.create_issue`, `github.fetch_file`, `github.fetch_issue`, `github.fetch_issue_comments`, `github.fetch_pr`, `github.fetch_pr_comments`, `github.fetch_pr_patch`, `github.list_pr_changed_filenames`, `github.reply_to_review_comment`, `github.search_prs`
- Historical called-tool coverage: 100.0%
- Mid-case sensitivity: 0.0% to 31.5%

#### Exposure model: `observed_only`

Lower bound: charge only directly observed parent exposure; never use calls as exposure evidence.

| Metric | Low | Mid | High |
|---|---:|---:|---:|
| Baseline tokens/session | 0.0 | 0.0 | 0.0 |
| Proposed tokens/session | 256.1 | 392.3 | 784.6 |
| Absolute reduction | -256.1 | -392.3 | -784.6 |
| Relative reduction | 0.0% | 0.0% | 0.0% |
| Specialist activation rate | 0.2 | 0.2 | 0.2 |

#### Exposure model: `all_runtime_tools`

Counterfactual: expose every observed Codex runtime tool on the parent in every applicable Codex session.

| Metric | Low | Mid | High |
|---|---:|---:|---:|
| Baseline tokens/session | 2602.8 | 3987.5 | 7975.0 |
| Proposed tokens/session | 1781.8 | 2729.8 | 5459.6 |
| Absolute reduction | 820.9 | 1257.7 | 2515.4 |
| Relative reduction | 31.5% | 31.5% | 31.5% |
| Specialist activation rate | 0.2 | 0.2 | 0.2 |

#### Exposure model: `provider_scoped`

Counterfactual: expose tools in providers explicitly marked available by Codex dynamic-tool telemetry.

| Metric | Low | Mid | High |
|---|---:|---:|---:|
| Baseline tokens/session | 0.0 | 0.0 | 0.0 |
| Proposed tokens/session | 256.1 | 392.3 | 784.6 |
| Absolute reduction | -256.1 | -392.3 | -784.6 |
| Relative reduction | 0.0% | 0.0% | 0.0% |
| Specialist activation rate | 0.2 | 0.2 | 0.2 |

### 3. `cluster_02`

- Baseline architecture: `pruned_flat_baseline`
- Specialist tools: `followup_task`, `interrupt_agent`, `list_agents`, `send_message`, `spawn_agent`, `wait`, `wait_agent`
- Historical called-tool coverage: 100.0%
- Mid-case sensitivity: 0.0% to 6.2%

#### Exposure model: `observed_only`

Lower bound: charge only directly observed parent exposure; never use calls as exposure evidence.

| Metric | Low | Mid | High |
|---|---:|---:|---:|
| Baseline tokens/session | 0.0 | 0.0 | 0.0 |
| Proposed tokens/session | 465.7 | 713.5 | 1426.9 |
| Absolute reduction | -465.7 | -713.5 | -1426.9 |
| Relative reduction | 0.0% | 0.0% | 0.0% |
| Specialist activation rate | 0.7 | 0.7 | 0.7 |

#### Exposure model: `all_runtime_tools`

Counterfactual: expose every observed Codex runtime tool on the parent in every applicable Codex session.

| Metric | Low | Mid | High |
|---|---:|---:|---:|
| Baseline tokens/session | 2602.8 | 3987.5 | 7975.0 |
| Proposed tokens/session | 2440.2 | 3738.5 | 7476.9 |
| Absolute reduction | 162.6 | 249.0 | 498.1 |
| Relative reduction | 6.2% | 6.2% | 6.2% |
| Specialist activation rate | 0.7 | 0.7 | 0.7 |

#### Exposure model: `provider_scoped`

Counterfactual: expose tools in providers explicitly marked available by Codex dynamic-tool telemetry.

| Metric | Low | Mid | High |
|---|---:|---:|---:|
| Baseline tokens/session | 0.0 | 0.0 | 0.0 |
| Proposed tokens/session | 465.7 | 713.5 | 1426.9 |
| Absolute reduction | -465.7 | -713.5 | -1426.9 |
| Relative reduction | 0.0% | 0.0% | 0.0% |
| Specialist activation rate | 0.7 | 0.7 | 0.7 |

### 4. `cluster_02_boundary_pruned`

- Baseline architecture: `pruned_flat_baseline`
- Specialist tools: `followup_task`, `interrupt_agent`, `list_agents`, `send_message`, `spawn_agent`, `wait`, `wait_agent`
- Historical called-tool coverage: 100.0%
- Mid-case sensitivity: 0.0% to 6.2%

#### Exposure model: `observed_only`

Lower bound: charge only directly observed parent exposure; never use calls as exposure evidence.

| Metric | Low | Mid | High |
|---|---:|---:|---:|
| Baseline tokens/session | 0.0 | 0.0 | 0.0 |
| Proposed tokens/session | 465.7 | 713.5 | 1426.9 |
| Absolute reduction | -465.7 | -713.5 | -1426.9 |
| Relative reduction | 0.0% | 0.0% | 0.0% |
| Specialist activation rate | 0.7 | 0.7 | 0.7 |

#### Exposure model: `all_runtime_tools`

Counterfactual: expose every observed Codex runtime tool on the parent in every applicable Codex session.

| Metric | Low | Mid | High |
|---|---:|---:|---:|
| Baseline tokens/session | 2602.8 | 3987.5 | 7975.0 |
| Proposed tokens/session | 2440.2 | 3738.5 | 7476.9 |
| Absolute reduction | 162.6 | 249.0 | 498.1 |
| Relative reduction | 6.2% | 6.2% | 6.2% |
| Specialist activation rate | 0.7 | 0.7 | 0.7 |

#### Exposure model: `provider_scoped`

Counterfactual: expose tools in providers explicitly marked available by Codex dynamic-tool telemetry.

| Metric | Low | Mid | High |
|---|---:|---:|---:|
| Baseline tokens/session | 0.0 | 0.0 | 0.0 |
| Proposed tokens/session | 465.7 | 713.5 | 1426.9 |
| Absolute reduction | -465.7 | -713.5 | -1426.9 |
| Relative reduction | 0.0% | 0.0% | 0.0% |
| Specialist activation rate | 0.7 | 0.7 | 0.7 |

### 5. `cluster_03`

- Baseline architecture: `pruned_flat_baseline`
- Specialist tools: `github.add_issue_assignees`, `github.get_user_login`, `github.list_pull_request_review_threads`, `github.list_pull_request_reviews`
- Historical called-tool coverage: 100.0%
- Mid-case sensitivity: 0.0% to 12.6%

#### Exposure model: `observed_only`

Lower bound: charge only directly observed parent exposure; never use calls as exposure evidence.

| Metric | Low | Mid | High |
|---|---:|---:|---:|
| Baseline tokens/session | 0.0 | 0.0 | 0.0 |
| Proposed tokens/session | 30.1 | 46.2 | 92.3 |
| Absolute reduction | -30.1 | -46.2 | -92.3 |
| Relative reduction | 0.0% | 0.0% | 0.0% |
| Specialist activation rate | 0.1 | 0.1 | 0.1 |

#### Exposure model: `all_runtime_tools`

Counterfactual: expose every observed Codex runtime tool on the parent in every applicable Codex session.

| Metric | Low | Mid | High |
|---|---:|---:|---:|
| Baseline tokens/session | 2602.8 | 3987.5 | 7975.0 |
| Proposed tokens/session | 2273.9 | 3483.7 | 6967.3 |
| Absolute reduction | 328.9 | 503.8 | 1007.7 |
| Relative reduction | 12.6% | 12.6% | 12.6% |
| Specialist activation rate | 0.1 | 0.1 | 0.1 |

#### Exposure model: `provider_scoped`

Counterfactual: expose tools in providers explicitly marked available by Codex dynamic-tool telemetry.

| Metric | Low | Mid | High |
|---|---:|---:|---:|
| Baseline tokens/session | 0.0 | 0.0 | 0.0 |
| Proposed tokens/session | 30.1 | 46.2 | 92.3 |
| Absolute reduction | -30.1 | -46.2 | -92.3 |
| Relative reduction | 0.0% | 0.0% | 0.0% |
| Specialist activation rate | 0.1 | 0.1 | 0.1 |

### 6. `cluster_03_boundary_pruned`

- Baseline architecture: `pruned_flat_baseline`
- Specialist tools: `github.add_issue_assignees`, `github.get_user_login`, `github.list_pull_request_review_threads`, `github.list_pull_request_reviews`
- Historical called-tool coverage: 100.0%
- Mid-case sensitivity: 0.0% to 12.6%

#### Exposure model: `observed_only`

Lower bound: charge only directly observed parent exposure; never use calls as exposure evidence.

| Metric | Low | Mid | High |
|---|---:|---:|---:|
| Baseline tokens/session | 0.0 | 0.0 | 0.0 |
| Proposed tokens/session | 30.1 | 46.2 | 92.3 |
| Absolute reduction | -30.1 | -46.2 | -92.3 |
| Relative reduction | 0.0% | 0.0% | 0.0% |
| Specialist activation rate | 0.1 | 0.1 | 0.1 |

#### Exposure model: `all_runtime_tools`

Counterfactual: expose every observed Codex runtime tool on the parent in every applicable Codex session.

| Metric | Low | Mid | High |
|---|---:|---:|---:|
| Baseline tokens/session | 2602.8 | 3987.5 | 7975.0 |
| Proposed tokens/session | 2273.9 | 3483.7 | 6967.3 |
| Absolute reduction | 328.9 | 503.8 | 1007.7 |
| Relative reduction | 12.6% | 12.6% | 12.6% |
| Specialist activation rate | 0.1 | 0.1 | 0.1 |

#### Exposure model: `provider_scoped`

Counterfactual: expose tools in providers explicitly marked available by Codex dynamic-tool telemetry.

| Metric | Low | Mid | High |
|---|---:|---:|---:|
| Baseline tokens/session | 0.0 | 0.0 | 0.0 |
| Proposed tokens/session | 30.1 | 46.2 | 92.3 |
| Absolute reduction | -30.1 | -46.2 | -92.3 |
| Relative reduction | 0.0% | 0.0% | 0.0% |
| Specialist activation rate | 0.1 | 0.1 | 0.1 |

### 7. `pruned_flat_baseline`

- Baseline architecture: `pruned_flat_baseline`
- Specialist tools: none
- Historical called-tool coverage: 100.0%
- Mid-case sensitivity: 0.0% to 0.0%

#### Exposure model: `observed_only`

Lower bound: charge only directly observed parent exposure; never use calls as exposure evidence.

| Metric | Low | Mid | High |
|---|---:|---:|---:|
| Baseline tokens/session | 0.0 | 0.0 | 0.0 |
| Proposed tokens/session | 0.0 | 0.0 | 0.0 |
| Absolute reduction | 0.0 | 0.0 | 0.0 |
| Relative reduction | 0.0% | 0.0% | 0.0% |
| Specialist activation rate | 0.0 | 0.0 | 0.0 |

#### Exposure model: `all_runtime_tools`

Counterfactual: expose every observed Codex runtime tool on the parent in every applicable Codex session.

| Metric | Low | Mid | High |
|---|---:|---:|---:|
| Baseline tokens/session | 2602.8 | 3987.5 | 7975.0 |
| Proposed tokens/session | 2602.8 | 3987.5 | 7975.0 |
| Absolute reduction | 0.0 | 0.0 | 0.0 |
| Relative reduction | 0.0% | 0.0% | 0.0% |
| Specialist activation rate | 0.0 | 0.0 | 0.0 |

#### Exposure model: `provider_scoped`

Counterfactual: expose tools in providers explicitly marked available by Codex dynamic-tool telemetry.

| Metric | Low | Mid | High |
|---|---:|---:|---:|
| Baseline tokens/session | 0.0 | 0.0 | 0.0 |
| Proposed tokens/session | 0.0 | 0.0 | 0.0 |
| Absolute reduction | 0.0 | 0.0 | 0.0 |
| Relative reduction | 0.0% | 0.0% | 0.0% |
| Specialist activation rate | 0.0 | 0.0 | 0.0 |

## GitHub exposure sensitivity analysis

This is diagnostic sensitivity analysis, not reconstructed telemetry. Each applicable Codex session has probability p that the full Cluster 1 GitHub tool surface is exposed on the parent.

- Applicable Codex sessions: 143
- Historical specialist activation rate: 23.8%
- Classification: `worthwhile_above_break_even`

## Cluster 1 exhaustive subset evaluation

Evaluated 4083 subsets containing at least two Cluster 1 tools. Excluded tools remain on the parent.

### Pareto frontier

- `github.add_review_to_pr`, `github.list_pr_changed_filenames`: break-even 11.2%, definition 275.0, activation 11.2%
- `github.add_review_to_pr`, `github.reply_to_review_comment`: break-even 11.2%, definition 275.0, activation 11.2%
- `github.fetch_file`, `github.list_pr_changed_filenames`: break-even 11.2%, definition 275.0, activation 11.2%
- `github.list_pr_changed_filenames`, `github.reply_to_review_comment`: break-even 11.2%, definition 275.0, activation 11.2%

## Candidate decision table

| Candidate | Type | Tools | Activation | Definition tokens | Affinity | Min boundary | Worst-case reduction | Viable cells |
|---|---|---|---:|---:|---:|---:|---:|---:|
| `pareto_01` | pareto | `github.add_review_to_pr`, `github.list_pr_changed_filenames` | 11.2% | 275.0 | 0.725 | -0.206 | -18.0 | 93.8% |
| `pareto_02` | pareto | `github.add_review_to_pr`, `github.reply_to_review_comment` | 11.2% | 275.0 | 0.891 | 0.096 | -18.0 | 93.8% |
| `pareto_03` | pareto | `github.fetch_file`, `github.list_pr_changed_filenames` | 11.2% | 275.0 | 0.931 | 0.060 | -18.0 | 93.8% |
| `pareto_04` | pareto | `github.list_pr_changed_filenames`, `github.reply_to_review_comment` | 11.2% | 275.0 | 0.725 | -0.206 | -18.0 | 93.8% |
| `cluster_01_reference` | reference | `github.add_comment_to_issue`, `github.add_review_to_pr`, `github.create_issue`, `github.fetch_file`, `github.fetch_issue`, `github.fetch_issue_comments`, `github.fetch_pr`, `github.fetch_pr_comments`, `github.fetch_pr_patch`, `github.list_pr_changed_filenames`, `github.reply_to_review_comment`, `github.search_prs` | 23.8% | 1650.0 | 0.707 | 0.048 | -98.7 | 81.2% |

## Provider availability reconstruction

Availability and mappings below come only from explicit dynamic-tools groups; runtime calls never establish provider availability.

| Provider | Groups observed | Sessions | Advertised tools |
|---|---:|---:|---|
| `codex_app` | 533 | 117 | `automation_update`, `capture_screen_context`, `create_thread`, `end_realtime_voice_call`, `fork_thread`, `get_handoff_status`, `handoff_thread`, `list_projects`, `list_threads`, `load_workspace_dependencies`, `navigate_to_codex_page`, `open_in_codex`, `read_thread`, `read_thread_terminal`, `send_message_to_thread`, `send_realtime_voice_feedback`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title`, `wait_threads` |
| `plugin_management` | 499 | 99 | `uninstall_plugin` |

### GitHub-specific reconstruction

- Advertised GitHub-like tools: none
- Runtime `github.*` tools: `github.add_comment_to_issue`, `github.add_issue_assignees`, `github.add_review_to_pr`, `github.create_issue`, `github.create_pull_request`, `github.fetch_file`, `github.fetch_issue`, `github.fetch_issue_comments`, `github.fetch_pr`, `github.fetch_pr_comments`, `github.fetch_pr_patch`, `github.get_pr_info`, `github.get_user_login`, `github.list_pr_changed_filenames`, `github.list_pull_request_review_threads`, `github.list_pull_request_reviews`, `github.reply_to_review_comment`, `github.resolve_review_thread`, `github.search_prs`, `github.update_issue`, `github.update_pull_request`
- Unresolved mappings: `github.add_comment_to_issue`, `github.add_issue_assignees`, `github.add_review_to_pr`, `github.create_issue`, `github.create_pull_request`, `github.fetch_file`, `github.fetch_issue`, `github.fetch_issue_comments`, `github.fetch_pr`, `github.fetch_pr_comments`, `github.fetch_pr_patch`, `github.get_pr_info`, `github.get_user_login`, `github.list_pr_changed_filenames`, `github.list_pull_request_review_threads`, `github.list_pull_request_reviews`, `github.reply_to_review_comment`, `github.resolve_review_thread`, `github.search_prs`, `github.update_issue`, `github.update_pull_request`

## Provider-scoped session diagnostics

| Session | Provider availability observed? | Providers available | Inferred runtime tools | Directly exposed tools | Called tools |
|---|---|---|---|---|---|
| `codex:2026\08\02\rollout-2026-08-02T17-49-42-019fc4ab-3493-73b2-bad1-627e161d1734.jsonl` | yes | `codex_app`, `plugin_management` | none | `automation_update`, `capture_screen_context`, `create_thread`, `end_realtime_voice_call`, `fork_thread`, `get_handoff_status`, `handoff_thread`, `list_projects`, `list_threads`, `load_workspace_dependencies`, `navigate_to_codex_page`, `open_in_codex`, `read_thread`, `read_thread_terminal`, `send_message_to_thread`, `send_realtime_voice_feedback`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title`, `uninstall_plugin`, `wait_threads` | none |
| `codex:2026\08\03\rollout-2026-08-03T03-05-52-019fc6a8-64ce-7203-916b-f720dfabc194.jsonl` | yes | `codex_app` | `automation_update`, `capture_screen_context`, `end_realtime_voice_call`, `get_handoff_status`, `handoff_thread`, `load_workspace_dependencies`, `open_in_codex`, `read_thread_terminal`, `send_realtime_voice_feedback`, `wait_threads` | `create_thread`, `fork_thread`, `list_projects`, `list_threads`, `navigate_to_codex_page`, `read_thread`, `send_message_to_thread`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title` | `exec`, `wait` |
| `codex:2026\08\03\rollout-2026-08-03T04-19-38-019fc6eb-ed60-78a2-95de-1a4f20929e95.jsonl` | yes | `codex_app` | `automation_update`, `capture_screen_context`, `end_realtime_voice_call`, `get_handoff_status`, `handoff_thread`, `load_workspace_dependencies`, `open_in_codex`, `read_thread_terminal`, `send_realtime_voice_feedback`, `wait_threads` | `create_thread`, `fork_thread`, `list_projects`, `list_threads`, `navigate_to_codex_page`, `read_thread`, `send_message_to_thread`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title` | `exec`, `followup_task`, `github.add_comment_to_issue`, `github.add_review_to_pr`, `github.create_issue`, `github.fetch_file`, `github.fetch_issue`, `github.fetch_issue_comments`, `github.fetch_pr`, `github.fetch_pr_comments`, `github.fetch_pr_patch`, `github.list_pr_changed_filenames`, `github.reply_to_review_comment`, `github.search_prs`, `interrupt_agent`, `list_agents`, `send_message`, `spawn_agent`, `wait`, `wait_agent` |
| `codex:2026\08\03\rollout-2026-08-03T04-50-54-019fc708-8e3b-7cb1-a502-db72356ee434.jsonl` | yes | `codex_app` | `automation_update`, `capture_screen_context`, `end_realtime_voice_call`, `get_handoff_status`, `handoff_thread`, `load_workspace_dependencies`, `open_in_codex`, `read_thread_terminal`, `send_realtime_voice_feedback`, `wait_threads` | `create_thread`, `fork_thread`, `list_projects`, `list_threads`, `navigate_to_codex_page`, `read_thread`, `send_message_to_thread`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title` | `exec`, `github.create_issue`, `github.fetch_file`, `github.fetch_issue`, `github.fetch_issue_comments`, `github.fetch_pr`, `github.fetch_pr_patch`, `github.list_pr_changed_filenames`, `github.search_prs`, `wait` |
| `codex:2026\08\03\rollout-2026-08-03T04-51-05-019fc708-ba04-7d71-9991-62ae0a14ef3e.jsonl` | yes | `codex_app` | `automation_update`, `capture_screen_context`, `end_realtime_voice_call`, `get_handoff_status`, `handoff_thread`, `load_workspace_dependencies`, `open_in_codex`, `read_thread_terminal`, `send_realtime_voice_feedback`, `wait_threads` | `create_thread`, `fork_thread`, `list_projects`, `list_threads`, `navigate_to_codex_page`, `read_thread`, `send_message_to_thread`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title` | `exec`, `github.create_issue`, `github.fetch_issue`, `github.fetch_issue_comments`, `github.fetch_pr`, `github.fetch_pr_patch`, `github.search_prs` |
| `codex:2026\08\03\rollout-2026-08-03T05-20-51-019fc723-faef-71f0-a91f-886866fc64d6.jsonl` | yes | `codex_app` | `automation_update`, `capture_screen_context`, `end_realtime_voice_call`, `get_handoff_status`, `handoff_thread`, `load_workspace_dependencies`, `open_in_codex`, `read_thread_terminal`, `send_realtime_voice_feedback`, `wait_threads` | `create_thread`, `fork_thread`, `list_projects`, `list_threads`, `navigate_to_codex_page`, `read_thread`, `send_message_to_thread`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title` | `exec`, `github.add_comment_to_issue`, `github.create_issue`, `github.fetch_file`, `github.fetch_issue`, `github.fetch_issue_comments`, `github.fetch_pr`, `github.fetch_pr_comments`, `github.fetch_pr_patch`, `github.search_prs`, `wait` |
| `codex:2026\08\03\rollout-2026-08-03T05-21-01-019fc724-204a-7d02-af1f-d130b61f2c29.jsonl` | yes | `codex_app` | `automation_update`, `capture_screen_context`, `end_realtime_voice_call`, `get_handoff_status`, `handoff_thread`, `load_workspace_dependencies`, `open_in_codex`, `read_thread_terminal`, `send_realtime_voice_feedback`, `wait_threads` | `create_thread`, `fork_thread`, `list_projects`, `list_threads`, `navigate_to_codex_page`, `read_thread`, `send_message_to_thread`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title` | `exec`, `github.add_comment_to_issue`, `github.create_issue`, `github.fetch_file`, `github.fetch_issue`, `github.fetch_issue_comments`, `github.fetch_pr`, `github.fetch_pr_comments`, `github.fetch_pr_patch`, `github.search_prs`, `send_message`, `wait` |
| `codex:2026\08\03\rollout-2026-08-03T12-21-53-019fc8a5-720d-73b2-8546-5fcc59df0585.jsonl` | yes | `codex_app` | `automation_update`, `capture_screen_context`, `end_realtime_voice_call`, `get_handoff_status`, `handoff_thread`, `load_workspace_dependencies`, `open_in_codex`, `read_thread_terminal`, `send_realtime_voice_feedback`, `wait_threads` | `create_thread`, `fork_thread`, `list_projects`, `list_threads`, `navigate_to_codex_page`, `read_thread`, `send_message_to_thread`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title` | `exec`, `github.add_comment_to_issue`, `github.add_review_to_pr`, `github.create_issue`, `github.fetch_file`, `github.fetch_issue`, `github.fetch_issue_comments`, `github.fetch_pr`, `github.fetch_pr_comments`, `github.fetch_pr_patch`, `github.list_pr_changed_filenames`, `github.reply_to_review_comment`, `github.search_prs` |
| `codex:2026\08\03\rollout-2026-08-03T12-22-00-019fc8a5-8bf1-7c30-8e54-d8cbadec584c.jsonl` | yes | `codex_app` | `automation_update`, `capture_screen_context`, `end_realtime_voice_call`, `get_handoff_status`, `handoff_thread`, `load_workspace_dependencies`, `open_in_codex`, `read_thread_terminal`, `send_realtime_voice_feedback`, `wait_threads` | `create_thread`, `fork_thread`, `list_projects`, `list_threads`, `navigate_to_codex_page`, `read_thread`, `send_message_to_thread`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title` | `exec`, `github.add_comment_to_issue`, `github.add_review_to_pr`, `github.create_issue`, `github.fetch_file`, `github.fetch_issue`, `github.fetch_issue_comments`, `github.fetch_pr`, `github.fetch_pr_comments`, `github.fetch_pr_patch`, `github.list_pr_changed_filenames`, `github.reply_to_review_comment`, `github.search_prs`, `send_message` |
| `codex:2026\08\03\rollout-2026-08-03T13-13-26-019fc8d4-a201-73d3-b366-332dcf80d593.jsonl` | yes | `codex_app` | `automation_update`, `capture_screen_context`, `end_realtime_voice_call`, `get_handoff_status`, `handoff_thread`, `load_workspace_dependencies`, `open_in_codex`, `read_thread_terminal`, `send_realtime_voice_feedback`, `wait_threads` | `create_thread`, `fork_thread`, `list_projects`, `list_threads`, `navigate_to_codex_page`, `read_thread`, `send_message_to_thread`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title` | `exec`, `github.add_comment_to_issue`, `github.add_review_to_pr`, `github.create_issue`, `github.fetch_file`, `github.fetch_issue`, `github.fetch_issue_comments`, `github.fetch_pr`, `github.fetch_pr_comments`, `github.fetch_pr_patch`, `github.list_pr_changed_filenames`, `github.reply_to_review_comment`, `github.search_prs`, `send_message` |
| `codex:2026\08\03\rollout-2026-08-03T13-13-33-019fc8d4-bcf3-7633-8837-1c105d48f97d.jsonl` | yes | `codex_app` | `automation_update`, `capture_screen_context`, `end_realtime_voice_call`, `get_handoff_status`, `handoff_thread`, `load_workspace_dependencies`, `open_in_codex`, `read_thread_terminal`, `send_realtime_voice_feedback`, `wait_threads` | `create_thread`, `fork_thread`, `list_projects`, `list_threads`, `navigate_to_codex_page`, `read_thread`, `send_message_to_thread`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title` | `exec`, `github.add_comment_to_issue`, `github.add_review_to_pr`, `github.create_issue`, `github.fetch_file`, `github.fetch_issue`, `github.fetch_issue_comments`, `github.fetch_pr`, `github.fetch_pr_comments`, `github.fetch_pr_patch`, `github.list_pr_changed_filenames`, `github.reply_to_review_comment`, `github.search_prs`, `send_message` |
| `codex:2026\08\03\rollout-2026-08-03T13-17-16-019fc8d8-2510-7712-a128-2decd71bfe32.jsonl` | yes | `codex_app` | `automation_update`, `capture_screen_context`, `end_realtime_voice_call`, `get_handoff_status`, `handoff_thread`, `load_workspace_dependencies`, `open_in_codex`, `read_thread_terminal`, `send_realtime_voice_feedback`, `wait_threads` | `create_thread`, `fork_thread`, `list_projects`, `list_threads`, `navigate_to_codex_page`, `read_thread`, `send_message_to_thread`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title` | `exec`, `github.add_comment_to_issue`, `github.add_review_to_pr`, `github.create_issue`, `github.fetch_file`, `github.fetch_issue`, `github.fetch_issue_comments`, `github.fetch_pr`, `github.fetch_pr_comments`, `github.fetch_pr_patch`, `github.list_pr_changed_filenames`, `github.reply_to_review_comment`, `github.search_prs`, `send_message`, `wait_agent` |
| `codex:2026\08\03\rollout-2026-08-03T13-18-43-019fc8d9-7a85-7cc1-8b59-0be31220e3d0.jsonl` | yes | `codex_app` | `automation_update`, `capture_screen_context`, `end_realtime_voice_call`, `get_handoff_status`, `handoff_thread`, `load_workspace_dependencies`, `open_in_codex`, `read_thread_terminal`, `send_realtime_voice_feedback`, `wait_threads` | `create_thread`, `fork_thread`, `list_projects`, `list_threads`, `navigate_to_codex_page`, `read_thread`, `send_message_to_thread`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title` | `exec`, `github.add_comment_to_issue`, `github.add_review_to_pr`, `github.create_issue`, `github.fetch_file`, `github.fetch_issue`, `github.fetch_issue_comments`, `github.fetch_pr`, `github.fetch_pr_comments`, `github.fetch_pr_patch`, `github.list_pr_changed_filenames`, `github.reply_to_review_comment`, `github.search_prs`, `send_message`, `wait` |
| `codex:2026\08\03\rollout-2026-08-03T14-31-04-019fc91b-b619-7933-8372-daff8149b4be.jsonl` | yes | `codex_app` | `automation_update`, `capture_screen_context`, `end_realtime_voice_call`, `get_handoff_status`, `handoff_thread`, `load_workspace_dependencies`, `open_in_codex`, `read_thread_terminal`, `send_realtime_voice_feedback`, `wait_threads` | `create_thread`, `fork_thread`, `list_projects`, `list_threads`, `navigate_to_codex_page`, `read_thread`, `send_message_to_thread`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title` | `exec`, `github.add_comment_to_issue`, `github.add_review_to_pr`, `github.create_issue`, `github.fetch_file`, `github.fetch_issue`, `github.fetch_issue_comments`, `github.fetch_pr`, `github.fetch_pr_comments`, `github.fetch_pr_patch`, `github.list_pr_changed_filenames`, `github.reply_to_review_comment`, `github.search_prs`, `send_message`, `wait_agent` |
| `codex:2026\08\03\rollout-2026-08-03T14-31-11-019fc91b-d1cd-7933-b46a-8919b6bb25f2.jsonl` | yes | `codex_app` | `automation_update`, `capture_screen_context`, `end_realtime_voice_call`, `get_handoff_status`, `handoff_thread`, `load_workspace_dependencies`, `open_in_codex`, `read_thread_terminal`, `send_realtime_voice_feedback`, `wait_threads` | `create_thread`, `fork_thread`, `list_projects`, `list_threads`, `navigate_to_codex_page`, `read_thread`, `send_message_to_thread`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title` | `exec`, `github.add_comment_to_issue`, `github.add_review_to_pr`, `github.create_issue`, `github.fetch_file`, `github.fetch_issue`, `github.fetch_issue_comments`, `github.fetch_pr`, `github.fetch_pr_comments`, `github.fetch_pr_patch`, `github.list_pr_changed_filenames`, `github.reply_to_review_comment`, `github.search_prs`, `send_message` |
| `codex:2026\08\03\rollout-2026-08-03T14-31-18-019fc91b-eb8a-7562-86a3-1a742674469d.jsonl` | yes | `codex_app` | `automation_update`, `capture_screen_context`, `end_realtime_voice_call`, `get_handoff_status`, `handoff_thread`, `load_workspace_dependencies`, `open_in_codex`, `read_thread_terminal`, `send_realtime_voice_feedback`, `wait_threads` | `create_thread`, `fork_thread`, `list_projects`, `list_threads`, `navigate_to_codex_page`, `read_thread`, `send_message_to_thread`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title` | `exec`, `github.add_comment_to_issue`, `github.add_review_to_pr`, `github.create_issue`, `github.fetch_file`, `github.fetch_issue`, `github.fetch_issue_comments`, `github.fetch_pr`, `github.fetch_pr_comments`, `github.fetch_pr_patch`, `github.list_pr_changed_filenames`, `github.reply_to_review_comment`, `github.search_prs`, `send_message` |
| `codex:2026\08\03\rollout-2026-08-03T14-34-25-019fc91e-c99d-71e1-b933-6072968b226b.jsonl` | yes | `codex_app` | `automation_update`, `capture_screen_context`, `end_realtime_voice_call`, `get_handoff_status`, `handoff_thread`, `load_workspace_dependencies`, `open_in_codex`, `read_thread_terminal`, `send_realtime_voice_feedback`, `wait_threads` | `create_thread`, `fork_thread`, `list_projects`, `list_threads`, `navigate_to_codex_page`, `read_thread`, `send_message_to_thread`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title` | `exec`, `github.add_comment_to_issue`, `github.add_review_to_pr`, `github.create_issue`, `github.fetch_file`, `github.fetch_issue`, `github.fetch_issue_comments`, `github.fetch_pr`, `github.fetch_pr_comments`, `github.fetch_pr_patch`, `github.list_pr_changed_filenames`, `github.reply_to_review_comment`, `github.search_prs`, `send_message` |
| `codex:2026\08\03\rollout-2026-08-03T14-34-32-019fc91e-e2d1-7692-b254-89f22c7cb283.jsonl` | yes | `codex_app` | `automation_update`, `capture_screen_context`, `end_realtime_voice_call`, `get_handoff_status`, `handoff_thread`, `load_workspace_dependencies`, `open_in_codex`, `read_thread_terminal`, `send_realtime_voice_feedback`, `wait_threads` | `create_thread`, `fork_thread`, `list_projects`, `list_threads`, `navigate_to_codex_page`, `read_thread`, `send_message_to_thread`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title` | `exec`, `github.add_comment_to_issue`, `github.add_review_to_pr`, `github.create_issue`, `github.fetch_file`, `github.fetch_issue`, `github.fetch_issue_comments`, `github.fetch_pr`, `github.fetch_pr_comments`, `github.fetch_pr_patch`, `github.list_pr_changed_filenames`, `github.reply_to_review_comment`, `github.search_prs`, `send_message` |
| `codex:2026\08\03\rollout-2026-08-03T14-34-37-019fc91e-f855-71b0-964b-f1402bb9db20.jsonl` | yes | `codex_app` | `automation_update`, `capture_screen_context`, `end_realtime_voice_call`, `get_handoff_status`, `handoff_thread`, `load_workspace_dependencies`, `open_in_codex`, `read_thread_terminal`, `send_realtime_voice_feedback`, `wait_threads` | `create_thread`, `fork_thread`, `list_projects`, `list_threads`, `navigate_to_codex_page`, `read_thread`, `send_message_to_thread`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title` | `exec`, `github.add_comment_to_issue`, `github.add_review_to_pr`, `github.create_issue`, `github.fetch_file`, `github.fetch_issue`, `github.fetch_issue_comments`, `github.fetch_pr`, `github.fetch_pr_comments`, `github.fetch_pr_patch`, `github.list_pr_changed_filenames`, `github.reply_to_review_comment`, `github.search_prs`, `send_message` |
| `codex:2026\08\03\rollout-2026-08-03T14-41-36-019fc925-5940-7243-b8c0-1b6c250f6992.jsonl` | yes | `codex_app`, `plugin_management` | `capture_screen_context`, `end_realtime_voice_call`, `send_realtime_voice_feedback` | `automation_update`, `create_thread`, `fork_thread`, `get_handoff_status`, `handoff_thread`, `list_projects`, `list_threads`, `load_workspace_dependencies`, `navigate_to_codex_page`, `open_in_codex`, `read_thread`, `read_thread_terminal`, `send_message_to_thread`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title`, `uninstall_plugin`, `wait_threads` | `exec`, `followup_task`, `send_message`, `spawn_agent`, `wait_agent` |
| `codex:2026\08\03\rollout-2026-08-03T14-44-20-019fc927-dc78-7ea0-8ceb-f2121684929d.jsonl` | yes | `codex_app`, `plugin_management` | `capture_screen_context`, `end_realtime_voice_call`, `send_realtime_voice_feedback` | `automation_update`, `create_thread`, `fork_thread`, `get_handoff_status`, `handoff_thread`, `list_projects`, `list_threads`, `load_workspace_dependencies`, `navigate_to_codex_page`, `open_in_codex`, `read_thread`, `read_thread_terminal`, `send_message_to_thread`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title`, `uninstall_plugin`, `wait_threads` | `exec`, `send_message` |
| `codex:2026\08\03\rollout-2026-08-03T14-44-30-019fc928-0408-7bb2-8027-433f67ac344e.jsonl` | yes | `codex_app`, `plugin_management` | `capture_screen_context`, `end_realtime_voice_call`, `send_realtime_voice_feedback` | `automation_update`, `create_thread`, `fork_thread`, `get_handoff_status`, `handoff_thread`, `list_projects`, `list_threads`, `load_workspace_dependencies`, `navigate_to_codex_page`, `open_in_codex`, `read_thread`, `read_thread_terminal`, `send_message_to_thread`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title`, `uninstall_plugin`, `wait_threads` | `exec` |
| `codex:2026\08\03\rollout-2026-08-03T14-44-38-019fc928-2202-7b50-8ad8-7a23231ba133.jsonl` | yes | `codex_app`, `plugin_management` | `capture_screen_context`, `end_realtime_voice_call`, `send_realtime_voice_feedback` | `automation_update`, `create_thread`, `fork_thread`, `get_handoff_status`, `handoff_thread`, `list_projects`, `list_threads`, `load_workspace_dependencies`, `navigate_to_codex_page`, `open_in_codex`, `read_thread`, `read_thread_terminal`, `send_message_to_thread`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title`, `uninstall_plugin`, `wait_threads` | `exec` |
| `codex:2026\08\03\rollout-2026-08-03T14-56-20-019fc932-d800-7a10-9252-530dc5efcdc8.jsonl` | yes | `codex_app`, `plugin_management` | `capture_screen_context`, `end_realtime_voice_call`, `send_realtime_voice_feedback` | `automation_update`, `create_thread`, `fork_thread`, `get_handoff_status`, `handoff_thread`, `list_projects`, `list_threads`, `load_workspace_dependencies`, `navigate_to_codex_page`, `open_in_codex`, `read_thread`, `read_thread_terminal`, `send_message_to_thread`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title`, `uninstall_plugin`, `wait_threads` | `exec` |
| `codex:2026\08\03\rollout-2026-08-03T14-56-28-019fc932-f5de-7112-ba21-b4054c3c4d56.jsonl` | yes | `codex_app`, `plugin_management` | `capture_screen_context`, `end_realtime_voice_call`, `send_realtime_voice_feedback` | `automation_update`, `create_thread`, `fork_thread`, `get_handoff_status`, `handoff_thread`, `list_projects`, `list_threads`, `load_workspace_dependencies`, `navigate_to_codex_page`, `open_in_codex`, `read_thread`, `read_thread_terminal`, `send_message_to_thread`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title`, `uninstall_plugin`, `wait_threads` | `exec` |
| `codex:2026\08\03\rollout-2026-08-03T14-56-34-019fc933-0f80-7ac2-bcd3-20ffc5918bbc.jsonl` | yes | `codex_app`, `plugin_management` | `capture_screen_context`, `end_realtime_voice_call`, `send_realtime_voice_feedback` | `automation_update`, `create_thread`, `fork_thread`, `get_handoff_status`, `handoff_thread`, `list_projects`, `list_threads`, `load_workspace_dependencies`, `navigate_to_codex_page`, `open_in_codex`, `read_thread`, `read_thread_terminal`, `send_message_to_thread`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title`, `uninstall_plugin`, `wait_threads` | `exec`, `send_message` |
| `codex:2026\08\03\rollout-2026-08-03T15-43-33-019fc95e-1284-78d3-aa41-30c3be2ed763.jsonl` | yes | `codex_app`, `plugin_management` | `capture_screen_context`, `end_realtime_voice_call`, `send_realtime_voice_feedback` | `automation_update`, `create_thread`, `fork_thread`, `get_handoff_status`, `handoff_thread`, `list_projects`, `list_threads`, `load_workspace_dependencies`, `navigate_to_codex_page`, `open_in_codex`, `read_thread`, `read_thread_terminal`, `send_message_to_thread`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title`, `uninstall_plugin`, `wait_threads` | `exec`, `followup_task`, `interrupt_agent`, `list_agents`, `send_message`, `spawn_agent`, `wait_agent` |
| `codex:2026\08\03\rollout-2026-08-03T15-47-00-019fc961-3a8d-7872-9ef4-66bbf942088e.jsonl` | no | none | none | none | `exec` |
| `codex:2026\08\03\rollout-2026-08-03T15-52-56-019fc966-a9ec-79c3-8355-23c0d8ca4608.jsonl` | yes | `codex_app`, `plugin_management` | `capture_screen_context`, `end_realtime_voice_call`, `send_realtime_voice_feedback` | `automation_update`, `create_thread`, `fork_thread`, `get_handoff_status`, `handoff_thread`, `list_projects`, `list_threads`, `load_workspace_dependencies`, `navigate_to_codex_page`, `open_in_codex`, `read_thread`, `read_thread_terminal`, `send_message_to_thread`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title`, `uninstall_plugin`, `wait_threads` | `exec`, `followup_task`, `list_agents`, `spawn_agent`, `wait_agent` |
| `codex:2026\08\03\rollout-2026-08-03T16-15-09-019fc97a-ffb3-70c2-b22b-1c9d1cd0ebee.jsonl` | no | none | none | none | `exec`, `send_message` |
| `codex:2026\08\03\rollout-2026-08-03T16-54-18-019fc99e-d6df-75a2-90bc-508193ec420a.jsonl` | no | none | none | none | `exec` |
| `codex:2026\08\03\rollout-2026-08-03T16-54-22-019fc99e-ea3d-7931-b7a2-6d6eb98795ad.jsonl` | no | none | none | none | `exec`, `send_message` |
| `codex:2026\08\03\rollout-2026-08-03T16-54-26-019fc99e-f8b2-7251-b10a-dc61c89797c2.jsonl` | no | none | none | none | `exec` |
| `codex:2026\08\03\rollout-2026-08-03T17-10-48-019fc9ad-f436-7620-a3da-21a75aa3810c.jsonl` | no | none | none | none | `exec`, `send_message` |
| `codex:2026\08\03\rollout-2026-08-03T17-10-52-019fc9ae-04a7-7410-b4dc-b48faf98d2a9.jsonl` | no | none | none | none | `exec` |
| `codex:2026\08\03\rollout-2026-08-03T17-25-48-019fc9bb-af2b-7bf3-805d-9d72ee40c7b6.jsonl` | yes | `codex_app`, `plugin_management` | `capture_screen_context`, `end_realtime_voice_call`, `send_realtime_voice_feedback` | `automation_update`, `create_thread`, `fork_thread`, `get_handoff_status`, `handoff_thread`, `list_projects`, `list_threads`, `load_workspace_dependencies`, `navigate_to_codex_page`, `open_in_codex`, `read_thread`, `read_thread_terminal`, `send_message_to_thread`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title`, `uninstall_plugin`, `wait_threads` | `exec`, `wait` |
| `codex:2026\08\03\rollout-2026-08-03T17-54-36-019fc9d6-0d39-7dd2-b683-9fd4a422362c.jsonl` | yes | `codex_app`, `plugin_management` | `capture_screen_context`, `end_realtime_voice_call`, `send_realtime_voice_feedback` | `automation_update`, `create_thread`, `fork_thread`, `get_handoff_status`, `handoff_thread`, `list_projects`, `list_threads`, `load_workspace_dependencies`, `navigate_to_codex_page`, `open_in_codex`, `read_thread`, `read_thread_terminal`, `send_message_to_thread`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title`, `uninstall_plugin`, `wait_threads` | `exec`, `list_agents`, `send_message`, `spawn_agent`, `wait`, `wait_agent` |
| `codex:2026\08\03\rollout-2026-08-03T18-01-12-019fc9dc-197f-7c13-9730-d556ab3194f9.jsonl` | yes | `codex_app`, `plugin_management` | `capture_screen_context`, `end_realtime_voice_call`, `send_realtime_voice_feedback` | `automation_update`, `create_thread`, `fork_thread`, `get_handoff_status`, `handoff_thread`, `list_projects`, `list_threads`, `load_workspace_dependencies`, `navigate_to_codex_page`, `open_in_codex`, `read_thread`, `read_thread_terminal`, `send_message_to_thread`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title`, `uninstall_plugin`, `wait_threads` | `exec`, `send_message` |
| `codex:2026\08\03\rollout-2026-08-03T18-01-21-019fc9dc-3c20-7553-ada4-e566c6e83b0c.jsonl` | yes | `codex_app`, `plugin_management` | `capture_screen_context`, `end_realtime_voice_call`, `send_realtime_voice_feedback` | `automation_update`, `create_thread`, `fork_thread`, `get_handoff_status`, `handoff_thread`, `list_projects`, `list_threads`, `load_workspace_dependencies`, `navigate_to_codex_page`, `open_in_codex`, `read_thread`, `read_thread_terminal`, `send_message_to_thread`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title`, `uninstall_plugin`, `wait_threads` | `exec`, `send_message` |
| `codex:2026\08\03\rollout-2026-08-03T18-01-26-019fc9dc-50c5-7da3-86ae-d7768d0bd154.jsonl` | yes | `codex_app`, `plugin_management` | `capture_screen_context`, `end_realtime_voice_call`, `send_realtime_voice_feedback` | `automation_update`, `create_thread`, `fork_thread`, `get_handoff_status`, `handoff_thread`, `list_projects`, `list_threads`, `load_workspace_dependencies`, `navigate_to_codex_page`, `open_in_codex`, `read_thread`, `read_thread_terminal`, `send_message_to_thread`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title`, `uninstall_plugin`, `wait_threads` | `exec` |
| `codex:2026\08\03\rollout-2026-08-03T18-08-05-019fc9e2-662f-7c12-ba17-b20dc6310be4.jsonl` | yes | `codex_app`, `plugin_management` | `capture_screen_context`, `end_realtime_voice_call`, `send_realtime_voice_feedback` | `automation_update`, `create_thread`, `fork_thread`, `get_handoff_status`, `handoff_thread`, `list_projects`, `list_threads`, `load_workspace_dependencies`, `navigate_to_codex_page`, `open_in_codex`, `read_thread`, `read_thread_terminal`, `send_message_to_thread`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title`, `uninstall_plugin`, `wait_threads` | `exec`, `followup_task`, `list_agents`, `spawn_agent`, `wait_agent` |
| `codex:2026\08\03\rollout-2026-08-03T18-12-48-019fc9e6-b6f8-71f2-806c-d8dc30282fd5.jsonl` | yes | `codex_app`, `plugin_management` | `capture_screen_context`, `end_realtime_voice_call`, `send_realtime_voice_feedback` | `automation_update`, `create_thread`, `fork_thread`, `get_handoff_status`, `handoff_thread`, `list_projects`, `list_threads`, `load_workspace_dependencies`, `navigate_to_codex_page`, `open_in_codex`, `read_thread`, `read_thread_terminal`, `send_message_to_thread`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title`, `uninstall_plugin`, `wait_threads` | `exec` |
| `codex:2026\08\03\rollout-2026-08-03T18-12-59-019fc9e6-dfa5-7cc1-916c-414cd66f5f8a.jsonl` | yes | `codex_app`, `plugin_management` | `capture_screen_context`, `end_realtime_voice_call`, `send_realtime_voice_feedback` | `automation_update`, `create_thread`, `fork_thread`, `get_handoff_status`, `handoff_thread`, `list_projects`, `list_threads`, `load_workspace_dependencies`, `navigate_to_codex_page`, `open_in_codex`, `read_thread`, `read_thread_terminal`, `send_message_to_thread`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title`, `uninstall_plugin`, `wait_threads` | `exec`, `send_message` |
| `codex:2026\08\03\rollout-2026-08-03T18-13-06-019fc9e6-fd10-7e62-8ecb-e34d36fa2f01.jsonl` | yes | `codex_app`, `plugin_management` | `capture_screen_context`, `end_realtime_voice_call`, `send_realtime_voice_feedback` | `automation_update`, `create_thread`, `fork_thread`, `get_handoff_status`, `handoff_thread`, `list_projects`, `list_threads`, `load_workspace_dependencies`, `navigate_to_codex_page`, `open_in_codex`, `read_thread`, `read_thread_terminal`, `send_message_to_thread`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title`, `uninstall_plugin`, `wait_threads` | `exec`, `send_message` |
| `codex:2026\08\03\rollout-2026-08-03T18-19-31-019fc9ec-dd24-75a3-81f9-c4c8038e4120.jsonl` | yes | `codex_app`, `plugin_management` | `capture_screen_context`, `end_realtime_voice_call`, `send_realtime_voice_feedback` | `automation_update`, `create_thread`, `fork_thread`, `get_handoff_status`, `handoff_thread`, `list_projects`, `list_threads`, `load_workspace_dependencies`, `navigate_to_codex_page`, `open_in_codex`, `read_thread`, `read_thread_terminal`, `send_message_to_thread`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title`, `uninstall_plugin`, `wait_threads` | `exec`, `followup_task`, `github.add_issue_assignees`, `github.add_review_to_pr`, `github.fetch_issue`, `github.fetch_issue_comments`, `github.fetch_pr`, `github.fetch_pr_comments`, `github.fetch_pr_patch`, `github.get_user_login`, `github.list_pull_request_review_threads`, `github.list_pull_request_reviews`, `spawn_agent`, `wait_agent` |
| `codex:2026\08\03\rollout-2026-08-03T18-23-56-019fc9f0-e771-72f0-97d0-e2376017cbdb.jsonl` | yes | `codex_app`, `plugin_management` | `capture_screen_context`, `end_realtime_voice_call`, `send_realtime_voice_feedback` | `automation_update`, `create_thread`, `fork_thread`, `get_handoff_status`, `handoff_thread`, `list_projects`, `list_threads`, `load_workspace_dependencies`, `navigate_to_codex_page`, `open_in_codex`, `read_thread`, `read_thread_terminal`, `send_message_to_thread`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title`, `uninstall_plugin`, `wait_threads` | `exec`, `github.add_issue_assignees`, `github.fetch_issue`, `github.fetch_issue_comments`, `github.get_user_login`, `send_message` |
| `codex:2026\08\03\rollout-2026-08-03T18-24-06-019fc9f1-0ef3-7d10-9330-2a0c426e675a.jsonl` | yes | `codex_app`, `plugin_management` | `capture_screen_context`, `end_realtime_voice_call`, `send_realtime_voice_feedback` | `automation_update`, `create_thread`, `fork_thread`, `get_handoff_status`, `handoff_thread`, `list_projects`, `list_threads`, `load_workspace_dependencies`, `navigate_to_codex_page`, `open_in_codex`, `read_thread`, `read_thread_terminal`, `send_message_to_thread`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title`, `uninstall_plugin`, `wait_threads` | `exec`, `github.add_issue_assignees`, `github.fetch_issue`, `github.fetch_issue_comments`, `github.get_user_login`, `send_message` |
| `codex:2026\08\03\rollout-2026-08-03T18-24-12-019fc9f1-2599-7c12-a67e-14dce65209f6.jsonl` | yes | `codex_app`, `plugin_management` | `capture_screen_context`, `end_realtime_voice_call`, `send_realtime_voice_feedback` | `automation_update`, `create_thread`, `fork_thread`, `get_handoff_status`, `handoff_thread`, `list_projects`, `list_threads`, `load_workspace_dependencies`, `navigate_to_codex_page`, `open_in_codex`, `read_thread`, `read_thread_terminal`, `send_message_to_thread`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title`, `uninstall_plugin`, `wait_threads` | `exec`, `github.add_issue_assignees`, `github.fetch_issue`, `github.fetch_issue_comments`, `github.get_user_login` |
| `codex:2026\08\03\rollout-2026-08-03T18-24-56-019fc9f1-d3f9-77f3-bba0-e580f9e58cf8.jsonl` | yes | `codex_app`, `plugin_management` | `capture_screen_context`, `end_realtime_voice_call`, `send_realtime_voice_feedback` | `automation_update`, `create_thread`, `fork_thread`, `get_handoff_status`, `handoff_thread`, `list_projects`, `list_threads`, `load_workspace_dependencies`, `navigate_to_codex_page`, `open_in_codex`, `read_thread`, `read_thread_terminal`, `send_message_to_thread`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title`, `uninstall_plugin`, `wait_threads` | `exec`, `send_message` |
| `codex:2026\08\03\rollout-2026-08-03T18-25-04-019fc9f1-f02e-7232-ad78-b154c21a8377.jsonl` | yes | `codex_app`, `plugin_management` | `capture_screen_context`, `end_realtime_voice_call`, `send_realtime_voice_feedback` | `automation_update`, `create_thread`, `fork_thread`, `get_handoff_status`, `handoff_thread`, `list_projects`, `list_threads`, `load_workspace_dependencies`, `navigate_to_codex_page`, `open_in_codex`, `read_thread`, `read_thread_terminal`, `send_message_to_thread`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title`, `uninstall_plugin`, `wait_threads` | `exec` |
| `codex:2026\08\03\rollout-2026-08-03T18-25-09-019fc9f2-051a-7e71-a64d-58a7da4825af.jsonl` | yes | `codex_app`, `plugin_management` | `capture_screen_context`, `end_realtime_voice_call`, `send_realtime_voice_feedback` | `automation_update`, `create_thread`, `fork_thread`, `get_handoff_status`, `handoff_thread`, `list_projects`, `list_threads`, `load_workspace_dependencies`, `navigate_to_codex_page`, `open_in_codex`, `read_thread`, `read_thread_terminal`, `send_message_to_thread`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title`, `uninstall_plugin`, `wait_threads` | `exec`, `send_message` |
| `codex:2026\08\03\rollout-2026-08-03T18-25-56-019fc9f2-bdc1-75b1-a29e-3c043b983813.jsonl` | yes | `codex_app`, `plugin_management` | `capture_screen_context`, `end_realtime_voice_call`, `send_realtime_voice_feedback` | `automation_update`, `create_thread`, `fork_thread`, `get_handoff_status`, `handoff_thread`, `list_projects`, `list_threads`, `load_workspace_dependencies`, `navigate_to_codex_page`, `open_in_codex`, `read_thread`, `read_thread_terminal`, `send_message_to_thread`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title`, `uninstall_plugin`, `wait_threads` | `exec`, `send_message` |
| `codex:2026\08\03\rollout-2026-08-03T18-26-03-019fc9f2-d774-71c3-abfe-282162dee774.jsonl` | yes | `codex_app`, `plugin_management` | `capture_screen_context`, `end_realtime_voice_call`, `send_realtime_voice_feedback` | `automation_update`, `create_thread`, `fork_thread`, `get_handoff_status`, `handoff_thread`, `list_projects`, `list_threads`, `load_workspace_dependencies`, `navigate_to_codex_page`, `open_in_codex`, `read_thread`, `read_thread_terminal`, `send_message_to_thread`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title`, `uninstall_plugin`, `wait_threads` | `exec`, `send_message` |
| `codex:2026\08\03\rollout-2026-08-03T18-26-09-019fc9f2-ee33-7d92-be46-080f8e2060bd.jsonl` | yes | `codex_app`, `plugin_management` | `capture_screen_context`, `end_realtime_voice_call`, `send_realtime_voice_feedback` | `automation_update`, `create_thread`, `fork_thread`, `get_handoff_status`, `handoff_thread`, `list_projects`, `list_threads`, `load_workspace_dependencies`, `navigate_to_codex_page`, `open_in_codex`, `read_thread`, `read_thread_terminal`, `send_message_to_thread`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title`, `uninstall_plugin`, `wait_threads` | `exec` |
| `codex:2026\08\03\rollout-2026-08-03T18-31-09-019fc9f7-8505-71a0-87ca-8bea829555c8.jsonl` | yes | `codex_app`, `plugin_management` | `capture_screen_context`, `end_realtime_voice_call`, `send_realtime_voice_feedback` | `automation_update`, `create_thread`, `fork_thread`, `get_handoff_status`, `handoff_thread`, `list_projects`, `list_threads`, `load_workspace_dependencies`, `navigate_to_codex_page`, `open_in_codex`, `read_thread`, `read_thread_terminal`, `send_message_to_thread`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title`, `uninstall_plugin`, `wait_threads` | `exec`, `github.add_issue_assignees`, `github.fetch_issue`, `github.fetch_issue_comments`, `github.fetch_pr`, `github.fetch_pr_comments`, `github.fetch_pr_patch`, `github.get_user_login`, `github.list_pull_request_review_threads`, `github.list_pull_request_reviews`, `send_message` |
| `codex:2026\08\03\rollout-2026-08-03T18-31-18-019fc9f7-a678-7763-9323-10625de6dbf6.jsonl` | yes | `codex_app`, `plugin_management` | `capture_screen_context`, `end_realtime_voice_call`, `send_realtime_voice_feedback` | `automation_update`, `create_thread`, `fork_thread`, `get_handoff_status`, `handoff_thread`, `list_projects`, `list_threads`, `load_workspace_dependencies`, `navigate_to_codex_page`, `open_in_codex`, `read_thread`, `read_thread_terminal`, `send_message_to_thread`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title`, `uninstall_plugin`, `wait_threads` | `exec`, `github.add_issue_assignees`, `github.fetch_issue`, `github.fetch_issue_comments`, `github.fetch_pr`, `github.fetch_pr_comments`, `github.fetch_pr_patch`, `github.get_user_login`, `github.list_pull_request_review_threads`, `github.list_pull_request_reviews`, `send_message` |
| `codex:2026\08\03\rollout-2026-08-03T18-31-24-019fc9f7-bd55-7b70-b439-ebb1597ed5c0.jsonl` | yes | `codex_app`, `plugin_management` | `capture_screen_context`, `end_realtime_voice_call`, `send_realtime_voice_feedback` | `automation_update`, `create_thread`, `fork_thread`, `get_handoff_status`, `handoff_thread`, `list_projects`, `list_threads`, `load_workspace_dependencies`, `navigate_to_codex_page`, `open_in_codex`, `read_thread`, `read_thread_terminal`, `send_message_to_thread`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title`, `uninstall_plugin`, `wait_threads` | `exec`, `github.add_issue_assignees`, `github.fetch_issue`, `github.fetch_issue_comments`, `github.fetch_pr`, `github.fetch_pr_comments`, `github.fetch_pr_patch`, `github.get_user_login`, `github.list_pull_request_review_threads`, `github.list_pull_request_reviews`, `send_message` |
| `codex:2026\08\03\rollout-2026-08-03T18-40-43-019fca00-459e-79c2-a32c-db65e1e1d2df.jsonl` | yes | `codex_app`, `plugin_management` | `capture_screen_context`, `end_realtime_voice_call`, `send_realtime_voice_feedback` | `automation_update`, `create_thread`, `fork_thread`, `get_handoff_status`, `handoff_thread`, `list_projects`, `list_threads`, `load_workspace_dependencies`, `navigate_to_codex_page`, `open_in_codex`, `read_thread`, `read_thread_terminal`, `send_message_to_thread`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title`, `uninstall_plugin`, `wait_threads` | `exec`, `wait` |
| `codex:2026\08\03\rollout-2026-08-03T18-59-14-019fca11-37b8-7a13-995b-4e0e583ad767.jsonl` | yes | `codex_app`, `plugin_management` | `capture_screen_context`, `end_realtime_voice_call`, `send_realtime_voice_feedback` | `automation_update`, `create_thread`, `fork_thread`, `get_handoff_status`, `handoff_thread`, `list_projects`, `list_threads`, `load_workspace_dependencies`, `navigate_to_codex_page`, `open_in_codex`, `read_thread`, `read_thread_terminal`, `send_message_to_thread`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title`, `uninstall_plugin`, `wait_threads` | `exec`, `followup_task`, `github.add_comment_to_issue`, `github.add_issue_assignees`, `github.add_review_to_pr`, `github.create_pull_request`, `github.fetch_issue`, `github.fetch_issue_comments`, `github.fetch_pr`, `github.fetch_pr_comments`, `github.get_pr_info`, `github.get_user_login`, `github.list_pull_request_review_threads`, `github.list_pull_request_reviews`, `github.reply_to_review_comment`, `github.resolve_review_thread`, `github.update_pull_request`, `list_agents`, `spawn_agent`, `wait_agent` |
| `codex:2026\08\03\rollout-2026-08-03T19-06-34-019fca17-f096-7630-bc69-da5879216c61.jsonl` | yes | `codex_app`, `plugin_management` | `capture_screen_context`, `end_realtime_voice_call`, `send_realtime_voice_feedback` | `automation_update`, `create_thread`, `fork_thread`, `get_handoff_status`, `handoff_thread`, `list_projects`, `list_threads`, `load_workspace_dependencies`, `navigate_to_codex_page`, `open_in_codex`, `read_thread`, `read_thread_terminal`, `send_message_to_thread`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title`, `uninstall_plugin`, `wait_threads` | `exec`, `github.add_issue_assignees`, `github.fetch_issue`, `github.fetch_issue_comments`, `github.get_user_login` |
| `codex:2026\08\03\rollout-2026-08-03T19-06-44-019fca18-1900-7291-b539-453554f28318.jsonl` | yes | `codex_app`, `plugin_management` | `capture_screen_context`, `end_realtime_voice_call`, `send_realtime_voice_feedback` | `automation_update`, `create_thread`, `fork_thread`, `get_handoff_status`, `handoff_thread`, `list_projects`, `list_threads`, `load_workspace_dependencies`, `navigate_to_codex_page`, `open_in_codex`, `read_thread`, `read_thread_terminal`, `send_message_to_thread`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title`, `uninstall_plugin`, `wait_threads` | `exec`, `github.add_issue_assignees`, `github.fetch_issue`, `github.fetch_issue_comments`, `github.get_user_login`, `send_message` |
| `codex:2026\08\03\rollout-2026-08-03T19-06-52-019fca18-3753-7ac1-9bae-9b30b5e7f13b.jsonl` | yes | `codex_app`, `plugin_management` | `capture_screen_context`, `end_realtime_voice_call`, `send_realtime_voice_feedback` | `automation_update`, `create_thread`, `fork_thread`, `get_handoff_status`, `handoff_thread`, `list_projects`, `list_threads`, `load_workspace_dependencies`, `navigate_to_codex_page`, `open_in_codex`, `read_thread`, `read_thread_terminal`, `send_message_to_thread`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title`, `uninstall_plugin`, `wait_threads` | `exec`, `github.add_issue_assignees`, `github.fetch_issue`, `github.fetch_issue_comments`, `github.get_user_login`, `send_message` |
| `codex:2026\08\03\rollout-2026-08-03T19-57-42-019fca46-c0c0-7a22-b5f6-26efc92296d3.jsonl` | yes | `codex_app`, `plugin_management` | `capture_screen_context`, `end_realtime_voice_call`, `send_realtime_voice_feedback` | `automation_update`, `create_thread`, `fork_thread`, `get_handoff_status`, `handoff_thread`, `list_projects`, `list_threads`, `load_workspace_dependencies`, `navigate_to_codex_page`, `open_in_codex`, `read_thread`, `read_thread_terminal`, `send_message_to_thread`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title`, `uninstall_plugin`, `wait_threads` | `exec`, `github.add_comment_to_issue`, `github.fetch_pr`, `github.fetch_pr_comments`, `github.fetch_pr_patch`, `github.list_pull_request_review_threads`, `github.reply_to_review_comment`, `github.resolve_review_thread` |
| `codex:2026\08\03\rollout-2026-08-03T20-07-24-019fca4f-a393-7471-ae8b-375d4e8a918d.jsonl` | yes | `codex_app`, `plugin_management` | `capture_screen_context`, `end_realtime_voice_call`, `send_realtime_voice_feedback` | `automation_update`, `create_thread`, `fork_thread`, `get_handoff_status`, `handoff_thread`, `list_projects`, `list_threads`, `load_workspace_dependencies`, `navigate_to_codex_page`, `open_in_codex`, `read_thread`, `read_thread_terminal`, `send_message_to_thread`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title`, `uninstall_plugin`, `wait_threads` | `exec`, `followup_task`, `spawn_agent`, `wait`, `wait_agent` |
| `codex:2026\08\03\rollout-2026-08-03T20-14-13-019fca55-e04c-7543-9919-0ec77e2682c2.jsonl` | yes | `codex_app`, `plugin_management` | `capture_screen_context`, `end_realtime_voice_call`, `send_realtime_voice_feedback` | `automation_update`, `create_thread`, `fork_thread`, `get_handoff_status`, `handoff_thread`, `list_projects`, `list_threads`, `load_workspace_dependencies`, `navigate_to_codex_page`, `open_in_codex`, `read_thread`, `read_thread_terminal`, `send_message_to_thread`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title`, `uninstall_plugin`, `wait_threads` | `exec`, `send_message` |
| `codex:2026\08\03\rollout-2026-08-03T20-14-22-019fca56-02d2-7df3-a6b3-8fdb1eb8411b.jsonl` | yes | `codex_app`, `plugin_management` | `capture_screen_context`, `end_realtime_voice_call`, `send_realtime_voice_feedback` | `automation_update`, `create_thread`, `fork_thread`, `get_handoff_status`, `handoff_thread`, `list_projects`, `list_threads`, `load_workspace_dependencies`, `navigate_to_codex_page`, `open_in_codex`, `read_thread`, `read_thread_terminal`, `send_message_to_thread`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title`, `uninstall_plugin`, `wait_threads` | `exec`, `send_message` |
| `codex:2026\08\03\rollout-2026-08-03T20-14-28-019fca56-190f-7d61-a6d7-5bad399988c5.jsonl` | yes | `codex_app`, `plugin_management` | `capture_screen_context`, `end_realtime_voice_call`, `send_realtime_voice_feedback` | `automation_update`, `create_thread`, `fork_thread`, `get_handoff_status`, `handoff_thread`, `list_projects`, `list_threads`, `load_workspace_dependencies`, `navigate_to_codex_page`, `open_in_codex`, `read_thread`, `read_thread_terminal`, `send_message_to_thread`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title`, `uninstall_plugin`, `wait_threads` | `exec`, `send_message` |
| `codex:2026\08\03\rollout-2026-08-03T20-30-39-019fca64-ed4a-7920-80f8-d896789029d3.jsonl` | yes | `codex_app`, `plugin_management` | `capture_screen_context`, `end_realtime_voice_call`, `send_realtime_voice_feedback` | `automation_update`, `create_thread`, `fork_thread`, `get_handoff_status`, `handoff_thread`, `list_projects`, `list_threads`, `load_workspace_dependencies`, `navigate_to_codex_page`, `open_in_codex`, `read_thread`, `read_thread_terminal`, `send_message_to_thread`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title`, `uninstall_plugin`, `wait_threads` | `exec`, `followup_task`, `list_agents`, `send_message`, `spawn_agent`, `wait`, `wait_agent` |
| `codex:2026\08\03\rollout-2026-08-03T20-40-31-019fca6d-f33c-7d71-bef9-2f5ca17624bf.jsonl` | yes | `codex_app`, `plugin_management` | `capture_screen_context`, `end_realtime_voice_call`, `send_realtime_voice_feedback` | `automation_update`, `create_thread`, `fork_thread`, `get_handoff_status`, `handoff_thread`, `list_projects`, `list_threads`, `load_workspace_dependencies`, `navigate_to_codex_page`, `open_in_codex`, `read_thread`, `read_thread_terminal`, `send_message_to_thread`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title`, `uninstall_plugin`, `wait_threads` | `exec`, `send_message` |
| `codex:2026\08\03\rollout-2026-08-03T20-40-49-019fca6e-3ad0-7200-ba66-2b5ccf10ccec.jsonl` | yes | `codex_app`, `plugin_management` | `capture_screen_context`, `end_realtime_voice_call`, `send_realtime_voice_feedback` | `automation_update`, `create_thread`, `fork_thread`, `get_handoff_status`, `handoff_thread`, `list_projects`, `list_threads`, `load_workspace_dependencies`, `navigate_to_codex_page`, `open_in_codex`, `read_thread`, `read_thread_terminal`, `send_message_to_thread`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title`, `uninstall_plugin`, `wait_threads` | `exec` |
| `codex:2026\08\03\rollout-2026-08-03T20-41-02-019fca6e-6b11-7ed0-8928-adc6b401954d.jsonl` | yes | `codex_app`, `plugin_management` | `capture_screen_context`, `end_realtime_voice_call`, `send_realtime_voice_feedback` | `automation_update`, `create_thread`, `fork_thread`, `get_handoff_status`, `handoff_thread`, `list_projects`, `list_threads`, `load_workspace_dependencies`, `navigate_to_codex_page`, `open_in_codex`, `read_thread`, `read_thread_terminal`, `send_message_to_thread`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title`, `uninstall_plugin`, `wait_threads` | `exec` |
| `codex:2026\08\03\rollout-2026-08-03T20-56-04-019fca7c-31ff-72a1-a5bd-324baa9ce04c.jsonl` | yes | `codex_app`, `plugin_management` | `capture_screen_context`, `end_realtime_voice_call`, `send_realtime_voice_feedback` | `automation_update`, `create_thread`, `fork_thread`, `get_handoff_status`, `handoff_thread`, `list_projects`, `list_threads`, `load_workspace_dependencies`, `navigate_to_codex_page`, `open_in_codex`, `read_thread`, `read_thread_terminal`, `send_message_to_thread`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title`, `uninstall_plugin`, `wait_threads` | `exec`, `followup_task`, `list_agents`, `spawn_agent`, `wait`, `wait_agent` |
| `codex:2026\08\03\rollout-2026-08-03T21-03-47-019fca83-4127-7052-a9c6-1501b541f85a.jsonl` | yes | `codex_app`, `plugin_management` | `capture_screen_context`, `end_realtime_voice_call`, `send_realtime_voice_feedback` | `automation_update`, `create_thread`, `fork_thread`, `get_handoff_status`, `handoff_thread`, `list_projects`, `list_threads`, `load_workspace_dependencies`, `navigate_to_codex_page`, `open_in_codex`, `read_thread`, `read_thread_terminal`, `send_message_to_thread`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title`, `uninstall_plugin`, `wait_threads` | `exec`, `send_message` |
| `codex:2026\08\03\rollout-2026-08-03T21-03-56-019fca83-6470-7400-9497-913d7d40456a.jsonl` | yes | `codex_app`, `plugin_management` | `capture_screen_context`, `end_realtime_voice_call`, `send_realtime_voice_feedback` | `automation_update`, `create_thread`, `fork_thread`, `get_handoff_status`, `handoff_thread`, `list_projects`, `list_threads`, `load_workspace_dependencies`, `navigate_to_codex_page`, `open_in_codex`, `read_thread`, `read_thread_terminal`, `send_message_to_thread`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title`, `uninstall_plugin`, `wait_threads` | `exec`, `send_message`, `wait` |
| `codex:2026\08\03\rollout-2026-08-03T21-04-03-019fca83-7e6d-7b41-82db-8d16c564f958.jsonl` | yes | `codex_app`, `plugin_management` | `capture_screen_context`, `end_realtime_voice_call`, `send_realtime_voice_feedback` | `automation_update`, `create_thread`, `fork_thread`, `get_handoff_status`, `handoff_thread`, `list_projects`, `list_threads`, `load_workspace_dependencies`, `navigate_to_codex_page`, `open_in_codex`, `read_thread`, `read_thread_terminal`, `send_message_to_thread`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title`, `uninstall_plugin`, `wait_threads` | `exec`, `send_message` |
| `codex:2026\08\04\rollout-2026-08-04T01-44-17-019fcb84-0d78-7c72-8af9-a469cfb71e9f.jsonl` | yes | `codex_app`, `plugin_management` | `capture_screen_context`, `end_realtime_voice_call`, `send_realtime_voice_feedback` | `automation_update`, `create_thread`, `fork_thread`, `get_handoff_status`, `handoff_thread`, `list_projects`, `list_threads`, `load_workspace_dependencies`, `navigate_to_codex_page`, `open_in_codex`, `read_thread`, `read_thread_terminal`, `send_message_to_thread`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title`, `uninstall_plugin`, `wait_threads` | `exec`, `spawn_agent`, `wait` |
| `codex:2026\08\04\rollout-2026-08-04T01-59-47-019fcb92-421a-7632-a981-c7b70986333a.jsonl` | no | none | none | none | `exec` |
| `codex:2026\08\04\rollout-2026-08-04T02-15-54-019fcba1-021f-71e2-8b9f-4b71a56e5a0b.jsonl` | yes | `codex_app`, `plugin_management` | `capture_screen_context`, `end_realtime_voice_call`, `send_realtime_voice_feedback` | `automation_update`, `create_thread`, `fork_thread`, `get_handoff_status`, `handoff_thread`, `list_projects`, `list_threads`, `load_workspace_dependencies`, `navigate_to_codex_page`, `open_in_codex`, `read_thread`, `read_thread_terminal`, `send_message_to_thread`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title`, `uninstall_plugin`, `wait_threads` | `exec` |
| `codex:2026\08\04\rollout-2026-08-04T02-18-50-019fcba3-b12f-7a40-b1fd-6e6da7b2d45b.jsonl` | yes | `codex_app`, `plugin_management` | `capture_screen_context`, `end_realtime_voice_call`, `send_realtime_voice_feedback` | `automation_update`, `create_thread`, `fork_thread`, `get_handoff_status`, `handoff_thread`, `list_projects`, `list_threads`, `load_workspace_dependencies`, `navigate_to_codex_page`, `open_in_codex`, `read_thread`, `read_thread_terminal`, `send_message_to_thread`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title`, `uninstall_plugin`, `wait_threads` | `exec` |
| `codex:2026\08\04\rollout-2026-08-04T12-23-06-019fcdcc-e8a1-7650-838b-04ce9845e7b6.jsonl` | yes | `codex_app`, `plugin_management` | `capture_screen_context`, `end_realtime_voice_call`, `send_realtime_voice_feedback` | `automation_update`, `create_thread`, `fork_thread`, `get_handoff_status`, `handoff_thread`, `list_projects`, `list_threads`, `load_workspace_dependencies`, `navigate_to_codex_page`, `open_in_codex`, `read_thread`, `read_thread_terminal`, `send_message_to_thread`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title`, `uninstall_plugin`, `wait_threads` | `exec`, `followup_task`, `list_agents`, `send_message`, `spawn_agent`, `wait_agent` |
| `codex:2026\08\04\rollout-2026-08-04T12-24-20-019fcdce-0b4a-7182-b39d-deec9ea38ae5.jsonl` | yes | `codex_app`, `plugin_management` | `capture_screen_context`, `end_realtime_voice_call`, `send_realtime_voice_feedback` | `automation_update`, `create_thread`, `fork_thread`, `get_handoff_status`, `handoff_thread`, `list_projects`, `list_threads`, `load_workspace_dependencies`, `navigate_to_codex_page`, `open_in_codex`, `read_thread`, `read_thread_terminal`, `send_message_to_thread`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title`, `uninstall_plugin`, `wait_threads` | `exec`, `send_message`, `spawn_agent`, `wait`, `wait_agent` |
| `codex:2026\08\04\rollout-2026-08-04T12-24-28-019fcdce-2bc5-7ab0-888b-c54b27be0fcc.jsonl` | yes | `codex_app`, `plugin_management` | `capture_screen_context`, `end_realtime_voice_call`, `send_realtime_voice_feedback` | `automation_update`, `create_thread`, `fork_thread`, `get_handoff_status`, `handoff_thread`, `list_projects`, `list_threads`, `load_workspace_dependencies`, `navigate_to_codex_page`, `open_in_codex`, `read_thread`, `read_thread_terminal`, `send_message_to_thread`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title`, `uninstall_plugin`, `wait_threads` | `exec`, `wait` |
| `codex:2026\08\04\rollout-2026-08-04T12-47-07-019fcde2-e59f-7c82-b3f4-2fbc8dc57809.jsonl` | yes | `codex_app`, `plugin_management` | `capture_screen_context`, `end_realtime_voice_call`, `send_realtime_voice_feedback` | `automation_update`, `create_thread`, `fork_thread`, `get_handoff_status`, `handoff_thread`, `list_projects`, `list_threads`, `load_workspace_dependencies`, `navigate_to_codex_page`, `open_in_codex`, `read_thread`, `read_thread_terminal`, `send_message_to_thread`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title`, `uninstall_plugin`, `wait_threads` | `exec`, `send_message`, `wait` |
| `codex:2026\08\04\rollout-2026-08-04T12-51-28-019fcde6-e2c7-7f83-b39e-87f86ec80266.jsonl` | yes | `codex_app`, `plugin_management` | `capture_screen_context`, `end_realtime_voice_call`, `send_realtime_voice_feedback` | `automation_update`, `create_thread`, `fork_thread`, `get_handoff_status`, `handoff_thread`, `list_projects`, `list_threads`, `load_workspace_dependencies`, `navigate_to_codex_page`, `open_in_codex`, `read_thread`, `read_thread_terminal`, `send_message_to_thread`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title`, `uninstall_plugin`, `wait_threads` | `exec`, `send_message`, `wait` |
| `codex:2026\08\04\rollout-2026-08-04T12-54-54-019fcdea-0721-74e0-875e-76d308fe2838.jsonl` | yes | `codex_app`, `plugin_management` | `capture_screen_context`, `end_realtime_voice_call`, `send_realtime_voice_feedback` | `automation_update`, `create_thread`, `fork_thread`, `get_handoff_status`, `handoff_thread`, `list_projects`, `list_threads`, `load_workspace_dependencies`, `navigate_to_codex_page`, `open_in_codex`, `read_thread`, `read_thread_terminal`, `send_message_to_thread`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title`, `uninstall_plugin`, `wait_threads` | `exec`, `send_message`, `wait_agent` |
| `codex:2026\08\04\rollout-2026-08-04T13-07-23-019fcdf5-7541-7371-9dca-4670a0923433.jsonl` | yes | `codex_app`, `plugin_management` | `capture_screen_context`, `end_realtime_voice_call`, `send_realtime_voice_feedback` | `automation_update`, `create_thread`, `fork_thread`, `get_handoff_status`, `handoff_thread`, `list_projects`, `list_threads`, `load_workspace_dependencies`, `navigate_to_codex_page`, `open_in_codex`, `read_thread`, `read_thread_terminal`, `send_message_to_thread`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title`, `uninstall_plugin`, `wait_threads` | `exec`, `followup_task`, `list_agents`, `send_message`, `spawn_agent`, `wait`, `wait_agent` |
| `codex:2026\08\04\rollout-2026-08-04T13-09-28-019fcdf7-5dee-7540-8534-a12b8b92c6b7.jsonl` | yes | `codex_app`, `plugin_management` | `capture_screen_context`, `end_realtime_voice_call`, `send_realtime_voice_feedback` | `automation_update`, `create_thread`, `fork_thread`, `get_handoff_status`, `handoff_thread`, `list_projects`, `list_threads`, `load_workspace_dependencies`, `navigate_to_codex_page`, `open_in_codex`, `read_thread`, `read_thread_terminal`, `send_message_to_thread`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title`, `uninstall_plugin`, `wait_threads` | `exec`, `list_agents`, `send_message`, `spawn_agent`, `wait_agent` |
| `codex:2026\08\04\rollout-2026-08-04T13-12-18-019fcdf9-f431-7cb1-9690-cd6e3cd77075.jsonl` | no | none | none | none | `followup_task`, `interrupt_agent`, `list_agents`, `send_message`, `spawn_agent`, `wait_agent` |
| `codex:2026\08\04\rollout-2026-08-04T13-12-39-019fcdfa-47d6-75b0-991c-94d984c41c10.jsonl` | no | none | none | none | `exec` |
| `codex:2026\08\04\rollout-2026-08-04T13-17-13-019fcdfe-739d-7a31-9772-16adc8366752.jsonl` | no | none | none | none | `exec`, `send_message`, `wait` |
| `codex:2026\08\04\rollout-2026-08-04T13-17-28-019fcdfe-afdc-7ce3-bdb5-7f01133707d2.jsonl` | no | none | none | none | `exec`, `list_agents`, `send_message`, `wait`, `wait_agent` |
| `codex:2026\08\04\rollout-2026-08-04T13-28-53-019fce09-2191-74b3-a152-bced3a4fad20.jsonl` | no | none | none | none | `exec`, `send_message` |
| `codex:2026\08\04\rollout-2026-08-04T13-35-34-019fce0f-40ed-7f72-8cee-5c0a142cbc50.jsonl` | no | none | none | none | `exec`, `list_agents`, `send_message`, `spawn_agent`, `wait`, `wait_agent` |
| `codex:2026\08\04\rollout-2026-08-04T13-38-00-019fce11-7ba3-7013-8de6-1072c7dbe7b7.jsonl` | no | none | none | none | `exec` |
| `codex:2026\08\04\rollout-2026-08-04T13-47-45-019fce1a-6ade-78f3-89f6-a178331564c9.jsonl` | no | none | none | none | `exec`, `send_message` |
| `codex:2026\08\04\rollout-2026-08-04T14-19-39-019fce37-9e09-73e2-85e5-082bca53c5ec.jsonl` | yes | `codex_app`, `plugin_management` | `capture_screen_context`, `end_realtime_voice_call`, `send_realtime_voice_feedback` | `automation_update`, `create_thread`, `fork_thread`, `get_handoff_status`, `handoff_thread`, `list_projects`, `list_threads`, `load_workspace_dependencies`, `navigate_to_codex_page`, `open_in_codex`, `read_thread`, `read_thread_terminal`, `send_message_to_thread`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title`, `uninstall_plugin`, `wait_threads` | `exec`, `interrupt_agent`, `list_agents`, `send_message`, `spawn_agent`, `wait` |
| `codex:2026\08\04\rollout-2026-08-04T14-20-22-019fce38-4662-78d0-8b3c-8cce90d93189.jsonl` | yes | `codex_app`, `plugin_management` | `capture_screen_context`, `end_realtime_voice_call`, `send_realtime_voice_feedback` | `automation_update`, `create_thread`, `fork_thread`, `get_handoff_status`, `handoff_thread`, `list_projects`, `list_threads`, `load_workspace_dependencies`, `navigate_to_codex_page`, `open_in_codex`, `read_thread`, `read_thread_terminal`, `send_message_to_thread`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title`, `uninstall_plugin`, `wait_threads` | `exec` |
| `codex:2026\08\04\rollout-2026-08-04T14-20-26-019fce38-56fa-7431-8a61-1a695ed36851.jsonl` | yes | `codex_app`, `plugin_management` | `capture_screen_context`, `end_realtime_voice_call`, `send_realtime_voice_feedback` | `automation_update`, `create_thread`, `fork_thread`, `get_handoff_status`, `handoff_thread`, `list_projects`, `list_threads`, `load_workspace_dependencies`, `navigate_to_codex_page`, `open_in_codex`, `read_thread`, `read_thread_terminal`, `send_message_to_thread`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title`, `uninstall_plugin`, `wait_threads` | `exec` |
| `codex:2026\08\04\rollout-2026-08-04T14-42-05-019fce4c-267a-77e2-b7a9-4b731b00dfb6.jsonl` | yes | `codex_app`, `plugin_management` | `capture_screen_context`, `end_realtime_voice_call`, `send_realtime_voice_feedback` | `automation_update`, `create_thread`, `fork_thread`, `get_handoff_status`, `handoff_thread`, `list_projects`, `list_threads`, `load_workspace_dependencies`, `navigate_to_codex_page`, `open_in_codex`, `read_thread`, `read_thread_terminal`, `send_message_to_thread`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title`, `uninstall_plugin`, `wait_threads` | `exec`, `wait` |
| `codex:2026\08\04\rollout-2026-08-04T14-49-47-019fce53-331a-7523-9c48-41ea10c2db56.jsonl` | yes | `codex_app`, `plugin_management` | `capture_screen_context`, `end_realtime_voice_call`, `send_realtime_voice_feedback` | `automation_update`, `create_thread`, `fork_thread`, `get_handoff_status`, `handoff_thread`, `list_projects`, `list_threads`, `load_workspace_dependencies`, `navigate_to_codex_page`, `open_in_codex`, `read_thread`, `read_thread_terminal`, `send_message_to_thread`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title`, `uninstall_plugin`, `wait_threads` | `exec`, `send_message`, `wait` |
| `codex:2026\08\04\rollout-2026-08-04T14-57-08-019fce59-efa3-79a2-a938-c82067fad785.jsonl` | yes | `codex_app`, `plugin_management` | `capture_screen_context`, `end_realtime_voice_call`, `send_realtime_voice_feedback` | `automation_update`, `create_thread`, `fork_thread`, `get_handoff_status`, `handoff_thread`, `list_projects`, `list_threads`, `load_workspace_dependencies`, `navigate_to_codex_page`, `open_in_codex`, `read_thread`, `read_thread_terminal`, `send_message_to_thread`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title`, `uninstall_plugin`, `wait_threads` | `exec`, `wait` |
| `codex:2026\08\04\rollout-2026-08-04T15-02-52-019fce5f-3035-7513-8a43-b952537b91d0.jsonl` | yes | `codex_app`, `plugin_management` | `capture_screen_context`, `end_realtime_voice_call`, `send_realtime_voice_feedback` | `automation_update`, `create_thread`, `fork_thread`, `get_handoff_status`, `handoff_thread`, `list_projects`, `list_threads`, `load_workspace_dependencies`, `navigate_to_codex_page`, `open_in_codex`, `read_thread`, `read_thread_terminal`, `send_message_to_thread`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title`, `uninstall_plugin`, `wait_threads` | `exec`, `list_agents`, `send_message`, `spawn_agent`, `wait_agent` |
| `codex:2026\08\04\rollout-2026-08-04T15-04-23-019fce60-9241-78a1-9f8a-b8257ee3a359.jsonl` | yes | `codex_app`, `plugin_management` | `capture_screen_context`, `end_realtime_voice_call`, `send_realtime_voice_feedback` | `automation_update`, `create_thread`, `fork_thread`, `get_handoff_status`, `handoff_thread`, `list_projects`, `list_threads`, `load_workspace_dependencies`, `navigate_to_codex_page`, `open_in_codex`, `read_thread`, `read_thread_terminal`, `send_message_to_thread`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title`, `uninstall_plugin`, `wait_threads` | `exec`, `send_message`, `wait` |
| `codex:2026\08\04\rollout-2026-08-04T15-09-57-019fce65-ab6e-7f13-a089-44835bb23744.jsonl` | no | none | none | none | `exec`, `send_message`, `wait` |
| `codex:2026\08\04\rollout-2026-08-04T15-19-11-019fce6e-1eeb-7ee1-a9c5-c9642c767fe6.jsonl` | yes | `codex_app`, `plugin_management` | `capture_screen_context`, `end_realtime_voice_call`, `send_realtime_voice_feedback` | `automation_update`, `create_thread`, `fork_thread`, `get_handoff_status`, `handoff_thread`, `list_projects`, `list_threads`, `load_workspace_dependencies`, `navigate_to_codex_page`, `open_in_codex`, `read_thread`, `read_thread_terminal`, `send_message_to_thread`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title`, `uninstall_plugin`, `wait_threads` | `exec` |
| `codex:2026\08\04\rollout-2026-08-04T15-19-24-019fce6e-4f2b-7003-966a-e711f72dc9fe.jsonl` | yes | `codex_app`, `plugin_management` | `capture_screen_context`, `end_realtime_voice_call`, `send_realtime_voice_feedback` | `automation_update`, `create_thread`, `fork_thread`, `get_handoff_status`, `handoff_thread`, `list_projects`, `list_threads`, `load_workspace_dependencies`, `navigate_to_codex_page`, `open_in_codex`, `read_thread`, `read_thread_terminal`, `send_message_to_thread`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title`, `uninstall_plugin`, `wait_threads` | `exec` |
| `codex:2026\08\04\rollout-2026-08-04T15-19-34-019fce6e-7983-7102-898b-015d469cc820.jsonl` | yes | `codex_app`, `plugin_management` | `capture_screen_context`, `end_realtime_voice_call`, `send_realtime_voice_feedback` | `automation_update`, `create_thread`, `fork_thread`, `get_handoff_status`, `handoff_thread`, `list_projects`, `list_threads`, `load_workspace_dependencies`, `navigate_to_codex_page`, `open_in_codex`, `read_thread`, `read_thread_terminal`, `send_message_to_thread`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title`, `uninstall_plugin`, `wait_threads` | `exec`, `send_message`, `wait` |
| `codex:2026\08\04\rollout-2026-08-04T15-36-06-019fce7d-9bbe-7f52-bd1d-709b79856859.jsonl` | no | none | none | none | `exec` |
| `codex:2026\08\04\rollout-2026-08-04T15-36-23-019fce7d-dacc-72f0-9307-275b04272f48.jsonl` | no | none | none | none | `exec`, `send_message`, `wait` |
| `codex:2026\08\04\rollout-2026-08-04T15-36-42-019fce7e-260a-7b90-920f-696dde5dcaf2.jsonl` | no | none | none | none | `exec`, `wait` |
| `codex:2026\08\04\rollout-2026-08-04T15-44-09-019fce84-fb4a-7260-a751-95d4f20a9e31.jsonl` | yes | `codex_app`, `plugin_management` | `capture_screen_context`, `end_realtime_voice_call`, `send_realtime_voice_feedback` | `automation_update`, `create_thread`, `fork_thread`, `get_handoff_status`, `handoff_thread`, `list_projects`, `list_threads`, `load_workspace_dependencies`, `navigate_to_codex_page`, `open_in_codex`, `read_thread`, `read_thread_terminal`, `send_message_to_thread`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title`, `uninstall_plugin`, `wait_threads` | `exec`, `send_message`, `wait`, `wait_agent` |
| `codex:2026\08\04\rollout-2026-08-04T15-57-50-019fce91-8174-7360-b2a7-5f935dfac0a8.jsonl` | yes | `codex_app`, `plugin_management` | `capture_screen_context`, `end_realtime_voice_call`, `send_realtime_voice_feedback` | `automation_update`, `create_thread`, `fork_thread`, `get_handoff_status`, `handoff_thread`, `list_projects`, `list_threads`, `load_workspace_dependencies`, `navigate_to_codex_page`, `open_in_codex`, `read_thread`, `read_thread_terminal`, `send_message_to_thread`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title`, `uninstall_plugin`, `wait_threads` | `exec`, `send_message`, `wait` |
| `codex:2026\08\04\rollout-2026-08-04T16-56-49-019fcec7-805b-7752-834c-d7435bb52f56.jsonl` | yes | `codex_app`, `plugin_management` | `capture_screen_context`, `end_realtime_voice_call`, `send_realtime_voice_feedback` | `automation_update`, `create_thread`, `fork_thread`, `get_handoff_status`, `handoff_thread`, `list_projects`, `list_threads`, `load_workspace_dependencies`, `navigate_to_codex_page`, `open_in_codex`, `read_thread`, `read_thread_terminal`, `send_message_to_thread`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title`, `uninstall_plugin`, `wait_threads` | `exec`, `followup_task`, `interrupt_agent`, `list_agents`, `send_message`, `spawn_agent`, `wait_agent` |
| `codex:2026\08\04\rollout-2026-08-04T16-59-44-019fceca-2b25-7021-970a-c4a5b3a71834.jsonl` | yes | `codex_app`, `plugin_management` | `capture_screen_context`, `end_realtime_voice_call`, `send_realtime_voice_feedback` | `automation_update`, `create_thread`, `fork_thread`, `get_handoff_status`, `handoff_thread`, `list_projects`, `list_threads`, `load_workspace_dependencies`, `navigate_to_codex_page`, `open_in_codex`, `read_thread`, `read_thread_terminal`, `send_message_to_thread`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title`, `uninstall_plugin`, `wait_threads` | `exec`, `send_message` |
| `codex:2026\08\04\rollout-2026-08-04T17-01-51-019fcecc-1d53-7302-9e32-1fe3371672e0.jsonl` | yes | `codex_app`, `plugin_management` | `capture_screen_context`, `end_realtime_voice_call`, `send_realtime_voice_feedback` | `automation_update`, `create_thread`, `fork_thread`, `get_handoff_status`, `handoff_thread`, `list_projects`, `list_threads`, `load_workspace_dependencies`, `navigate_to_codex_page`, `open_in_codex`, `read_thread`, `read_thread_terminal`, `send_message_to_thread`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title`, `uninstall_plugin`, `wait_threads` | `exec`, `wait` |
| `codex:2026\08\04\rollout-2026-08-04T17-02-15-019fcecc-7b28-7451-a25d-1d9fbe285b2b.jsonl` | yes | `codex_app`, `plugin_management` | `capture_screen_context`, `end_realtime_voice_call`, `send_realtime_voice_feedback` | `automation_update`, `create_thread`, `fork_thread`, `get_handoff_status`, `handoff_thread`, `list_projects`, `list_threads`, `load_workspace_dependencies`, `navigate_to_codex_page`, `open_in_codex`, `read_thread`, `read_thread_terminal`, `send_message_to_thread`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title`, `uninstall_plugin`, `wait_threads` | `exec`, `send_message` |
| `codex:2026\08\04\rollout-2026-08-04T17-02-29-019fcecc-b076-7580-bc5b-8e2212681694.jsonl` | yes | `codex_app`, `plugin_management` | `capture_screen_context`, `end_realtime_voice_call`, `send_realtime_voice_feedback` | `automation_update`, `create_thread`, `fork_thread`, `get_handoff_status`, `handoff_thread`, `list_projects`, `list_threads`, `load_workspace_dependencies`, `navigate_to_codex_page`, `open_in_codex`, `read_thread`, `read_thread_terminal`, `send_message_to_thread`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title`, `uninstall_plugin`, `wait_threads` | `exec`, `send_message` |
| `codex:2026\08\04\rollout-2026-08-04T17-42-31-019fcef1-5793-7271-9373-70b6d053af49.jsonl` | yes | `codex_app`, `plugin_management` | `capture_screen_context`, `end_realtime_voice_call`, `send_realtime_voice_feedback` | `automation_update`, `create_thread`, `fork_thread`, `get_handoff_status`, `handoff_thread`, `list_projects`, `list_threads`, `load_workspace_dependencies`, `navigate_to_codex_page`, `open_in_codex`, `read_thread`, `read_thread_terminal`, `send_message_to_thread`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title`, `uninstall_plugin`, `wait_threads` | `exec`, `followup_task`, `interrupt_agent`, `spawn_agent`, `wait_agent` |
| `codex:2026\08\04\rollout-2026-08-04T17-43-00-019fcef1-cac2-7d63-8ac5-07db9741a5f8.jsonl` | no | none | none | none | `exec` |
| `codex:2026\08\04\rollout-2026-08-04T17-45-04-019fcef3-ad86-74d3-a9b7-c2f4a5b1e1ee.jsonl` | yes | `codex_app`, `plugin_management` | `capture_screen_context`, `end_realtime_voice_call`, `send_realtime_voice_feedback` | `automation_update`, `create_thread`, `fork_thread`, `get_handoff_status`, `handoff_thread`, `list_projects`, `list_threads`, `load_workspace_dependencies`, `navigate_to_codex_page`, `open_in_codex`, `read_thread`, `read_thread_terminal`, `send_message_to_thread`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title`, `uninstall_plugin`, `wait_threads` | none |
| `codex:2026\08\04\rollout-2026-08-04T17-45-23-019fcef3-f929-7953-8965-4f3c2978d62b.jsonl` | no | none | none | none | `exec`, `wait` |
| `codex:2026\08\04\rollout-2026-08-04T17-51-44-019fcef9-c934-7b51-95b4-bc7bd3b80134.jsonl` | no | none | none | none | `exec` |
| `codex:2026\08\04\rollout-2026-08-04T17-51-55-019fcef9-f10f-7413-a7af-049e97b6766d.jsonl` | no | none | none | none | `exec`, `send_message` |
| `codex:2026\08\04\rollout-2026-08-04T17-52-03-019fcefa-1066-7e21-8287-35d80a2156ae.jsonl` | no | none | none | none | `exec` |
| `codex:2026\08\04\rollout-2026-08-04T18-02-06-019fcf03-47e5-7ed1-9bfb-932c9666f59e.jsonl` | no | none | none | none | `exec`, `wait` |
| `codex:2026\08\04\rollout-2026-08-04T18-37-42-019fcf23-de3c-7453-b129-854784a2766e.jsonl` | yes | `codex_app`, `plugin_management` | `capture_screen_context`, `end_realtime_voice_call`, `send_realtime_voice_feedback` | `automation_update`, `create_thread`, `fork_thread`, `get_handoff_status`, `handoff_thread`, `list_projects`, `list_threads`, `load_workspace_dependencies`, `navigate_to_codex_page`, `open_in_codex`, `read_thread`, `read_thread_terminal`, `send_message_to_thread`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title`, `uninstall_plugin`, `wait_threads` | `exec`, `followup_task`, `github.fetch_issue`, `github.fetch_issue_comments`, `interrupt_agent`, `list_agents`, `send_message`, `spawn_agent`, `wait`, `wait_agent` |
| `codex:2026\08\04\rollout-2026-08-04T18-40-34-019fcf26-7c7f-75a1-8264-3606b83a7cb9.jsonl` | yes | `codex_app`, `plugin_management` | `capture_screen_context`, `end_realtime_voice_call`, `send_realtime_voice_feedback` | `automation_update`, `create_thread`, `fork_thread`, `get_handoff_status`, `handoff_thread`, `list_projects`, `list_threads`, `load_workspace_dependencies`, `navigate_to_codex_page`, `open_in_codex`, `read_thread`, `read_thread_terminal`, `send_message_to_thread`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title`, `uninstall_plugin`, `wait_threads` | `exec`, `send_message`, `wait` |
| `codex:2026\08\04\rollout-2026-08-04T18-47-20-019fcf2c-b080-7181-b8f4-8557866fcd73.jsonl` | yes | `codex_app`, `plugin_management` | `capture_screen_context`, `end_realtime_voice_call`, `send_realtime_voice_feedback` | `automation_update`, `create_thread`, `fork_thread`, `get_handoff_status`, `handoff_thread`, `list_projects`, `list_threads`, `load_workspace_dependencies`, `navigate_to_codex_page`, `open_in_codex`, `read_thread`, `read_thread_terminal`, `send_message_to_thread`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title`, `uninstall_plugin`, `wait_threads` | `exec`, `github.fetch_issue`, `github.fetch_issue_comments`, `github.update_issue`, `wait` |
| `codex:2026\08\04\rollout-2026-08-04T18-57-26-019fcf35-ee35-7bd2-8a40-3636fc98d75b.jsonl` | yes | `codex_app`, `plugin_management` | `capture_screen_context`, `end_realtime_voice_call`, `send_realtime_voice_feedback` | `automation_update`, `create_thread`, `fork_thread`, `get_handoff_status`, `handoff_thread`, `list_projects`, `list_threads`, `load_workspace_dependencies`, `navigate_to_codex_page`, `open_in_codex`, `read_thread`, `read_thread_terminal`, `send_message_to_thread`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title`, `uninstall_plugin`, `wait_threads` | `exec`, `list_agents`, `send_message`, `wait`, `wait_agent` |
| `codex:2026\08\04\rollout-2026-08-04T19-02-05-019fcf3a-3021-7613-a774-34dbf9f9b957.jsonl` | yes | `codex_app`, `plugin_management` | `capture_screen_context`, `end_realtime_voice_call`, `send_realtime_voice_feedback` | `automation_update`, `create_thread`, `fork_thread`, `get_handoff_status`, `handoff_thread`, `list_projects`, `list_threads`, `load_workspace_dependencies`, `navigate_to_codex_page`, `open_in_codex`, `read_thread`, `read_thread_terminal`, `send_message_to_thread`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title`, `uninstall_plugin`, `wait_threads` | `exec`, `followup_task`, `list_agents`, `send_message`, `spawn_agent`, `wait_agent` |
| `codex:2026\08\04\rollout-2026-08-04T19-02-44-019fcf3a-c74a-7881-bfb6-0510f3b496fb.jsonl` | yes | `codex_app`, `plugin_management` | `capture_screen_context`, `end_realtime_voice_call`, `send_realtime_voice_feedback` | `automation_update`, `create_thread`, `fork_thread`, `get_handoff_status`, `handoff_thread`, `list_projects`, `list_threads`, `load_workspace_dependencies`, `navigate_to_codex_page`, `open_in_codex`, `read_thread`, `read_thread_terminal`, `send_message_to_thread`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title`, `uninstall_plugin`, `wait_threads` | `exec`, `send_message`, `wait` |
| `codex:2026\08\04\rollout-2026-08-04T19-03-55-019fcf3b-dd06-7912-b2b4-39656bca996e.jsonl` | yes | `codex_app`, `plugin_management` | `capture_screen_context`, `end_realtime_voice_call`, `send_realtime_voice_feedback` | `automation_update`, `create_thread`, `fork_thread`, `get_handoff_status`, `handoff_thread`, `list_projects`, `list_threads`, `load_workspace_dependencies`, `navigate_to_codex_page`, `open_in_codex`, `read_thread`, `read_thread_terminal`, `send_message_to_thread`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title`, `uninstall_plugin`, `wait_threads` | `exec`, `wait` |
| `codex:2026\08\04\rollout-2026-08-04T19-23-07-019fcf4d-7493-7ae3-a659-f8976924f13c.jsonl` | yes | `codex_app`, `plugin_management` | `capture_screen_context`, `end_realtime_voice_call`, `send_realtime_voice_feedback` | `automation_update`, `create_thread`, `fork_thread`, `get_handoff_status`, `handoff_thread`, `list_projects`, `list_threads`, `load_workspace_dependencies`, `navigate_to_codex_page`, `open_in_codex`, `read_thread`, `read_thread_terminal`, `send_message_to_thread`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title`, `uninstall_plugin`, `wait_threads` | `exec` |
| `codex:2026\08\04\rollout-2026-08-04T19-56-23-019fcf6b-e6c8-7b23-b528-4ba2cf9266b9.jsonl` | yes | `codex_app`, `plugin_management` | `capture_screen_context`, `end_realtime_voice_call`, `send_realtime_voice_feedback` | `automation_update`, `create_thread`, `fork_thread`, `get_handoff_status`, `handoff_thread`, `list_projects`, `list_threads`, `load_workspace_dependencies`, `navigate_to_codex_page`, `open_in_codex`, `read_thread`, `read_thread_terminal`, `send_message_to_thread`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title`, `uninstall_plugin`, `wait_threads` | `exec`, `send_message`, `wait` |
| `codex:2026\08\04\rollout-2026-08-04T20-12-23-019fcf7a-8c8b-75f1-8bd5-726336ffff7c.jsonl` | yes | `codex_app`, `plugin_management` | `capture_screen_context`, `end_realtime_voice_call`, `send_realtime_voice_feedback` | `automation_update`, `create_thread`, `fork_thread`, `get_handoff_status`, `handoff_thread`, `list_projects`, `list_threads`, `load_workspace_dependencies`, `navigate_to_codex_page`, `open_in_codex`, `read_thread`, `read_thread_terminal`, `send_message_to_thread`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title`, `uninstall_plugin`, `wait_threads` | `exec`, `send_message`, `wait` |
| `codex:2026\08\04\rollout-2026-08-04T20-12-40-019fcf7a-d018-7af1-ae91-aee019923df9.jsonl` | yes | `codex_app`, `plugin_management` | `capture_screen_context`, `end_realtime_voice_call`, `send_realtime_voice_feedback` | `automation_update`, `create_thread`, `fork_thread`, `get_handoff_status`, `handoff_thread`, `list_projects`, `list_threads`, `load_workspace_dependencies`, `navigate_to_codex_page`, `open_in_codex`, `read_thread`, `read_thread_terminal`, `send_message_to_thread`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title`, `uninstall_plugin`, `wait_threads` | `exec`, `send_message`, `wait` |
| `codex:2026\08\04\rollout-2026-08-04T20-15-16-019fcf7d-3291-7011-a9f3-04092bf9eae0.jsonl` | yes | `codex_app`, `plugin_management` | `capture_screen_context`, `end_realtime_voice_call`, `send_realtime_voice_feedback` | `automation_update`, `create_thread`, `fork_thread`, `get_handoff_status`, `handoff_thread`, `list_projects`, `list_threads`, `load_workspace_dependencies`, `navigate_to_codex_page`, `open_in_codex`, `read_thread`, `read_thread_terminal`, `send_message_to_thread`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title`, `uninstall_plugin`, `wait_threads` | `exec`, `send_message`, `wait` |
| `codex:2026\08\04\rollout-2026-08-04T20-24-39-019fcf85-c7f5-7772-8e04-cc199c2c1371.jsonl` | yes | `codex_app`, `plugin_management` | `capture_screen_context`, `end_realtime_voice_call`, `send_realtime_voice_feedback` | `automation_update`, `create_thread`, `fork_thread`, `get_handoff_status`, `handoff_thread`, `list_projects`, `list_threads`, `load_workspace_dependencies`, `navigate_to_codex_page`, `open_in_codex`, `read_thread`, `read_thread_terminal`, `send_message_to_thread`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title`, `uninstall_plugin`, `wait_threads` | `exec`, `github.fetch_issue`, `send_message`, `wait` |
| `codex:2026\08\04\rollout-2026-08-04T20-24-54-019fcf86-053c-72d0-afa7-72489b0df420.jsonl` | yes | `codex_app`, `plugin_management` | `capture_screen_context`, `end_realtime_voice_call`, `send_realtime_voice_feedback` | `automation_update`, `create_thread`, `fork_thread`, `get_handoff_status`, `handoff_thread`, `list_projects`, `list_threads`, `load_workspace_dependencies`, `navigate_to_codex_page`, `open_in_codex`, `read_thread`, `read_thread_terminal`, `send_message_to_thread`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title`, `uninstall_plugin`, `wait_threads` | `exec` |
| `codex:2026\08\04\rollout-2026-08-04T20-50-24-019fcf9d-5dbd-7de0-98ba-219407bfc173.jsonl` | yes | `codex_app`, `plugin_management` | `capture_screen_context`, `end_realtime_voice_call`, `send_realtime_voice_feedback` | `automation_update`, `create_thread`, `fork_thread`, `get_handoff_status`, `handoff_thread`, `list_projects`, `list_threads`, `load_workspace_dependencies`, `navigate_to_codex_page`, `open_in_codex`, `read_thread`, `read_thread_terminal`, `send_message_to_thread`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title`, `uninstall_plugin`, `wait_threads` | `exec`, `github.fetch_issue`, `github.fetch_issue_comments`, `send_message`, `wait` |
| `codex:2026\08\04\rollout-2026-08-04T21-00-36-019fcfa6-b0d5-73d3-8024-65b91f8517ce.jsonl` | yes | `codex_app`, `plugin_management` | `capture_screen_context`, `end_realtime_voice_call`, `send_realtime_voice_feedback` | `automation_update`, `create_thread`, `fork_thread`, `get_handoff_status`, `handoff_thread`, `list_projects`, `list_threads`, `load_workspace_dependencies`, `navigate_to_codex_page`, `open_in_codex`, `read_thread`, `read_thread_terminal`, `send_message_to_thread`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title`, `uninstall_plugin`, `wait_threads` | `exec` |
| `codex:2026\08\05\rollout-2026-08-05T17-09-28-019fd3f9-72aa-7571-b1ba-8a60003d582d.jsonl` | yes | `codex_app`, `plugin_management` | `capture_screen_context`, `end_realtime_voice_call`, `send_realtime_voice_feedback` | `automation_update`, `create_thread`, `fork_thread`, `get_handoff_status`, `handoff_thread`, `list_projects`, `list_threads`, `load_workspace_dependencies`, `navigate_to_codex_page`, `open_in_codex`, `read_thread`, `read_thread_terminal`, `send_message_to_thread`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title`, `uninstall_plugin`, `wait_threads` | `exec`, `followup_task`, `list_agents`, `send_message`, `spawn_agent`, `wait_agent` |
| `codex:2026\08\05\rollout-2026-08-05T17-10-22-019fd3fa-4691-7693-8c7b-cd0cbd9fb474.jsonl` | yes | `codex_app`, `plugin_management` | `capture_screen_context`, `end_realtime_voice_call`, `send_realtime_voice_feedback` | `automation_update`, `create_thread`, `fork_thread`, `get_handoff_status`, `handoff_thread`, `list_projects`, `list_threads`, `load_workspace_dependencies`, `navigate_to_codex_page`, `open_in_codex`, `read_thread`, `read_thread_terminal`, `send_message_to_thread`, `set_thread_archived`, `set_thread_pinned`, `set_thread_title`, `uninstall_plugin`, `wait_threads` | `exec`, `followup_task`, `github.fetch_issue`, `github.fetch_issue_comments`, `interrupt_agent`, `list_agents`, `send_message`, `spawn_agent`, `wait_agent` |

## Dependency warnings

No known dependency separations were detected.

## Strongest tool relationships

| Tool A | Tool B | Affinity | Jaccard | Overlap | Adjacent calls |
|---|---|---:|---:|---:|---:|
| `github.create_issue` | `github.search_prs` | 0.991 | 1.000 | 1.000 | 16 |
| `github.fetch_issue` | `github.fetch_issue_comments` | 0.983 | 0.970 | 1.000 | 55 |
| `github.fetch_pr` | `github.fetch_pr_patch` | 0.942 | 0.957 | 1.000 | 17 |
| `github.fetch_file` | `github.list_pr_changed_filenames` | 0.931 | 0.875 | 1.000 | 34 |
| `github.list_pull_request_review_threads` | `github.list_pull_request_reviews` | 0.908 | 0.833 | 1.000 | 7 |
| `github.fetch_pr_comments` | `github.fetch_pr_patch` | 0.893 | 0.870 | 0.952 | 18 |
| `github.add_review_to_pr` | `github.reply_to_review_comment` | 0.891 | 0.875 | 0.933 | 13 |
| `github.add_issue_assignees` | `github.get_user_login` | 0.891 | 1.000 | 1.000 | 3 |
| `github.fetch_pr_patch` | `github.search_prs` | 0.875 | 0.773 | 1.000 | 29 |
| `github.add_comment_to_issue` | `github.fetch_file` | 0.871 | 0.833 | 0.938 | 14 |
| `github.add_comment_to_issue` | `github.fetch_pr_comments` | 0.869 | 0.810 | 1.000 | 14 |
| `spawn_agent` | `wait_agent` | 0.839 | 0.750 | 0.923 | 109 |
| `github.fetch_pr` | `github.fetch_pr_comments` | 0.838 | 0.913 | 1.000 | 5 |
| `github.create_issue` | `github.fetch_file` | 0.818 | 0.941 | 1.000 | 0 |
| `github.fetch_file` | `github.search_prs` | 0.818 | 0.941 | 1.000 | 0 |
| `github.fetch_file` | `github.fetch_pr` | 0.814 | 0.696 | 1.000 | 14 |
| `list_agents` | `wait_agent` | 0.809 | 0.677 | 0.955 | 141 |
| `github.fetch_file` | `github.fetch_pr_comments` | 0.806 | 0.682 | 0.938 | 24 |
| `followup_task` | `wait_agent` | 0.798 | 0.633 | 1.000 | 132 |
| `github.add_comment_to_issue` | `github.reply_to_review_comment` | 0.795 | 0.882 | 1.000 | 1 |
| `github.fetch_file` | `github.reply_to_review_comment` | 0.777 | 0.722 | 0.867 | 12 |
| `github.fetch_issue` | `github.fetch_pr_patch` | 0.776 | 0.618 | 0.955 | 81 |
| `github.fetch_pr_comments` | `github.search_prs` | 0.773 | 0.652 | 0.882 | 43 |
| `exec` | `send_message` | 0.770 | 0.589 | 0.988 | 219 |
| `github.fetch_issue` | `github.fetch_pr_comments` | 0.759 | 0.588 | 0.952 | 39 |
| `github.create_issue` | `github.list_pr_changed_filenames` | 0.753 | 0.824 | 1.000 | 0 |
| `github.list_pr_changed_filenames` | `github.search_prs` | 0.753 | 0.824 | 1.000 | 0 |
| `github.add_review_to_pr` | `github.fetch_pr_patch` | 0.735 | 0.609 | 0.933 | 12 |
| `followup_task` | `spawn_agent` | 0.726 | 0.731 | 1.000 | 3 |
| `github.add_review_to_pr` | `github.list_pr_changed_filenames` | 0.725 | 0.812 | 0.929 | 0 |

## Caveats

- Historical co-usage is evidence of operational coupling, not proof that tools belong in the same agent.
- This script does not measure task correctness or success directly; quality preservation still requires empirical A/B or replay evaluation.
- Tool-definition token costs are exact only when supplied explicitly with --tool-costs. Telemetry-recovered costs use a chars/4 approximation.
- The known-token calculation excludes unknown tool-definition costs; scenario estimates use a global resolved-definition distribution for unresolved observed tools.
- A zero delegation-overhead setting is a lower-bound estimate, not a claim that delegation is free.
- Direct exposure, inferred baseline exposure, and actual calls are separate evidence dimensions; observed-only is an oracle lower bound and should not judge specialization.
- The all-runtime and provider-scoped results are counterfactual baseline assumptions, not observed exposure claims.
- Provider-scoped exposure requires explicit provider availability telemetry; calls and absent calls do not establish availability.
