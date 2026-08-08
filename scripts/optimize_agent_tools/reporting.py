"""Markdown and console presentation for agent tool analysis reports."""

from __future__ import annotations

from typing import Any, Iterable

from .cost_evaluation import COST_SCENARIOS
from .exposure_models import EXPOSURE_MODEL_DESCRIPTIONS, EXPOSURE_MODELS


def format_tools(values: Iterable[str]) -> str:
    return ", ".join(f"`{value}`" for value in values) or "none"


def _number(value: Any, suffix: str = "") -> str:
    if value is None:
        return "unavailable"
    return f"{value:.1%}" if suffix == "%" else f"{value:.1f}{suffix}"


def _append_table(
    lines: list[str], headers: str, separator: str, rows: Iterable[str]
) -> None:
    lines.extend([headers, separator, *rows, ""])


def render_markdown(report: dict[str, Any]) -> str:
    pruned = report["pruned_flat_baseline"]
    specialist = report.get("specialist_recommendation")
    lines = [
        "# Agent Tool Exposure Analysis",
        "",
        "This report is advisory. No agent configuration was modified.",
        "",
        "## Recommendation",
        "",
        f"**{pruned['recommendation']['headline']}**",
        "",
        f"- Observed dead-tool savings: {pruned['observed_exposure_tokens_removed_per_session']['mid']:.1f} known tool-definition tokens/session",
        f"- Catalog tokens removed: {pruned['catalog_tokens_removed']['mid']:.1f}",
        f"- Catalog-only safe candidates: {len(pruned['catalog_only_tools_removed'])} tools; exposure benefit unmeasured",
        f"- Unresolved retained runtime-tool exposure: {pruned['unresolved_retained_runtime_tool_exposure']['status']}",
        "",
        "## Specialist recommendation",
        "",
    ]
    topology = report.get("topology_discovery")
    if topology:
        best = topology["best_candidate"]
        evidence = topology["evidence"]
        lines.extend(
            [
                "## Topology discovery",
                "",
                f"- Best current topology hypothesis: `{best['topology']}` ({best['score']:.1%}; confidence `{best['confidence']}`)",
                f"- Delegation events: {evidence['delegation_events']}; return-to-caller events: {evidence['return_to_caller_events']}",
                f"- Origin symmetry: {evidence['origin_symmetry']:.1%}; activation asymmetry: {evidence['activation_asymmetry']:.1%}",
                "- Candidates: "
                + ", ".join(
                    f"`{candidate['topology']}` ({candidate['score']:.1%})"
                    for candidate in topology["candidates"]
                ),
                "",
            ]
        )
    if specialist is None:
        lines.extend(["Partition search was not included in this report.", ""])
    else:
        search_status = (
            "complete"
            if specialist["search_complete"]
            else "bounded; the full partition space was not evaluated"
        )
        offline_replay = report.get("offline_replay") or {}
        if offline_replay.get("status") == "completed":
            replay_status = (
                f"completed for `{offline_replay.get('candidate_id', 'unknown')}`; "
                f"status is `{specialist.get('evidence_status', 'unknown')}`"
            )
        elif offline_replay.get("status") == "not_run":
            replay_status = "not run; " + "; ".join(offline_replay.get("reasons", []))
        elif offline_replay.get("status") in {"not_configured", "not_requested"}:
            replay_status = "optional advanced validation; not requested"
        elif not specialist["pareto_candidate_ids"]:
            replay_status = "not run; no cost-complete empirical finalist architectures were available"
        else:
            replay_status = "optional advanced validation; not requested"
        lines.extend(
            [
                f"**{specialist['headline']}**",
                "",
                f"- Evidence status: `{specialist.get('evidence_status', 'unknown')}`",
                f"- Recommendation strength: `{specialist.get('status', 'unknown')}`",
                f"- Best current direction: {specialist.get('direction') or 'none'}",
                f"- Confidence: `{specialist.get('confidence', 'unknown')}`",
                f"- Best-guess architecture: `{specialist.get('best_guess_architecture') or 'none'}`",
                "- Why: " + "; ".join(specialist.get("why", [])),
                f"- Required validation: {specialist.get('required_validation', 'unavailable')}",
                f"- Cost-complete empirical Pareto candidates under `{specialist.get('exposure_model', 'observed_only')}`: {', '.join(f'`{candidate}`' for candidate in specialist['pareto_candidate_ids']) or 'none'}",
                f"- Partition search: {search_status}",
                f"- Replay: {replay_status}",
                f"- Frontier kind: `{specialist.get('frontier_kind', 'unknown')}`; directional only: {'yes' if specialist.get('directional_only', True) else 'no'}",
                f"- Exposure evidence sufficient: {'yes' if specialist.get('exposure_evidence_sufficient', False) else 'no'}",
                "- Agent names, responsibilities, and routing are provisional semantic interpretations; this report does not apply configuration.",
                "",
            ]
        )
        alternatives = report.get("runtime_alternatives", [])
        if alternatives:
            lines.extend(
                [
                    "## Runtime alternatives",
                    "",
                    "These alternatives are normalized for comparison only; no winner is selected here.",
                    "",
                    "| Alternative | Supported | Loading | Occupancy | Tokens | Selection | Coordination | Outcomes |",
                    "| --- | --- | --- | --- | --- | --- | --- | --- |",
                ]
            )
            for alternative in alternatives:
                evidence = alternative.get("metric_evidence_status", {})
                supported = alternative.get("supported")
                supported_label = (
                    "yes"
                    if supported is True
                    else "no"
                    if supported is False
                    else "unknown"
                )
                lines.append(
                    "| "
                    + " | ".join(
                        [
                            f"`{alternative['alternative_id']}`",
                            supported_label,
                            str(alternative.get("loading_policy", "unknown")),
                            str(evidence.get("occupancy", "unavailable")),
                            str(evidence.get("tokens", "unavailable")),
                            str(evidence.get("selection", "unavailable")),
                            str(evidence.get("coordination", "unavailable")),
                            str(evidence.get("outcomes", "unavailable")),
                        ]
                    )
                    + " |"
                )
            lines.append("")
        runtime_recommendation = report.get("runtime_recommendation")
        if runtime_recommendation:
            lines.extend(
                [
                    "### Runtime recommendation policy",
                    "",
                    f"- Preferred option: `{runtime_recommendation.get('preferred_option_label') or runtime_recommendation.get('preferred_option') or 'none'}`",
                    f"- Strength: `{runtime_recommendation.get('recommendation_strength', 'none')}`",
                    f"- Runner-up options: {', '.join(f'`{item}`' for item in runtime_recommendation.get('runner_up_options', [])) or 'none'}",
                    "- Why: " + "; ".join(runtime_recommendation.get("why", [])),
                    "- Thresholds: "
                    + ", ".join(
                        f"{key}={value}"
                        for key, value in runtime_recommendation.get(
                            "thresholds", {}
                        ).items()
                        if key != "complexity_order"
                    ),
                    "",
                ]
            )
        options = report.get("architecture_options", [])
        if options:
            lines.extend(
                [
                    "## Architecture options",
                    "",
                    "The evidence does not choose among plausible options. Select one; replay/A-B is an optional advanced follow-up, not part of the normal workflow.",
                    "",
                ]
            )
            for index, option in enumerate(options, start=1):
                lines.extend(
                    [
                        f"### Option {index} — {option['label']}",
                        "",
                        f"- Architecture: `{option['architecture_id']}`",
                        f"- Topology: `{option.get('topology', 'flat')}`; actual agents: {option.get('agent_count', 1)}",
                        f"- Status: `{option['status']}`",
                        f"- Shared tools: {format_tools(option.get('shared_tools', option.get('parent_tools', [])))}",
                        f"- Why choose this: {'; '.join(option['why_choose'])}",
                        f"- Tradeoffs: {'; '.join(option['tradeoffs'])}",
                        f"- Confidence: {option['confidence']}",
                    ]
                )
                for agent in option.get("agents", []):
                    lines.extend(
                        [
                            f"- {agent['name']} (`{agent['agent_id']}`): {format_tools(agent['tools'])}",
                            f"  - Exclusive: {format_tools(agent.get('exclusive_tools', []))}; shared: {format_tools(agent.get('shared_tools', []))}",
                            f"  - Role: {agent['role']}",
                            f"  - Description: {agent['description']}",
                        ]
                    )
                lines.append("")
    lines.extend(
        [
            "## Corpus",
            "",
            f"- Sessions analyzed: {report['corpus']['sessions']}",
        ]
    )
    for key in (
        "sessions_total",
        "sessions_with_calls",
        "sessions_with_direct_exposure",
        "sessions_with_calls_and_exposure",
        "sessions_with_calls_without_exposure",
        "sessions_with_exposure_without_calls",
    ):
        lines.append(f"- {key}: {report['corpus'][key]}")
    lines.extend(
        [
            f"- Tool calls: {report['corpus']['tool_calls']}",
            f"- Unique tools: {report['corpus']['unique_tools']}",
            "- Sources: "
            + ", ".join(
                f"{name}={count}" for name, count in report["corpus"]["sources"].items()
            ),
            "",
            "## Definition resolution",
            "",
        ]
    )
    _append_table(
        lines,
        "| Observed tool | Calls | Sessions called | Resolved | Source | Estimated tokens | Evidence |",
        "|---|---:|---:|---|---|---:|---|",
        (
            f"| `{row['observed_tool']}` | {row['calls']} | {row['sessions_called']} | "
            f"{'yes' if row['definition_resolved'] else 'no'} | `{row['definition_source'] or 'unresolved'}` | "
            f"{row['estimated_tokens'] if row['estimated_tokens'] is not None else 'unknown'} | {row['evidence_type']} |"
            for row in report["definition_resolution"]
        ),
    )

    measurement = report.get("measurement_completeness")
    if measurement is not None:
        exposure = measurement["exposure_evidence"]
        retained = measurement["cost_completeness"]
        lines.extend(
            [
                "## Measurement completeness",
                "",
                f"- Frontier kind: `{measurement['frontier_kind']}`",
                f"- Directional only: {'yes' if measurement['directional_only'] else 'no'}",
                f"- Exposure evidence sufficient for an empirical frontier: {'yes' if measurement['exposure_evidence_sufficient'] else 'no'}",
                f"- Call-bearing sessions without direct exposure: {exposure['call_bearing_sessions_without_direct_exposure']}/{exposure['call_bearing_sessions']}",
                f"- Retained baseline exact definition costs: {retained['tools_with_exact_cost']}/{retained['tools_total']}",
                f"- Retained baseline cost status: `{retained['status']}`",
                "- Calls are never used as exposure evidence; recovered chars/4 costs remain estimates.",
                "",
            ]
        )

    nmf = report.get("nmf_screening")
    if nmf:
        hints = nmf.get("search_hints", {})
        lines.extend(
            [
                "## NMF workload screening",
                "",
                "NMF factors are screening signals, not agents or irreversible ownership assignments.",
                f"- Domain matrix: {nmf.get('matrix', {}).get('rows', 0)} sessions × {nmf.get('matrix', {}).get('columns', 0)} tools ({nmf.get('matrix', {}).get('mode', 'unknown')})",
                f"- Delegation/coordination tools excluded from the domain matrix: {nmf.get('control_plane', {}).get('control_plane_tool_count', 0)}",
                f"- Runtime-infrastructure tools excluded from the domain matrix: {nmf.get('control_plane', {}).get('runtime_infrastructure_tool_count', 0)}",
                f"- Factor counts evaluated: {format_tools(nmf.get('factor_counts', []))}",
                f"- Selected screening factor count: {nmf.get('selected_factor_count', 'none')} (not final agent count)",
                f"- Plausible factor counts: {format_tools(hints.get('plausible_factor_counts', []))}",
                f"- Strong communities: {'; '.join(format_tools(item.get('tools', [])) for item in hints.get('strong_communities', [])) or 'none'}",
                f"- Ambiguous/cross-loading tools: {format_tools(hints.get('ambiguous_tools', []))}",
                f"- Shared candidates: {format_tools(hints.get('shared_candidates', []))}",
                f"- Search units: {len(hints.get('search_units', []))} soft units; dependencies remain hard locks and soft units are refined later",
                "",
            ]
        )

    partition_search = report.get("partition_search", {}).get("search")
    if partition_search:
        stage_summary = ", ".join(
            f"{stage['name']} ({stage['effective_search_units']})"
            for stage in partition_search.get("stages", [])
        )
        lines.extend(
            [
                "## Staged partition search",
                "",
                f"- Effective units before screening: {partition_search.get('search_units_before_screening', 0)}",
                f"- Effective units after NMF screening/freeze: {partition_search.get('search_units_after_screening', 0)}",
                f"- Effective units after refinement: {partition_search.get('search_units_after_refinement', 0)}",
                f"- Search stages: {stage_summary}",
                "",
            ]
        )

    freshness = report.get("freshness")
    if freshness:
        lines.extend(
            [
                "## Freshness and maturity",
                "",
                f"- Exponential half-life: {freshness['config']['half_life_days']:.1f} days",
                f"- Lifetime-required tools (never removed by decay): {format_tools(freshness.get('lifetime_required', []))}",
                f"- Current tools: {format_tools(freshness.get('current', []))}",
                f"- Currently low-frequency tools: {format_tools(freshness.get('currently_low_frequency', []))}",
                f"- Trial MCP tools: {format_tools(freshness.get('trial', []))}",
                f"- Trial workload opportunities: {len(report.get('trial_workload_opportunities', []))}",
                "",
            ]
        )

    discovery = report["definition_discovery"]
    manifest = discovery["runtime_manifest"]
    lines.extend(
        [
            "## Definition discovery",
            "",
            f"- Explicit records: {discovery['explicit_records']}",
            f"- Telemetry records: {discovery['telemetry_records']}",
            f"- Runtime roots scanned: {', '.join(manifest['roots']) or 'none'}",
            f"- Manifest files scanned: {manifest['files_scanned']}",
            f"- Manifest definitions found: {manifest['definitions_found']}",
            "",
            "## Tool inventory",
            "",
        ]
    )
    _append_table(
        lines,
        "| Tool | Directly observed exposure | Used | P(use|exposed) | Calls | Def tokens | Waste/session | Boundary margin | Recommendation |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---|",
        (
            f"| `{tool['name']}` | {tool['sessions_exposed']} | {tool['sessions_called']} | "
            f"{_number(tool['call_given_exposed'], '%')} | {tool['calls']} | "
            f"{tool['definition_tokens'] if tool['definition_tokens'] is not None else 'unknown'} | "
            f"{_number(tool['expected_unused_tokens_per_session'])} | "
            f"{_number(tool['boundary_margin'])} | {tool['classification']} |"
            for tool in report["tools"]
        ),
    )

    lines.extend(["## Candidate specialist agents", ""])
    if not report["candidate_agents"]:
        lines.extend(["No candidate clusters met the configured thresholds.", ""])
    else:
        for agent in report["candidate_agents"]:
            lines.extend(
                [
                    f"### {agent['candidate_id']} ({len(agent['tools'])} tools, {agent['session_coverage_rate']:.1%} session coverage)",
                    "",
                    f"- Internal affinity: {agent['internal_affinity']:.3f}",
                    f"- Known definition tokens isolated: {agent['known_definition_tokens']}",
                    f"- Tools: {format_tools(agent['tools'])}",
                    "",
                ]
            )

    lines.extend(["## Cluster boundaries", ""])
    _append_table(
        lines,
        "| Cluster | Internal affinity | Max external affinity | Mean boundary margin | Session coverage | Exclusive coverage | Overlapping coverage |",
        "|---|---:|---:|---:|---:|---:|---:|",
        (
            f"| `{cluster['cluster_id']}` | {cluster['internal_affinity']:.3f} | {cluster['max_external_affinity']:.3f} | "
            f"{cluster['mean_boundary_margin']:.3f} | {cluster['session_coverage']:.1%} | "
            f"{cluster['exclusive_session_coverage']:.1%} | {cluster['overlapping_session_coverage']:.1%} |"
            for cluster in report["clusters"]
        ),
    )

    overhead = report["overhead"]
    coverage = overhead["known_cost_coverage"]
    lines.extend(
        [
            "## Baseline overhead context",
            "",
            f"- Tool-definition cost coverage: {coverage['tools_with_known_cost']}/{coverage['tools_total']} ({coverage['catalog_coverage_rate']:.1%})",
            f"- Observed-tool cost coverage: {coverage['observed_tools_with_known_cost']}/{coverage['observed_tools_total']} ({coverage['observed_tool_coverage_rate']:.1%})",
            f"- Usage-weighted cost coverage: {coverage['calls_with_known_cost']}/{coverage['total_calls']} ({coverage['usage_weighted_coverage_rate']:.1%})",
            f"- Exposure-record cost coverage: {coverage['exposure_weighted_coverage_rate']:.1%}",
            f"- Flat baseline known definition tokens: {overhead['flat_baseline_known_tokens']:.1f}",
            f"- Unassigned known definition tokens after partition: {overhead.get('unassigned_known_tokens_after_partition', overhead.get('parent_known_tokens_after_partition', 0.0)):.1f}",
            f"- Expected known tokens/session after partition: {overhead['expected_known_tokens_per_session_after_partition']:.1f}",
            f"- Expected known-token savings/session: {_number(overhead['expected_known_tokens_saved_per_session'])}",
            f"- Delegation overhead assumption: {overhead['delegation_overhead_tokens_per_activated_specialist']} tokens per activated specialist",
            "",
            overhead["interpretation"],
            "",
            "## Baseline exposure models",
            "",
            "Direct exposure is telemetry evidence. Inferred exposure is a labeled counterfactual assumption and is never derived from calls in the same session.",
            "",
        ]
    )
    _append_table(
        lines,
        "| Model | Description | Runtime catalog | Sessions with inferred exposure | Inferred exposure rows | Sessions with provider availability |",
        "|---|---|---:|---:|---:|---:|",
        (
            f"| `{model['model']}` | {model['description']} | {model['runtime_tool_catalog_size']} | "
            f"{model['sessions_with_inferred_exposure']} | {model['inferred_exposure_rows']} | {model['sessions_with_provider_availability']} |"
            for model in report["exposure_models"]
        ),
    )

    lines.extend(
        [
            "## Independent architecture variants",
            "",
            "Variants are ranked by mid-case relative reduction; negative values are reported, not selected away.",
            "",
        ]
    )
    lines.extend(
        [
            "## Pruned flat baseline",
            "",
            "The flat parent retains every historically used tool plus recursively required dependencies.",
            f"**Recommendation: {pruned['recommendation']['headline']}**",
            "",
            f"- Tools removed: {format_tools(pruned['tools_removed'])}",
            f"- Tools retained: {format_tools(pruned['tools_retained'])}",
            f"- Historical called-tool coverage: {pruned['historical_called_tool_coverage']:.1%}",
            f"- Dependency-preservation warnings: {pruned['dependency_preservation_warnings'] or 'none'}",
            f"- Directly observed, never-used tools removed: {format_tools(pruned['directly_observed_never_used_tools_removed'])}",
            f"- Catalog-only tools removed: {format_tools(pruned['catalog_only_tools_removed'])}",
            f"- Unresolved retained runtime-tool exposure: {pruned['unresolved_retained_runtime_tool_exposure']['status']} ({pruned['unresolved_retained_runtime_tool_exposure']['tool_count']} tools)",
            "",
        ]
    )
    _append_table(
        lines,
        "| Scenario | Catalog tokens removed | Observed exposure removed/session | Baseline before pruning | Baseline after pruning | Relative reduction |",
        "|---|---:|---:|---:|---:|---:|",
        (
            f"| {scenario} | {_number(pruned['catalog_tokens_removed'][scenario])} | "
            f"{_number(pruned['observed_exposure_tokens_removed_per_session'][scenario])} | "
            f"{_number(pruned['baseline_tokens_per_session_before_pruning'][scenario])} | "
            f"{_number(pruned['baseline_tokens_per_session_after_pruning'][scenario])} | "
            f"{_number(pruned['relative_reduction'][scenario], '%')} |"
            for scenario in COST_SCENARIOS
        ),
    )
    lines.extend(
        [
            "Specialist architecture variants below are rebased against `pruned_flat_baseline`.",
            "",
        ]
    )
    for variant in report["architecture_variants"]:
        lines.extend(
            [
                f"### {variant['rank']}. `{variant['variant_id']}`",
                "",
                f"- Baseline architecture: `{variant['baseline_architecture_id']}`",
                f"- Specialist tools: {format_tools(variant['specialist_tools'])}",
                f"- Historical called-tool coverage: {variant['historical_called_tool_coverage_rate']:.1%}",
                f"- Mid-case sensitivity: {_number(variant['sensitivity']['min_mid_reduction'], '%')} to {_number(variant['sensitivity']['max_mid_reduction'], '%')}",
                "",
            ]
        )
        for model in EXPOSURE_MODELS:
            lines.extend(
                [
                    f"#### Exposure model: `{model}`",
                    "",
                    EXPOSURE_MODEL_DESCRIPTIONS[model],
                    "",
                ]
            )
            metrics = variant["scenarios_by_exposure_model"][model]
            _append_table(
                lines,
                "| Metric | Low | Mid | High |",
                "|---|---:|---:|---:|",
                (
                    f"| {label} | "
                    + " | ".join(
                        "unavailable"
                        if metrics[scenario][key] is None
                        else (
                            f"{metrics[scenario][key]:.1%}"
                            if key == "relative_token_reduction"
                            else f"{metrics[scenario][key]:.1f}"
                        )
                        for scenario in COST_SCENARIOS
                    )
                    + " |"
                    for key, label in (
                        ("baseline_tokens_per_session", "Baseline tokens/session"),
                        ("proposed_tokens_per_session", "Proposed tokens/session"),
                        ("absolute_token_reduction_per_session", "Absolute reduction"),
                        ("relative_token_reduction", "Relative reduction"),
                        ("specialist_activation_rate", "Specialist activation rate"),
                    )
                ),
            )

    github = report["github_exposure_sensitivity"]
    lines.extend(["## GitHub exposure sensitivity analysis", ""])
    if github is None:
        lines.extend(["Cluster 1 was not an eligible specialist candidate.", ""])
    else:
        lines.extend(
            [
                "This is diagnostic sensitivity analysis, not reconstructed telemetry. "
                + github["assumption"],
                "",
                f"- Applicable Codex sessions: {github['applicable_session_count']}",
                f"- Historical specialist activation rate: {github['activation_rate']:.1%}",
                f"- Classification: `{github['classification']}`",
                "",
            ]
        )

    subset = report["cluster_one_subset_analysis"]
    lines.extend(["## Cluster 1 exhaustive subset evaluation", ""])
    if subset is None:
        lines.extend(["Cluster 1 was not an eligible specialist candidate.", ""])
    else:
        lines.extend(
            [
                f"Evaluated {subset['subset_count']} subsets containing at least two Cluster 1 tools. Excluded tools remain on the parent.",
                "",
                "### Pareto frontier",
                "",
            ]
        )
        for row in subset["pareto_frontier"]:
            lines.append(
                f"- {format_tools(row['tools'])}: break-even {_number(row['break_even_exposure_rate_mid'], '%')}, definition {_number(row['definition_tokens_mid'])}, activation {row['activation_rate']:.1%}"
            )
        lines.append("")

    decision = report["candidate_decision_table"]
    lines.extend(["## Candidate decision table", ""])
    if decision is None:
        lines.extend(["Cluster 1 candidate decisions are unavailable.", ""])
    else:
        _append_table(
            lines,
            "| Candidate | Type | Tools | Activation | Definition tokens | Affinity | Min boundary | Worst-case reduction | Viable cells |",
            "|---|---|---|---:|---:|---:|---:|---:|---:|",
            (
                f"| `{candidate['candidate_id']}` | {candidate['candidate_type']} | {format_tools(candidate['tools'])} | {candidate['activation_rate']:.1%} | "
                f"{candidate['specialist_definition_tokens']:.1f} | {candidate['internal_affinity']:.3f} | {candidate['minimum_boundary_margin']:.3f} | "
                f"{candidate['worst_case_positive_reduction']:.1f} | {candidate['viable_cells']:.1%} |"
                for candidate in decision["candidates"]
            ),
        )

    provider = report["provider_availability_diagnostics"]
    lines.extend(
        [
            "## Provider availability reconstruction",
            "",
            "Availability and mappings below come only from explicit dynamic-tools groups; runtime calls never establish provider availability.",
            "",
        ]
    )
    _append_table(
        lines,
        "| Provider | Groups observed | Sessions | Advertised tools |",
        "|---|---:|---:|---|",
        (
            f"| `{row['provider']}` | {row['group_count']} | {row['session_count']} | {format_tools(row['tools_advertised'])} |"
            for row in provider["provider_groups_observed"]
        ),
    )
    github_provider = provider["github"]
    lines.extend(
        [
            "### GitHub-specific reconstruction",
            "",
            f"- Advertised GitHub-like tools: {format_tools(github_provider['advertised_github_like_tools'])}",
            f"- Runtime `github.*` tools: {format_tools(github_provider['runtime_github_tools'])}",
            f"- Unresolved mappings: {format_tools(github_provider['unresolved_mappings'])}",
            "",
            "## Provider-scoped session diagnostics",
            "",
        ]
    )
    _append_table(
        lines,
        "| Session | Provider availability observed? | Providers available | Inferred runtime tools | Directly exposed tools | Called tools |",
        "|---|---|---|---|---|---|",
        (
            f"| `{row['session_id']}` | {'yes' if row['provider_availability_observed'] else 'no'} | {format_tools(row['providers_available'])} | "
            f"{format_tools(row['inferred_runtime_tools'])} | {format_tools(row['directly_exposed_tools'])} | {format_tools(row['called_tools'])} |"
            for row in report["provider_scoped_session_diagnostics"]
        ),
    )

    lines.extend(["## Dependency warnings", ""])
    if not report["dependency_warnings"]:
        lines.append("No known dependency separations were detected.")
    else:
        for warning in report["dependency_warnings"]:
            lines.append(
                f"- {warning['candidate_id']}: {warning['missing_dependencies']}"
            )
    lines.extend(["", "## Strongest tool relationships", ""])
    _append_table(
        lines,
        "| Tool A | Tool B | Affinity | Jaccard | Overlap | Adjacent calls |",
        "|---|---|---:|---:|---:|---:|",
        (
            f"| `{pair['tool_a']}` | `{pair['tool_b']}` | {pair['affinity']:.3f} | {pair['jaccard']:.3f} | {pair['overlap']:.3f} | {pair['adjacency_count']} |"
            for pair in report["strongest_pairs"][:30]
        ),
    )
    lines.extend(["## Caveats", "", *(f"- {caveat}" for caveat in report["caveats"])])
    return "\n".join(lines) + "\n"


def print_summary(
    report: dict[str, Any],
    json_path: Any,
    markdown_path: Any,
    manifest_path: Any | None = None,
) -> None:
    corpus = report["corpus"]
    overhead = report["overhead"]
    print("=" * 72)
    print("AGENT TOOL EXPOSURE ANALYSIS")
    print("=" * 72)
    print(f"Sessions analyzed: {corpus['sessions']}")
    print(f"Tool calls:        {corpus['tool_calls']}")
    print(f"Unique tools:      {corpus['unique_tools']}")
    print(f"Clustered tools:   {corpus['active_tools_for_clustering']}")
    print(f"Global candidates: {len(report['global_candidates'])}")
    print(f"Agent candidates:  {len(report['candidate_agents'])}")
    specialist = report.get("specialist_recommendation")
    if specialist is not None:
        print(
            f"Cost-complete empirical Pareto architectures: {len(specialist['pareto_candidate_ids'])}"
            + (
                " (partition search bounded)"
                if not specialist["search_complete"]
                else ""
            )
        )
        option_ids = [
            option["architecture_id"]
            for option in report.get("architecture_options", [])
        ]
        print(
            "Architecture options: " + (", ".join(option_ids) if option_ids else "none")
        )
    coverage = overhead["known_cost_coverage"]
    print(
        f"\nKnown tool-cost coverage: {coverage['tools_with_known_cost']}/{coverage['tools_total']} (catalog {coverage['catalog_coverage_rate']:.1%}, usage-weighted {coverage['usage_weighted_coverage_rate']:.1%})"
    )
    savings = overhead["expected_known_token_savings_rate"]
    print(
        f"Expected known-token savings/session: {overhead['expected_known_tokens_saved_per_session']:.1f} ({savings:.1%})"
        if savings is not None
        else "Expected known-token savings/session: unavailable"
    )
    print(f"\nJSON report:     {json_path.resolve()}")
    print(f"Markdown report: {markdown_path.resolve()}")
    if manifest_path is not None:
        print(f"Architecture manifest: {manifest_path.resolve()}")
    print(
        "\nNext: inspect the architecture options in the Markdown report; replay is optional advanced validation."
    )
