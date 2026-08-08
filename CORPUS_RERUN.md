# Real corpus rerun

This record captures the reproducible real-corpus run for issue #11. The full
machine-readable report and architecture manifest are generated locally under
`scripts/agent_tool_analysis/` and remain ignored because the JSON report is
large and contains session-level diagnostics. Re-running the command below
regenerates them.

## Reproduction

Run from the repository's `scripts` directory:

```text
rtk python -m optimize_agent_tools --codex-sessions-dir "$env:USERPROFILE\.codex\sessions" --vscode-workspace-storage "$env:APPDATA\Code\User\workspaceStorage" --output-dir agent_tool_analysis --nmf-max-factors 4 --nmf-seeds 0,1,2 --freshness-half-life-days 30 --freshness-current-window-days 90 --freshness-trial-window-days 14
```

Inputs discovered by this run:

- Codex telemetry: `%USERPROFILE%\.codex\sessions`
- VS Code workspace telemetry: `%APPDATA%\Code\User\workspaceStorage`
- Sources: Codex only; no VS Code sessions contributed to this run
- Run configuration: freshness half-life 30 days, current window 90 days,
  trial window 14 days, NMF factors 1–4, seeds 0/1/2, 160 iterations

## Results

### Corpus and roles

- 143 sessions analyzed; 141 contained calls.
- 6,370 calls across 53 unique tools.
- 24 of 53 tool definitions were resolved; all 29 called tools remained
  unresolved by the local definition registry.
- Role classification separated 2 delegation tools, 5 coordination tools, and
  1 runtime-infrastructure tool. Control-plane calls were retained for impact
  measurement but excluded from the workload matrix and affinity clustering.
- Control-plane impact: 293 delegation calls and 1,983 coordination calls.

### NMF screening and communities

- Matrix: 141 sessions × 16 domain tools using
  `freshness_weighted_session_usage`.
- Factors evaluated: 1, 2, 3, and 4; selected screening factor count: 3.
- No factor count met the configured plausibility criteria.
- The only strong NMF community was
  `github.list_pr_changed_filenames` (a singleton).
- Fifteen GitHub tools were classified as ambiguous/cross-loading and shared
  candidates, so NMF did not establish stable multi-tool ownership.

### Search-unit reduction and representation mismatch

The staged search represented 21 dependency units at every stage:

| Stage | Effective units |
|---|---:|
| Before screening | 21 |
| After NMF screening/freeze | 21 |
| After refinement | 21 |

The screening/search mismatch is therefore explicit: NMF produced one soft
singleton unit and no reduction, while partition search retained all 21
dependency-closed units. Hard dependency units were not replaced by NMF
communities, and refinement restored the original units.

Partition search was bounded (`search_complete: false`) and produced no
cost-complete empirical Pareto architecture under the `observed_only` exposure
model. The provisional two-agent option remains directional only.

### Topology candidates

Topology discovery reported these hypotheses:

| Topology | Score |
|---|---:|
| `flat` | 81.8% |
| `peer` | 18.2% |
| `coordinator_children` | 0.0% |

The current best hypothesis is `flat` with high confidence. Evidence included
293 delegation events, 15 return-to-caller events, 26 delegation sessions,
100.0% origin symmetry, and 2.0% activation asymmetry. These remain structural
hypotheses because telemetry does not identify nested agent roles.

### GitHub-heavy structure

The legacy affinity clustering did find a GitHub-heavy structure without
forcing it:

- `cluster_01`: 12 GitHub issue/PR/file/review tools, 99.3% session coverage,
  0.666 internal affinity, and 0.393 mean boundary margin.
- `cluster_02`: 4 GitHub identity/review-metadata tools, 8.5% session coverage,
  0.643 internal affinity, and 0.112 mean boundary margin.

This split is evidence for a provisional specialization hypothesis, not proof
of agent boundaries. The stronger NMF result is cross-loading rather than
stable multi-tool communities.

## Generated evidence

After the run, inspect:

- `scripts/agent_tool_analysis/agent_tool_analysis.md`
- `scripts/agent_tool_analysis/agent_tool_analysis.json`
- `scripts/agent_tool_analysis/architecture_manifest.json`

These files are ignored by `scripts/.gitignore`; this checked-in summary keeps
the run parameters and acceptance evidence reviewable without committing the
large session-level JSON artifact.