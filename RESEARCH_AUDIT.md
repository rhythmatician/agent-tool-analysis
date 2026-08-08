# Research claim triage

The supplied `tmp/research.md` contains citation placeholders such as `[cite:
1, 15]`, but no bibliography, URLs, paper titles, authors, or runtime/model
identifiers that can be checked. The table therefore records what is currently
supported by the supplied artifact; it does not treat the claims as verified.

| Claim | Exact source in supplied audit | What is demonstrated here | Model/runtime/version | Setup/effect size | Generalizes to this project? | Verdict |
|---|---|---|---|---|---|---|
| Dynamic retrieval: 93.1% vs 87.1% | No resolvable source; number appears in audit prose only | A numerical claim is asserted, but no experiment or denominator is supplied | Missing | Missing | Cannot assess task/tool similarity | Unverified |
| Dynamic retrieval: ~7x context reduction | No resolvable source; number appears in audit prose only | A ratio is asserted, but token accounting and baseline are absent | Missing | Missing | Cannot assess schema/runtime applicability | Unverified |
| Claude/tool-search mechanics | No URL or document citation | The audit names tool-search concepts | Claude version and API mode missing | No request examples or measurements | Requires a controlled runtime capture | Plausible topic, unverified details |
| Prompt-cache behavior under dynamic tools | No URL or document citation | The audit asserts prefix-cache preservation | Provider/model/version missing | No cache-hit metadata or paired requests | Must be measured at the API boundary | Unverified |
| 250–500 / 500–1000 token handoff estimates | No resolvable source; estimates appear in audit prose | Estimates are presented without observed payloads | Missing | No message samples or tokenization method | Runtime- and prompt-dependent | Assumption only |
| 150–350 tokens per tool | No resolvable source; estimate appears in audit prose | A cost range is asserted | Missing | No serialized schemas or tokenizer | Tool-definition dependent | Assumption only |
| Pairwise projection loses hyperedge information | No paper or experiment citation | This is a representation argument, not evidence in the supplied audit | Missing | No corpus comparison | Testable on the existing corpus | Hypothesis |
| Claimed N=30/100/500 thresholds | No resolvable source; thresholds appear in audit prose | Thresholds are asserted without benchmark curves | Missing | No runtime, graph density, or timing data | Likely workload-dependent | Unverified |
| Python/Rust performance claims | No resolvable source or benchmark | Language-level performance is asserted | Missing | No benchmark harness or hardware | Cannot transfer without workload details | Unverified |
| Historical logs lack complete schemas | Local project evidence in `agent_tool_analysis` and telemetry model | The project explicitly represents unresolved definition costs and missing exposure | Local VS Code/Codex telemetry; versions vary | 24/53 recoverable is asserted in audit, but raw provenance is not attached here | Directly relevant to this project | Supported as a project risk; exact rate needs artifact provenance |

The next evidence step is the controlled measurement protocol in
`MEASUREMENT.md`. It records provider-reported input/cache tokens where
available, schema payload measurements where inspectable, selected tools,
latency, success, and quality for paired tool surfaces. No dynamic-retrieval
conclusion or hypergraph migration follows from this table.