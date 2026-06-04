"""Command-line dispatcher for TianGong.

Running ``tiangong-mcp`` with no arguments keeps the existing MCP server behavior.
Subcommands expose launch and growth gates for maintainers who need terminal
runbooks before a public release.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from contextlib import suppress
from typing import TextIO

from .activation import (
    EVENT_ISSUEOPS_REFERRAL_RECORDED,
    EVENT_SHARE_ATTRIBUTION_RECORDED,
    get_activation_event_path,
    load_activation_events,
    public_proof_url_problem,
    record_activation_event,
)
from .banner import append_brand_footer
from .config import config
from .launch_assets import format_public_launch_assets
from .proof_pack import format_public_proof_pack
from .public_growth import (
    fetch_public_growth_snapshot,
    format_public_growth_report,
    format_public_launch_preflight,
    get_public_growth_snapshot_path,
    load_public_growth_snapshots,
    record_public_growth_snapshot,
)
from .release_boundary import format_public_release_boundary


def _positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a positive integer") from exc
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return parsed


def _non_negative_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a non-negative integer") from exc
    if parsed < 0:
        raise argparse.ArgumentTypeError("must be a non-negative integer")
    return parsed


def _clean_cli_text(value: str, fallback: str = "") -> str:
    text = " ".join(str(value or "").split())[:240]
    return text or fallback


def _default_actor(value: str) -> str:
    return _clean_cli_text(value, config.GITHUB_USERNAME or "anonymous")


def _format_cli_url_rejection(
    *,
    title: str,
    problem: str,
    field_name: str,
    value: str,
    retry_command: str,
) -> str:
    return append_brand_footer(
        "\n".join(
            [
                f"# {title}",
                "",
                f"> {problem}",
                f"> Rejected `{field_name}`: {value or 'missing'}",
                "> No local activation ledger event was written.",
                "> Use the created public post/Issue/PR/Discussion URL after submission; do not use issues/new form entrypoints or placeholder URLs.",
                "> This command does not invent downloads, retention, repost counts, referral conversions, or rewards.",
                "",
                "## Retry Command",
                "",
                f"- `{retry_command}`",
                "",
                "## Recheck Commands",
                "",
                "- MCP activation report: `activation_funnel()`",
                "- MCP growth flywheel: `growth_flywheel()`",
                "- Terminal proof pack: `tiangong-mcp public-proof-pack --target-contributors 10`",
                "- Terminal preflight: `tiangong-mcp public-launch-preflight --target-contributors 10`",
            ]
        )
    )


def _format_cli_write_failure(
    *,
    title: str,
    public_url: str,
    error: str,
    retry_command: str,
) -> str:
    return append_brand_footer(
        "\n".join(
            [
                f"# {title}",
                "",
                f"> Public proof URL: {public_url}",
                f"> Local activation ledger write failed: {error}",
                "> No local activation ledger event was written.",
                "> This command does not invent downloads, retention, repost counts, referral conversions, or rewards.",
                "",
                "## Recovery",
                "",
                "- Fix the local log directory permissions or configure a writable `TIANGONG_CAVE_DIR`, then retry.",
                f"- Retry: `{retry_command}`",
                "- Recheck activation after a successful write: `activation_funnel()`",
                "- Recheck growth after a successful write: `growth_flywheel()`",
            ]
        )
    )


def _run_mcp_server() -> None:
    from .mcp_server import main as run_server

    run_server()


def _configure_text_stream(stream: TextIO) -> TextIO:
    reconfigure = getattr(stream, "reconfigure", None)
    if callable(reconfigure):
        with suppress(AttributeError, OSError, ValueError):
            reconfigure(encoding="utf-8", errors="replace")
    return stream


def _format_public_launch_preflight_command(args: argparse.Namespace) -> str:
    event_path = get_activation_event_path()
    events = load_activation_events(path=event_path)
    try:
        snapshot = fetch_public_growth_snapshot()
    except Exception as exc:
        return append_brand_footer(
            format_public_launch_preflight(
                None,
                activation_events=events,
                source_path=event_path,
                target_contributors=args.target_contributors,
                fetch_error=str(exc),
            )
        )
    return append_brand_footer(
        format_public_launch_preflight(
            snapshot,
            activation_events=events,
            source_path=event_path,
            target_contributors=args.target_contributors,
        )
    )


def _format_public_growth_report_command(args: argparse.Namespace) -> str:
    event_path = get_activation_event_path()
    events = load_activation_events(path=event_path)
    history_path = get_public_growth_snapshot_path()
    history = load_public_growth_snapshots(path=history_path)
    try:
        snapshot = fetch_public_growth_snapshot()
    except Exception as exc:
        return append_brand_footer(
            format_public_growth_report(
                None,
                activation_events=events,
                source_path=event_path,
                history=history,
                history_path=history_path,
                target_contributors=args.target_contributors,
                fetch_error=str(exc),
            )
        )

    snapshot_recorded = False
    if args.record_snapshot:
        record_public_growth_snapshot(snapshot, activation_events=events, path=history_path)
        snapshot_recorded = True

    return append_brand_footer(
        format_public_growth_report(
            snapshot,
            activation_events=events,
            source_path=event_path,
            history=history,
            history_path=history_path,
            snapshot_recorded=snapshot_recorded,
            target_contributors=args.target_contributors,
        )
    )


def _format_public_launch_assets_command(args: argparse.Namespace) -> str:
    return format_public_launch_assets(root=args.root, target_contributors=args.target_contributors)


def _format_public_release_boundary_command(args: argparse.Namespace) -> str:
    return format_public_release_boundary(root=args.root, dist=args.dist)


def _format_public_proof_pack_command(args: argparse.Namespace) -> str:
    return format_public_proof_pack(
        repo_owner=args.repo_owner,
        repo_name=args.repo_name,
        target_contributors=args.target_contributors,
        actor=args.actor,
        artifact_name=args.artifact_name,
        contribution=args.contribution,
    )


def _format_record_growth_referral_command(args: argparse.Namespace) -> str:
    event_path = get_activation_event_path()
    actor = _default_actor(args.actor)
    route = _clean_cli_text(args.route, "growth").lower()
    source_url = _clean_cli_text(args.source_url)
    issue_number = int(args.issue_number or 0)
    campaign_hook = _clean_cli_text(args.campaign_hook)
    retry_command = (
        f'tiangong-mcp record-growth-referral --route {route} --source-url "{source_url or "https://github.com/owner/repo/issues/1"}" '
        f'--actor "{actor}"'
    )
    problem = public_proof_url_problem(source_url, field_name="source_url")
    if problem:
        return _format_cli_url_rejection(
            title="TianGong CLI Growth Referral Not Written",
            problem=problem,
            field_name="source_url",
            value=source_url,
            retry_command=retry_command,
        )

    try:
        event = record_activation_event(
            EVENT_ISSUEOPS_REFERRAL_RECORDED,
            actor=actor,
            metadata={
                "route": route,
                "source_url": source_url,
                "issue_number": issue_number,
                "campaign_hook": campaign_hook,
                "source_tool": "tiangong-mcp record-growth-referral",
            },
            path=event_path,
        )
    except OSError as exc:
        return _format_cli_write_failure(
            title="TianGong CLI Growth Referral Not Written",
            public_url=source_url,
            error=str(exc),
            retry_command=retry_command,
        )

    return append_brand_footer(
        "\n".join(
            [
                "# TianGong CLI Growth Referral Recorded",
                "",
                f"> Local ledger: `{event_path}`.",
                f"> Public proof URL: {source_url}",
                "> This records external public attention returning into TianGong; it does not award Spirit Power or invent traction.",
                "",
                "## Recorded Event",
                "",
                f"- Event: `{event.event_type}`",
                f"- Actor: @{event.actor}",
                f"- Route: `{route}`",
                f"- Source Issue: #{issue_number}" if issue_number else "- Source Issue: not provided; source_url is the proof.",
                f"- Campaign hook: {campaign_hook}" if campaign_hook else "- Campaign hook: not provided.",
                "",
                "## Recheck Commands",
                "",
                "- MCP activation report: `activation_funnel()`",
                "- MCP growth flywheel: `growth_flywheel()`",
                "- Terminal public proof report: `tiangong-mcp public-growth-report --record-snapshot --target-contributors 10`",
                "- Terminal proof pack: `tiangong-mcp public-proof-pack --target-contributors 10`",
                "- Terminal launch preflight: `tiangong-mcp public-launch-preflight --target-contributors 10`",
                "- Next share proof: `tiangong-mcp record-share-attribution --contribution forge --share-url \"https://github.com/owner/repo/issues/2\" --source-url \""
                + source_url
                + f"\" --actor \"{actor}\"`",
            ]
        )
    )


def _format_record_share_attribution_command(args: argparse.Namespace) -> str:
    event_path = get_activation_event_path()
    actor = _default_actor(args.actor)
    contribution = _clean_cli_text(args.contribution, "forge").lower()
    share_url = _clean_cli_text(args.share_url)
    source_url = _clean_cli_text(args.source_url)
    artifact_name = _clean_cli_text(args.artifact_name)
    issue_number = int(args.issue_number or 0)
    campaign_hook = _clean_cli_text(args.campaign_hook)
    retry_command = (
        f'tiangong-mcp record-share-attribution --contribution {contribution} '
        f'--share-url "{share_url or "https://github.com/owner/repo/issues/2"}" --actor "{actor}"'
    )

    share_problem = public_proof_url_problem(share_url, field_name="share_url")
    if share_problem:
        return _format_cli_url_rejection(
            title="TianGong CLI Share Attribution Not Written",
            problem=share_problem,
            field_name="share_url",
            value=share_url,
            retry_command=retry_command,
        )
    source_problem = public_proof_url_problem(source_url, field_name="source_url") if source_url else ""
    if source_problem:
        return _format_cli_url_rejection(
            title="TianGong CLI Share Attribution Not Written",
            problem=source_problem,
            field_name="source_url",
            value=source_url,
            retry_command=retry_command,
        )

    try:
        event = record_activation_event(
            EVENT_SHARE_ATTRIBUTION_RECORDED,
            actor=actor,
            artifact_name=artifact_name,
            metadata={
                "contribution": contribution,
                "share_url": share_url,
                "source_url": source_url,
                "issue_number": issue_number,
                "campaign_hook": campaign_hook,
                "source_tool": "tiangong-mcp record-share-attribution",
            },
            path=event_path,
        )
    except OSError as exc:
        return _format_cli_write_failure(
            title="TianGong CLI Share Attribution Not Written",
            public_url=share_url,
            error=str(exc),
            retry_command=retry_command,
        )

    return append_brand_footer(
        "\n".join(
            [
                "# TianGong CLI Share Attribution Recorded",
                "",
                f"> Local ledger: `{event_path}`.",
                f"> Public share URL: {share_url}",
                "> This records a public contribution share into the local ledger; it does not claim downloads, repost counts, referrals, rewards, or retention.",
                "",
                "## Recorded Event",
                "",
                f"- Event: `{event.event_type}`",
                f"- Actor: @{event.actor}",
                f"- Contribution: `{contribution}`",
                f"- Artifact: `{artifact_name}`" if artifact_name else "- Artifact: not provided.",
                f"- Source bridge: {source_url}" if source_url else "- Source bridge: not provided.",
                f"- Source Issue: #{issue_number}" if issue_number else "- Source Issue: not provided.",
                f"- Campaign hook: {campaign_hook}" if campaign_hook else "- Campaign hook: not provided.",
                "",
                "## Recheck Commands",
                "",
                "- MCP share report: `share_attribution_report()`",
                "- MCP share leaderboard: `leaderboard(type=\"share\")`",
                "- MCP activation report: `activation_funnel()`",
                "- MCP growth flywheel: `growth_flywheel()`",
                "- Terminal public proof report: `tiangong-mcp public-growth-report --record-snapshot --target-contributors 10`",
                "- Terminal proof pack: `tiangong-mcp public-proof-pack --target-contributors 10`",
                "- Terminal launch preflight: `tiangong-mcp public-launch-preflight --target-contributors 10`",
            ]
        )
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tiangong-mcp",
        description=(
            "TianGong MCP server and public launch command line gates. "
            "Run without arguments to start the MCP server."
        ),
    )
    subparsers = parser.add_subparsers(dest="command")

    preflight = subparsers.add_parser(
        "public-launch-preflight",
        help="Print the ordered IssueOps, Release, PyPI, and first-proof launch runbook.",
    )
    preflight.add_argument(
        "--target-contributors",
        type=_positive_int,
        default=10,
        help="72-hour public campaign target used in recheck commands.",
    )
    preflight.set_defaults(handler=_format_public_launch_preflight_command)

    launch_assets = subparsers.add_parser(
        "public-launch-assets",
        help="Audit local IssueOps and release assets before staging public launch files.",
    )
    launch_assets.add_argument(
        "--root",
        default=".",
        help="Project root to audit. Defaults to the current working directory.",
    )
    launch_assets.add_argument(
        "--target-contributors",
        type=_positive_int,
        default=10,
        help="72-hour public campaign target used in recheck commands.",
    )
    launch_assets.set_defaults(handler=_format_public_launch_assets_command)

    release_boundary = subparsers.add_parser(
        "public-release-boundary",
        help="Verify built distributions still contain the public growth loop before release.",
    )
    release_boundary.add_argument(
        "--root",
        default=".",
        help="Project root to audit. Defaults to the current working directory.",
    )
    release_boundary.add_argument(
        "--dist",
        default="dist",
        help="Distribution directory containing wheel and sdist artifacts.",
    )
    release_boundary.set_defaults(handler=_format_public_release_boundary_command)

    proof_pack = subparsers.add_parser(
        "public-proof-pack",
        help="Print a no-network Growth/Share Issue proof kit for API rate-limit recovery.",
    )
    proof_pack.add_argument("--repo-owner", default="", help="GitHub repository owner. Defaults to config.")
    proof_pack.add_argument("--repo-name", default="", help="GitHub repository name. Defaults to config.")
    proof_pack.add_argument(
        "--target-contributors",
        type=_positive_int,
        default=10,
        help="72-hour public campaign target used in proof URLs and recheck commands.",
    )
    proof_pack.add_argument("--actor", default="", help="GitHub actor used in paste-ready ledger commands.")
    proof_pack.add_argument(
        "--artifact-name",
        default="first-growth-artifact",
        help="Artifact name used in the first Share Proof Issue and ledger command.",
    )
    proof_pack.add_argument("--contribution", default="forge", help="Contribution type for the Share Proof route.")
    proof_pack.set_defaults(handler=_format_public_proof_pack_command)

    record_growth = subparsers.add_parser(
        "record-growth-referral",
        help="Record a created public Growth Issue/PR/Discussion URL into the local activation ledger.",
    )
    record_growth.add_argument("--route", default="growth", help="IssueOps route name, such as growth or season.")
    record_growth.add_argument(
        "--source-url",
        required=True,
        help="Created public Issue/PR/Discussion URL. Do not pass an issues/new form URL.",
    )
    record_growth.add_argument("--actor", default="", help="GitHub actor to bind to the local proof event.")
    record_growth.add_argument(
        "--issue-number",
        type=_non_negative_int,
        default=0,
        help="Optional public Issue number for display and metadata.",
    )
    record_growth.add_argument("--campaign-hook", default="", help="Optional campaign hook attached to the event.")
    record_growth.set_defaults(handler=_format_record_growth_referral_command)

    record_share = subparsers.add_parser(
        "record-share-attribution",
        help="Record a created public contribution share URL into the local activation ledger.",
    )
    record_share.add_argument("--contribution", default="forge", help="Contribution type, such as forge or refine.")
    record_share.add_argument(
        "--share-url",
        required=True,
        help="Created public share Issue/PR/Discussion/post URL. Do not pass an issues/new form URL.",
    )
    record_share.add_argument("--source-url", default="", help="Optional created public Growth Issue source URL.")
    record_share.add_argument("--actor", default="", help="GitHub actor to bind to the local proof event.")
    record_share.add_argument("--artifact-name", default="", help="Optional artifact name or id for the share proof.")
    record_share.add_argument(
        "--issue-number",
        type=_non_negative_int,
        default=0,
        help="Optional public Issue number for display and metadata.",
    )
    record_share.add_argument("--campaign-hook", default="", help="Optional campaign hook attached to the event.")
    record_share.set_defaults(handler=_format_record_share_attribution_command)

    public_report = subparsers.add_parser(
        "public-growth-report",
        help="Print the real public GitHub/PyPI traction proof report.",
    )
    public_report.add_argument(
        "--record-snapshot",
        action="store_true",
        help="Append the fetched public traction snapshot to the local snapshot history.",
    )
    public_report.add_argument(
        "--target-contributors",
        type=int,
        default=0,
        help="Optional contributor target for campaign progress and recap.",
    )
    public_report.set_defaults(handler=_format_public_growth_report_command)

    return parser


def main(argv: Sequence[str] | None = None, *, stdout: TextIO | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args:
        _run_mcp_server()
        return 0

    stream = _configure_text_stream(stdout if stdout is not None else sys.stdout)
    parser = build_parser()
    namespace = parser.parse_args(args)
    handler = getattr(namespace, "handler", None)
    if handler is None:
        parser.print_help(stream)
        return 0

    stream.write(handler(namespace))
    stream.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
