#!/usr/bin/env python3
"""CLI entry point for telemetry-driven agent tool exposure analysis."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from optimize_agent_tools.analysis_pipeline import (
    DEFAULT_GITHUB_EXPOSURE_RATES,
    analyze,
    load_explicit_tool_costs,
)
from optimize_agent_tools.freshness import FreshnessConfig
from optimize_agent_tools.reporting import print_summary
from optimize_agent_tools.telemetry_ingestion import (
    get_codex_sessions,
    get_vscode_sessions,
)

DEFAULT_VSCODE_WORKSPACE_STORAGE = os.path.expanduser(
    r"~\AppData\Roaming\Code\User\workspaceStorage"
)
DEFAULT_CODEX_SESSIONS_DIR = os.path.expanduser(r"~\.codex\sessions")
DEFAULT_CODEX_DEFINITION_ROOTS = tuple(
    path
    for path in (
        os.path.expanduser(r"~\.codex"),
        os.path.expanduser(r"~\.config\codex"),
        os.path.join(os.environ.get("APPDATA", ""), "Codex"),
    )
    if path
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Analyze historical coding-agent tool usage and propose lower-overhead tool exposure."
    )
    parser.add_argument(
        "--vscode-workspace-storage", default=DEFAULT_VSCODE_WORKSPACE_STORAGE
    )
    parser.add_argument("--codex-sessions-dir", default=DEFAULT_CODEX_SESSIONS_DIR)
    parser.add_argument(
        "--tool-costs",
        default=None,
        help="Optional JSON mapping of normalized tool names to token costs.",
    )
    parser.add_argument(
        "--definition-search-root",
        action="append",
        default=[],
        help="Additional runtime/provider root to scan.",
    )
    parser.add_argument("--output-dir", default="agent_tool_analysis")
    parser.add_argument(
        "--offline-replay-input",
        default=None,
        help="Optional recorded replay bundle for explicit advanced validation; never discovered implicitly.",
    )
    parser.add_argument(
        "--offline-replay-candidate",
        default=None,
        help="Architecture option to validate with --offline-replay-input.",
    )
    parser.add_argument("--min-tool-sessions", type=int, default=3)
    parser.add_argument("--similarity-threshold", type=float, default=0.35)
    parser.add_argument("--global-usage-threshold", type=float, default=0.60)
    parser.add_argument("--min-cluster-size", type=int, default=2)
    parser.add_argument("--min-cluster-sessions", type=int, default=3)
    parser.add_argument(
        "--nucleus-threshold",
        type=float,
        default=0.40,
        help="Collapsed canonical session-coverage rate required for the shared nucleus (0 disables coverage-based detection, leaving only coordination tools).",
    )
    parser.add_argument("--delegation-overhead-tokens", type=int, default=0)
    parser.add_argument(
        "--max-agents",
        type=int,
        default=3,
        help="Maximum specialist count to evaluate in the normal recommendation workflow.",
    )
    parser.add_argument(
        "--communication-tokens-per-handoff",
        type=float,
        default=0.0,
        help="Estimated inter-agent communication cost per observed handoff.",
    )
    parser.add_argument(
        "--github-exposure-rates",
        default=",".join(f"{rate:g}" for rate in DEFAULT_GITHUB_EXPOSURE_RATES),
    )
    parser.add_argument("--nmf-max-factors", type=int, default=4)
    parser.add_argument("--nmf-seeds", default="0,1,2")
    parser.add_argument("--nmf-iterations", type=int, default=160)
    parser.add_argument("--freshness-half-life-days", type=float, default=30.0)
    parser.add_argument("--freshness-current-window-days", type=float, default=90.0)
    parser.add_argument("--freshness-trial-window-days", type=float, default=14.0)
    parser.add_argument(
        "--freshness-current-weight-threshold", type=float, default=0.25
    )
    return parser.parse_args()


def _github_rates(raw: str) -> tuple[float, ...]:
    try:
        rates = tuple(float(value.strip()) for value in raw.split(",") if value.strip())
    except ValueError as error:
        raise SystemExit(
            "--github-exposure-rates must be comma-separated numbers"
        ) from error
    if not rates:
        raise SystemExit("--github-exposure-rates must contain at least one rate")
    if any(rate < 0 or rate > 1 for rate in rates):
        raise SystemExit("--github-exposure-rates values must be between 0 and 1")
    return rates


def _validate_args(args: argparse.Namespace, github_rates: tuple[float, ...]) -> None:
    if args.min_tool_sessions < 1:
        raise SystemExit("--min-tool-sessions must be >= 1")
    if not 0 <= args.similarity_threshold <= 1:
        raise SystemExit("--similarity-threshold must be between 0 and 1")
    if not 0 <= args.global_usage_threshold <= 1:
        raise SystemExit("--global-usage-threshold must be between 0 and 1")
    if not 0 <= getattr(args, "nucleus_threshold", 0.40) <= 1:
        raise SystemExit("--nucleus-threshold must be between 0 and 1")
    if args.min_cluster_size < 2:
        raise SystemExit("--min-cluster-size must be >= 2")
    if args.min_cluster_sessions < 1:
        raise SystemExit("--min-cluster-sessions must be >= 1")
    if args.delegation_overhead_tokens < 0:
        raise SystemExit("--delegation-overhead-tokens cannot be negative")
    if args.max_agents < 1:
        raise SystemExit("--max-agents must be >= 1")
    if args.communication_tokens_per_handoff < 0:
        raise SystemExit("--communication-tokens-per-handoff cannot be negative")
    if getattr(args, "nmf_max_factors", 4) < 1:
        raise SystemExit("--nmf-max-factors must be >= 1")
    if getattr(args, "nmf_iterations", 160) < 1:
        raise SystemExit("--nmf-iterations must be >= 1")
    if not github_rates:
        raise SystemExit("--github-exposure-rates must contain at least one rate")
    if args.offline_replay_candidate and not args.offline_replay_input:
        raise SystemExit("--offline-replay-candidate requires --offline-replay-input")
    if args.offline_replay_input and not args.offline_replay_candidate:
        raise SystemExit(
            "--offline-replay-input requires --offline-replay-candidate; choose an architecture option explicitly"
        )
    _freshness_config(args).validate()


def _freshness_config(args: argparse.Namespace) -> FreshnessConfig:
    return FreshnessConfig(
        half_life_days=args.freshness_half_life_days,
        current_window_days=args.freshness_current_window_days,
        trial_window_days=args.freshness_trial_window_days,
        current_weight_threshold=args.freshness_current_weight_threshold,
    )


def _nmf_seeds(raw: str) -> tuple[int, ...]:
    try:
        seeds = tuple(int(value.strip()) for value in raw.split(",") if value.strip())
    except ValueError as error:
        raise SystemExit("--nmf-seeds must be comma-separated integers") from error
    if not seeds:
        raise SystemExit("--nmf-seeds must contain at least one integer")
    return seeds


def main() -> int:
    args = parse_args()
    github_rates = _github_rates(args.github_exposure_rates)
    nmf_seeds = _nmf_seeds(args.nmf_seeds)
    _validate_args(args, github_rates)
    vscode_sessions, vscode_defs = get_vscode_sessions(args.vscode_workspace_storage)
    codex_sessions, codex_defs = get_codex_sessions(args.codex_sessions_dir)
    sessions = vscode_sessions + codex_sessions
    if not sessions:
        raise SystemExit(
            "No tool-using sessions were found. Check --vscode-workspace-storage and --codex-sessions-dir."
        )

    explicit_costs = load_explicit_tool_costs(args.tool_costs)
    report = analyze(
        sessions,
        vscode_defs,
        codex_defs,
        explicit_path=args.tool_costs,
        definition_roots=list(
            dict.fromkeys(
                [*DEFAULT_CODEX_DEFINITION_ROOTS, *args.definition_search_root]
            )
        ),
        min_tool_sessions=args.min_tool_sessions,
        similarity_threshold=args.similarity_threshold,
        global_usage_threshold=args.global_usage_threshold,
        min_cluster_size=args.min_cluster_size,
        min_cluster_sessions=args.min_cluster_sessions,
        delegation_overhead_tokens=args.delegation_overhead_tokens,
        max_agents=args.max_agents,
        communication_tokens_per_handoff=args.communication_tokens_per_handoff,
        github_exposure_rates=github_rates,
        nmf_max_factors=args.nmf_max_factors,
        nmf_seeds=nmf_seeds,
        nmf_iterations=args.nmf_iterations,
        nucleus_threshold=args.nucleus_threshold,
        freshness_config=_freshness_config(args),
    )
    replay_bundle = None
    if args.offline_replay_input:
        replay_input_path = Path(args.offline_replay_input)
        if not replay_input_path.is_file():
            raise SystemExit(
                f"Recorded replay bundle was not found: {replay_input_path}"
            )
        replay_bundle = json.loads(replay_input_path.read_text(encoding="utf-8"))
    report = report.finalize(
        explicit_cost_entries=len(explicit_costs),
        replay_bundle=replay_bundle,
        replay_candidate=args.offline_replay_candidate,
    )
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "agent_tool_analysis.json"
    markdown_path = output_dir / "agent_tool_analysis.md"
    manifest_path = output_dir / "architecture_manifest.json"
    json_path.write_text(
        report.to_json(), encoding="utf-8"
    )
    markdown_path.write_text(report.to_markdown(), encoding="utf-8")
    manifest_path.write_text(
        json.dumps(
            report.serialize()["architecture_manifest"], indent=2, ensure_ascii=False
        ),
        encoding="utf-8",
    )
    print_summary(report, json_path, markdown_path, manifest_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
