"""No-network first public proof pack for TianGong launch operators."""

from __future__ import annotations

from .activation import build_share_proof_issue_url
from .config import config
from .growth import build_growth_issue_url


def _safe_positive_int(value: int | str | None, fallback: int = 10) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return fallback
    return number if number > 0 else fallback


def _clean_arg(value: str, fallback: str) -> str:
    text = " ".join(str(value or "").split())[:160]
    return text or fallback


def _quote(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _issue_placeholder(owner: str, repo: str, token: str) -> str:
    return f"https://github.com/{owner}/{repo}/issues/<opened-{token}-issue-number>"


def format_public_proof_pack(
    *,
    repo_owner: str = "",
    repo_name: str = "",
    target_contributors: int = 10,
    actor: str = "",
    artifact_name: str = "first-growth-artifact",
    contribution: str = "forge",
) -> str:
    """Format a no-network first-proof kit for public GitHub IssueOps launch."""
    owner = _clean_arg(repo_owner, config.GITHUB_REPO_OWNER)
    repo = _clean_arg(repo_name, config.GITHUB_REPO_NAME)
    target = _safe_positive_int(target_contributors)
    normalized_actor = _clean_arg(actor, "your_github_username")
    artifact = _clean_arg(artifact_name, "first-growth-artifact")
    normalized_contribution = _clean_arg(contribution, "forge")
    real_data_context = (
        "No-network first proof pack: public API metrics were not fetched in this command. "
        "Run public launch preflight after pushing IssueOps routes to verify real public state."
    )
    growth_issue_url = build_growth_issue_url(
        bottleneck_label="Public Growth IssueOps Issues",
        campaign_hook="Open the first reviewable TianGong public growth proof",
        real_data_context=real_data_context,
        target_contributors=target,
        repo_owner=owner,
        repo_name=repo,
    )
    share_issue_url = build_share_proof_issue_url(
        contribution=normalized_contribution,
        public_share_url="",
        artifact_name=artifact,
        campaign_hook="Bind the first TianGong public contribution share proof",
        repo_owner=owner,
        repo_name=repo,
    )
    growth_proof_url = _issue_placeholder(owner, repo, "growth")
    share_proof_url = _issue_placeholder(owner, repo, "share-proof")
    actor_arg = _quote(normalized_actor)
    artifact_arg = _quote(artifact)
    contribution_arg = _quote(normalized_contribution)
    cli_growth_command = (
        f'tiangong-mcp record-growth-referral --route growth --source-url "{growth_proof_url}" '
        f'--actor "{actor_arg}"'
    )
    cli_share_command = (
        f'tiangong-mcp record-share-attribution --contribution "{contribution_arg}" '
        f'--share-url "{share_proof_url}" --artifact-name "{artifact_arg}" '
        f'--source-url "{growth_proof_url}" --actor "{actor_arg}"'
    )

    return "\n".join(
        [
            "# TianGong First Public Proof Pack",
            "",
            f"> Repository: `{owner}/{repo}`.",
            "> This command does not fetch GitHub or PyPI state, upload distributions, open Issues, or claim public traction.",
            "> It prepares the first reviewable Growth and Share Proof actions when public APIs are unavailable or rate-limited.",
            "> It does not invent downloads, retention, repost counts, referral conversions, or rewards.",
            "",
            "## Prerequisite Gates",
            "",
            "- Local launch assets: `tiangong-mcp public-launch-assets`",
            "- Local release boundary: `tiangong-mcp public-release-boundary`",
            f"- Public preflight after remote push: `tiangong-mcp public-launch-preflight --target-contributors {target}`",
            "",
            "## Open Public Proof Issues",
            "",
            "> Use the form URLs only to create public Issues.",
            "> Use created Issue URLs, not `issues/new?...` form URLs, for ledger commands.",
            "",
            f"- Growth Issue Form: {growth_issue_url}",
            f"- Share Proof Issue Form: {share_issue_url}",
            f"- Created Growth Issue placeholder: {growth_proof_url}",
            f"- Created Share Proof Issue placeholder: {share_proof_url}",
            "",
            "## First External Contributor Path",
            "",
            "> Use after public preflight shows remote IssueOps live and PyPI latest current.",
            "> Use form URLs to open Issues, then use created Issue URLs as reviewable proof.",
            "> Only public Growth/Share Issue authors, public PR authors, and local ledger actors count toward the target; stars, forks, downloads, reposts, retention, and watchers do not.",
            "",
            "1. Install current public package: `pip install -U tiangong-mcp`",
            '2. Start cultivation in an MCP client: `start_cultivation(username="your_github_username")`',
            (
                "3. Forge the first public artifact: "
                f'`forge_agent(name="{artifact}", description="A TianGong artifact opening the first public proof loop")`'
            ),
            f"4. Open Share Proof Issue Form: {share_issue_url}",
            f"5. After submission, replace `{share_proof_url}` with the created Issue URL before recording proof.",
            "",
            "## After Submission CLI Ledger Commands",
            "",
            "```bash",
            cli_growth_command,
            cli_share_command,
            "```",
            "",
            "## After Submission MCP Ledger Commands",
            "",
            "```text",
            f'record_growth_referral(route="growth", source_url="{growth_proof_url}", actor="{actor_arg}")',
            (
                f'record_share_attribution(contribution="{contribution_arg}", share_url="{share_proof_url}", '
                f'artifact_name="{artifact_arg}", source_url="{growth_proof_url}", actor="{actor_arg}")'
            ),
            "```",
            "",
            "## Copy First Public Proof Post",
            "",
            "```text",
            f"TianGong first public proof pack for {owner}/{repo}: open one Growth Issue and one Share Proof Issue, then record the created Issue URLs back into the local activation ledger.",
            "This is a reviewable proof path, not a claim of downloads, retention, repost counts, referral conversions, or rewards.",
            f"Growth form: {growth_issue_url}",
            f"Share form: {share_issue_url}",
            f"CLI Record Growth return: {cli_growth_command}",
            f"CLI Record Share proof: {cli_share_command}",
            f"Record Growth return: record_growth_referral(route=\"growth\", source_url=\"{growth_proof_url}\", actor=\"{actor_arg}\")",
            (
                "Record Share proof: "
                f"record_share_attribution(contribution=\"{contribution_arg}\", share_url=\"{share_proof_url}\", "
                f"artifact_name=\"{artifact_arg}\", source_url=\"{growth_proof_url}\", actor=\"{actor_arg}\")"
            ),
            "Install: pip install tiangong-mcp",
            "```",
            "",
            "## Copy External Contributor Invite",
            "",
            "```text",
            f"I want to be counted in the TianGong 72h launch for {owner}/{repo}.",
            "Install current public package: pip install -U tiangong-mcp",
            'Start: start_cultivation(username="your_github_username")',
            (
                f'Forge: forge_agent(name="{artifact}", '
                'description="A TianGong artifact opening the first public proof loop")'
            ),
            f"Open Share Proof Issue: {share_issue_url}",
            "After submission, paste the created Issue URL so it can be recorded as reviewable proof.",
            "Only public Growth/Share Issue authors, public PR authors, and local ledger actors count; stars, forks, downloads, reposts, retention, and watchers do not.",
            "```",
            "",
            "## Recheck Commands",
            "",
            f"- Public preflight: `tiangong-mcp public-launch-preflight --target-contributors {target}`",
            f"- Public proof report: `tiangong-mcp public-growth-report --record-snapshot --target-contributors {target}`",
            "- Local activation: `activation_funnel()`",
            "",
        ]
    )
