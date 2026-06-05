"""Real activation telemetry for TianGong's growth loop."""

from __future__ import annotations

import json
import time
from collections import Counter
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import urlencode, urlsplit

from .config import config
from .install_bridge import DEFAULT_PACKAGE_NAME, git_tag_install_command, local_package_version

EVENT_START_CULTIVATION_VIEWED = "start_cultivation_viewed"
EVENT_ISSUEOPS_REFERRAL_RECORDED = "issueops_referral_recorded"
EVENT_FORGE_SUCCEEDED = "forge_agent_succeeded"
EVENT_PUBLISH_SUCCEEDED = "publish_agent_succeeded"
EVENT_INFUSE_SUCCEEDED = "infuse_spirit_succeeded"
EVENT_REFINE_SUCCEEDED = "refine_agent_succeeded"
EVENT_SHARE_ATTRIBUTION_RECORDED = "share_attribution_recorded"

CONTRIBUTION_SUCCESS_EVENTS = {
    EVENT_FORGE_SUCCEEDED,
    EVENT_PUBLISH_SUCCEEDED,
    EVENT_INFUSE_SUCCEEDED,
    EVENT_REFINE_SUCCEEDED,
}

SCHEMA_VERSION = 1
MAX_EVENT_BYTES = 2_000_000
MAX_EVENTS = 5_000
SHARE_PROOF_ISSUE_TEMPLATE = "tiangong-share-proof.yml"


def _current_candidate_install_command() -> str:
    return git_tag_install_command(
        repo_owner="",
        repo_name="",
        version_or_tag=local_package_version(DEFAULT_PACKAGE_NAME),
        package_name=DEFAULT_PACKAGE_NAME,
    )


@dataclass(frozen=True)
class ActivationEvent:
    """One real local activation event emitted by a public TianGong tool."""

    schema_version: int
    event_type: str
    actor: str
    artifact_name: str = ""
    timestamp: float = 0.0
    source: str = "mcp"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ActivationStage:
    """One measurable stage in the first-session activation funnel."""

    label: str
    value: str
    rate: float
    next_action: str
    denominator: int


@dataclass(frozen=True)
class ShareProofEntry:
    """One ranked public share proof contender."""

    actor: str
    public_share_events: int
    unique_public_urls: int
    source_bridges: int
    artifacts: int
    latest_timestamp: float

    @property
    def proof_power(self) -> int:
        return (
            self.public_share_events * 100
            + self.unique_public_urls * 50
            + self.source_bridges * 75
            + self.artifacts * 25
        )


def get_activation_event_path() -> Path:
    """Return the local JSONL event path for TianGong activation telemetry."""
    return Path(config.CAVE_LOGS_DIR) / "activation-events.jsonl"


def _clean_text(value: Any, fallback: str = "") -> str:
    text = " ".join(str(value or "").split())
    return text[:240] or fallback


def _safe_metadata(metadata: dict[str, Any] | None) -> dict[str, Any]:
    safe: dict[str, Any] = {}
    for key, value in (metadata or {}).items():
        safe_key = _clean_text(key)
        if not safe_key:
            continue
        if isinstance(value, bool | int | float) or value is None:
            safe[safe_key] = value
        else:
            safe[safe_key] = _clean_text(value)
    return safe


def _quote_arg(value: Any) -> str:
    return _clean_text(value).replace("\\", "\\\\").replace('"', '\\"')


def _is_public_http_url(value: str) -> bool:
    return value.startswith("https://") or value.startswith("http://")


def public_proof_url_problem(value: str, *, field_name: str) -> str:
    """Return why a public proof URL is not reviewable enough for the ledger."""
    url = (value or "").strip()
    if not _is_public_http_url(url):
        return f"{field_name} must be a public http(s) URL."
    if "<" in url or ">" in url:
        return f"{field_name} must be a created public post/Issue/PR/Discussion URL, not a placeholder URL."

    parsed = urlsplit(url)
    if not parsed.netloc:
        return f"{field_name} must include a public host."
    if parsed.netloc.lower() == "github.com" and parsed.path.rstrip("/").lower().endswith("/issues/new"):
        return f"{field_name} must be the created public post/Issue/PR/Discussion URL, not an issues/new form entrypoint."
    return ""


def format_share_attribution_command(
    *,
    contribution: str,
    actor: str,
    artifact_name: str = "",
    share_url: str = "https://github.com/owner/repo/issues/1",
    source_url: str = "",
) -> str:
    """Return a paste-ready command that binds a public share back to activation telemetry."""
    args = [
        f'contribution="{_quote_arg(contribution)}"',
        f'share_url="{_quote_arg(share_url)}"',
    ]
    if actor:
        args.append(f'actor="{_quote_arg(actor)}"')
    if artifact_name:
        args.append(f'artifact_name="{_quote_arg(artifact_name)}"')
    if source_url:
        args.append(f'source_url="{_quote_arg(source_url)}"')
    return f"`record_share_attribution({', '.join(args)})`"


def build_share_proof_issue_url(
    *,
    contribution: str = "forge",
    public_share_url: str = "",
    artifact_name: str = "artifact-name",
    campaign_hook: str = "Bind one public TianGong contribution share to real proof",
    repo_owner: str | None = None,
    repo_name: str | None = None,
) -> str:
    """Build a public GitHub new-issue URL for the share-proof Issue Form."""
    owner = repo_owner or config.GITHUB_REPO_OWNER
    name = repo_name or config.GITHUB_REPO_NAME
    normalized_contribution = _clean_text(contribution, "forge")
    query = urlencode(
        {
            "template": SHARE_PROOF_ISSUE_TEMPLATE,
            "title": f"[TianGong Share]: {normalized_contribution}",
            "contribution_type": normalized_contribution,
            "public_share_url": _clean_text(public_share_url),
            "artifact_name": _clean_text(artifact_name, "artifact-name"),
            "campaign_hook": _clean_text(campaign_hook),
        }
    )
    return f"https://github.com/{owner}/{name}/issues/new?{query}"


def _metadata_text(event: ActivationEvent, key: str, fallback: str = "") -> str:
    return _clean_text(event.metadata.get(key), fallback)


def _share_events(events: list[ActivationEvent]) -> list[ActivationEvent]:
    return [event for event in events if event.event_type == EVENT_SHARE_ATTRIBUTION_RECORDED]


def _recent_share_rows(share_events: list[ActivationEvent], limit: int = 5) -> list[str]:
    rows = []
    for event in sorted(share_events, key=lambda item: item.timestamp, reverse=True)[:limit]:
        contribution = _metadata_text(event, "contribution", "unknown")
        share_url = _metadata_text(event, "share_url", "missing-share-url")
        artifact = event.artifact_name or "unbound-artifact"
        actor = event.actor or "anonymous"
        rows.append(f"- `{contribution}` by @{actor} on `{artifact}`: {share_url}")
    return rows


def _build_share_proof_entries(events: list[ActivationEvent]) -> list[ShareProofEntry]:
    grouped: dict[str, dict[str, Any]] = {}
    for event in _share_events(events):
        actor = event.actor
        share_url = _metadata_text(event, "share_url")
        if not actor or not _is_public_http_url(share_url):
            continue

        bucket = grouped.setdefault(
            actor,
            {
                "events": 0,
                "urls": set(),
                "bridges": 0,
                "artifacts": set(),
                "latest": 0.0,
            },
        )
        bucket["events"] += 1
        bucket["urls"].add(share_url)
        if _is_public_http_url(_metadata_text(event, "source_url")):
            bucket["bridges"] += 1
        if event.artifact_name:
            bucket["artifacts"].add(event.artifact_name)
        bucket["latest"] = max(float(bucket["latest"]), event.timestamp)

    entries = [
        ShareProofEntry(
            actor=actor,
            public_share_events=int(data["events"]),
            unique_public_urls=len(data["urls"]),
            source_bridges=int(data["bridges"]),
            artifacts=len(data["artifacts"]),
            latest_timestamp=float(data["latest"]),
        )
        for actor, data in grouped.items()
    ]
    return sorted(
        entries,
        key=lambda entry: (
            -entry.proof_power,
            -entry.public_share_events,
            -entry.source_bridges,
            -entry.latest_timestamp,
            entry.actor.lower(),
        ),
    )


def _select_share_bottleneck(
    *,
    share_events_count: int,
    invalid_share_urls: int,
    source_bridge_count: int,
) -> tuple[str, str]:
    if share_events_count == 0:
        return (
            "No public share attribution",
            format_share_attribution_command(contribution="forge", actor="you", artifact_name="artifact-name"),
        )
    if invalid_share_urls:
        return (
            "Invalid or missing public share URLs",
            format_share_attribution_command(contribution="forge", actor="you", artifact_name="artifact-name"),
        )
    if source_bridge_count < share_events_count:
        return (
            "Source-to-share bridge",
            (
                '`record_share_attribution(contribution="forge", '
                'share_url="https://github.com/owner/repo/issues/2", '
                'source_url="https://github.com/owner/repo/issues/1", actor="your_github_username")`'
            ),
        )
    return (
        "Repeat public contribution",
        '`quest(action="browse")`',
    )


def format_share_attribution_report(
    events: list[ActivationEvent],
    *,
    source_path: str | Path | None = None,
    username: str = "",
) -> str:
    """Format a public growth proof report from recorded contribution-share attribution events."""
    filtered_events = [event for event in events if not username or event.actor == username]
    share_events = _share_events(filtered_events)
    share_urls = [_metadata_text(event, "share_url") for event in share_events]
    public_share_urls = {url for url in share_urls if _is_public_http_url(url)}
    invalid_share_urls = sum(1 for url in share_urls if not _is_public_http_url(url))
    source_bridge_count = sum(
        1
        for event in share_events
        if _is_public_http_url(_metadata_text(event, "share_url"))
        and _is_public_http_url(_metadata_text(event, "source_url"))
    )
    contribution_counter = Counter(_metadata_text(event, "contribution", "unknown") for event in share_events)
    actor_counter = Counter(event.actor for event in share_events if event.actor)
    artifact_counter = Counter(event.artifact_name for event in share_events if event.artifact_name)
    contribution_actors = {
        event.actor for event in filtered_events if event.event_type in CONTRIBUTION_SUCCESS_EVENTS and event.actor
    }
    share_actors = {event.actor for event in share_events if event.actor}
    denominator = max(len(contribution_actors), len(share_actors))
    share_rate = _rate(len(share_actors), denominator)
    bottleneck, next_action = _select_share_bottleneck(
        share_events_count=len(share_events),
        invalid_share_urls=invalid_share_urls,
        source_bridge_count=source_bridge_count,
    )
    recommended_contribution = contribution_counter.most_common(1)[0][0] if contribution_counter else "forge"
    recommended_artifact = artifact_counter.most_common(1)[0][0] if artifact_counter else "artifact-name"
    latest_public_share_url = next((url for url in reversed(share_urls) if _is_public_http_url(url)), "")
    share_issue_url = build_share_proof_issue_url(
        contribution=recommended_contribution,
        public_share_url=latest_public_share_url,
        artifact_name=recommended_artifact,
        campaign_hook=f"Bind TianGong public share proof; current bottleneck: {bottleneck}",
    )
    path = Path(source_path) if source_path is not None else get_activation_event_path()
    scope = f"@{username}" if username else "all local events"

    lines = [
        "# TianGong Public Growth Attribution",
        "",
        f"> Data source: `{path}`; scope: {scope}.",
        (
            "> This report does not invent downloads, retention, repost counts, or referral conversions; "
            "it only summarizes public URLs already recorded in the local MCP activation ledger."
        ),
        "",
        "## Proof Snapshot",
        "",
        "| Metric | Real value |",
        "|---|---:|",
        f"| Total local activation events | {len(filtered_events)} |",
        f"| Public share events | {len(share_events)} |",
        f"| Unique public share URLs | {len(public_share_urls)} |",
        f"| Source-to-share bridges | {source_bridge_count} |",
        f"| Public sharing actors | {len(share_actors)} |",
        f"| Contribution-to-share actor rate | {_format_percent(share_rate)} |",
        "",
    ]

    if not share_events:
        lines.extend(
            [
                "> No public contribution share attribution has been recorded yet.",
                "> First target: bind one real contribution share URL to one real contribution.",
                "",
            ]
        )

    lines.extend(
        [
            "## Contribution Pull",
            "",
            "| Contribution | Shares | Next proof command |",
            "|---|---:|---|",
        ]
    )
    if contribution_counter:
        for contribution, count in contribution_counter.most_common():
            lines.append(
                f"| {contribution} | {count} | "
                f"{format_share_attribution_command(contribution=contribution, actor='you', artifact_name='artifact-name')} |"
            )
    else:
        lines.append(
            "| forge | 0 | "
            f"{format_share_attribution_command(contribution='forge', actor='you', artifact_name='artifact-name')} |"
        )

    lines.extend(
        [
            "",
            "## Current Bottleneck",
            "",
            f"- Bottleneck: {bottleneck}",
            f"- First action: {next_action}",
            "",
            "## Top Public Proof URLs",
            "",
        ]
    )
    rows = _recent_share_rows(share_events)
    lines.extend(rows or ["- No public proof URL has been recorded yet."])

    lines.extend(
        [
            "",
            "## Repeat Loop",
            "",
            "- Record the next public contribution share: "
            f"{format_share_attribution_command(contribution='forge', actor='you', artifact_name='artifact-name')}",
            f"- Open public share-proof Issue: {share_issue_url}",
            "- Recheck activation: `activation_funnel()`",
            "- Recheck growth flywheel: `growth_flywheel()`",
            "- Turn a weak contribution type into a bounty: "
            '`quest(action="post", artifact_name="share-proof-bounty", description="Create one public TianGong contribution proof")`',
            "",
            "## Copy Public Growth Proof",
            "",
            "```text",
            (
                f"TianGong public growth attribution: {len(share_events)} public share events, "
                f"{len(public_share_urls)} unique public URLs, {len(share_actors)} sharing actors. "
                f"Current bottleneck: {bottleneck}."
            ),
            "No fake downloads, retention, repost counts, or referral conversions are claimed.",
            f"Install: {_current_candidate_install_command()}",
            "Install decision: tiangong-mcp public-install-command",
            "PyPI-current install after registry readiness: pip install -U tiangong-mcp",
            "Recheck: share_attribution_report()",
            f"Open proof issue: {share_issue_url}",
            "```",
        ]
    )

    if actor_counter:
        lines.extend(
            [
                "",
                "## Actor Pull",
                "",
                "| Actor | Shares |",
                "|---|---:|",
            ]
        )
        for actor, count in actor_counter.most_common(5):
            lines.append(f"| @{actor} | {count} |")

    if artifact_counter:
        lines.extend(
            [
                "",
                "## Artifact Pull",
                "",
                "| Artifact | Shares |",
                "|---|---:|",
            ]
        )
        for artifact, count in artifact_counter.most_common(5):
            lines.append(f"| `{artifact}` | {count} |")

    return "\n".join(lines)


def format_share_proof_leaderboard(
    events: list[ActivationEvent],
    *,
    source_path: str | Path | None = None,
    top_n: int = 20,
) -> str:
    """Format a competitive leaderboard from real public share-attribution proof events."""
    limit = max(1, int(top_n or 20))
    entries = _build_share_proof_entries(events)
    shown_entries = entries[:limit]
    path = Path(source_path) if source_path is not None else get_activation_event_path()
    total_public_share_events = sum(entry.public_share_events for entry in entries)
    total_public_share_urls = sum(entry.unique_public_urls for entry in entries)
    total_source_bridges = sum(entry.source_bridges for entry in entries)

    lines = [
        "# TianGong Share Proof Leaderboard",
        "",
        f"> Data source: `{path}`.",
        "> Ranking scope: only public http(s) share URLs already recorded in the local MCP activation ledger.",
        (
            "> Ranking formula: proof power = public share events * 100 + unique public URLs * 50 + "
            "source-to-share bridges * 75 + artifacts * 25."
        ),
        "> This leaderboard does not invent downloads, retention, repost counts, referrals, or Spirit Power.",
        "",
        "## Real Snapshot",
        "",
        "| Metric | Real value |",
        "|---|---:|",
        f"| Ranked actors | {len(entries)} |",
        f"| Public share events | {total_public_share_events} |",
        f"| Unique public share URLs | {total_public_share_urls} |",
        f"| Source-to-share bridges | {total_source_bridges} |",
        "",
        "## Share Proof Rankings",
        "",
        "| Rank | Actor | Proof Power | Public Shares | Unique URLs | Source Bridges | Artifacts | Next action |",
        "|---:|---|---:|---:|---:|---:|---:|---|",
    ]

    if shown_entries:
        for rank, entry in enumerate(shown_entries, start=1):
            lines.append(
                f"| {rank} | @{entry.actor} | {entry.proof_power} | {entry.public_share_events} | "
                f"{entry.unique_public_urls} | {entry.source_bridges} | {entry.artifacts} | "
                f"{format_share_attribution_command(contribution='forge', actor=entry.actor, artifact_name='artifact-name')} |"
            )
    else:
        lines.append(
            "| - | first-public-sharer | 0 | 0 | 0 | 0 | 0 | "
            f"{format_share_attribution_command(contribution='forge', actor='you', artifact_name='artifact-name')} |"
        )
        lines.extend(
            [
                "",
                "> No public share proof contender has entered the leaderboard yet.",
                "> First target: record one reviewable contribution share URL, then rerun the board.",
            ]
        )

    champion_line = (
        f"Current share proof champion: @{shown_entries[0].actor} with {shown_entries[0].proof_power} proof power."
        if shown_entries
        else "No champion yet; the first public proof URL creates the board."
    )
    next_chase_line = (
        f"Next chase target: beat {shown_entries[0].proof_power} proof power with another public contribution share."
        if shown_entries
        else "Next chase target: record the first public contribution share."
    )
    share_issue_url = build_share_proof_issue_url(campaign_hook=next_chase_line)

    lines.extend(
        [
            "",
            "## Challenge Loop",
            "",
            f"- {champion_line}",
            f"- {next_chase_line}",
            "- Record a new proof: "
            f"{format_share_attribution_command(contribution='forge', actor='you', artifact_name='artifact-name')}",
            "- Inspect proof URLs: `share_attribution_report()`",
            "- Refresh this board: `leaderboard(type=\"share\")`",
            f"- Open public share-proof Issue: {share_issue_url}",
            "- Recheck activation: `activation_funnel()`",
            "- Recheck growth flywheel: `growth_flywheel()`",
            "",
            "## Copy Share Proof Challenge",
            "",
            "```text",
            (
                f"TianGong Share Proof Leaderboard: {len(entries)} ranked actors, "
                f"{total_public_share_events} public share events, {total_public_share_urls} unique public URLs. "
                f"{champion_line}"
            ),
            "No fake downloads, retention, repost counts, referrals, or Spirit Power are claimed.",
            f"Join: {_current_candidate_install_command()}",
            "Install decision: tiangong-mcp public-install-command",
            "PyPI-current install after registry readiness: pip install -U tiangong-mcp",
            "Record proof: record_share_attribution(...)",
            "Refresh board: leaderboard(type=\"share\")",
            f"Open proof issue: {share_issue_url}",
            "```",
        ]
    )
    return "\n".join(lines)


def record_activation_event(
    event_type: str,
    *,
    actor: str = "",
    artifact_name: str = "",
    metadata: dict[str, Any] | None = None,
    path: str | Path | None = None,
    now: float | None = None,
) -> ActivationEvent:
    """Append one real activation event to the local JSONL event log."""
    event = ActivationEvent(
        schema_version=SCHEMA_VERSION,
        event_type=_clean_text(event_type, "unknown"),
        actor=_clean_text(actor, "anonymous"),
        artifact_name=_clean_text(artifact_name),
        timestamp=time.time() if now is None else float(now),
        metadata=_safe_metadata(metadata),
    )
    target = Path(path) if path is not None else get_activation_event_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(asdict(event), ensure_ascii=False, sort_keys=True) + "\n")
    return event


def _read_recent_text(path: Path, max_bytes: int) -> str:
    size = path.stat().st_size
    with path.open("rb") as handle:
        if size > max_bytes:
            handle.seek(size - max_bytes)
            handle.readline()
        return handle.read(max_bytes).decode("utf-8", errors="replace")


def _event_from_dict(data: dict[str, Any]) -> ActivationEvent | None:
    event_type = _clean_text(data.get("event_type"))
    if not event_type:
        return None
    metadata = data.get("metadata")
    return ActivationEvent(
        schema_version=int(data.get("schema_version") or SCHEMA_VERSION),
        event_type=event_type,
        actor=_clean_text(data.get("actor"), "anonymous"),
        artifact_name=_clean_text(data.get("artifact_name")),
        timestamp=float(data.get("timestamp") or 0.0),
        source=_clean_text(data.get("source"), "mcp"),
        metadata=_safe_metadata(metadata if isinstance(metadata, dict) else {}),
    )


def load_activation_events(
    *,
    path: str | Path | None = None,
    max_events: int = MAX_EVENTS,
    max_bytes: int = MAX_EVENT_BYTES,
) -> list[ActivationEvent]:
    """Load recent local activation events, skipping malformed lines."""
    target = Path(path) if path is not None else get_activation_event_path()
    if not target.exists():
        return []

    events: list[ActivationEvent] = []
    for line in _read_recent_text(target, max_bytes=max_bytes).splitlines():
        if not line.strip():
            continue
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict):
            event = _event_from_dict(data)
            if event:
                events.append(event)
    return events[-max_events:]


def _rate(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return min(1.0, max(0.0, numerator / denominator))


def _format_percent(value: float) -> str:
    return f"{value * 100:.1f}%"


def _event_actors(events: list[ActivationEvent], event_type: str) -> set[str]:
    return {event.actor for event in events if event.event_type == event_type and event.actor}


def _event_artifacts(events: list[ActivationEvent], event_type: str) -> set[str]:
    return {event.artifact_name for event in events if event.event_type == event_type and event.artifact_name}


def _build_activation_stages(events: list[ActivationEvent]) -> list[ActivationStage]:
    all_actors = {event.actor for event in events if event.actor}
    referral_actors = _event_actors(events, EVENT_ISSUEOPS_REFERRAL_RECORDED)
    entry_actors = _event_actors(events, EVENT_START_CULTIVATION_VIEWED)
    forge_actors = _event_actors(events, EVENT_FORGE_SUCCEEDED)
    refine_actors = _event_actors(events, EVENT_REFINE_SUCCEEDED)
    share_actors = _event_actors(events, EVENT_SHARE_ATTRIBUTION_RECORDED)
    forged_artifacts = _event_artifacts(events, EVENT_FORGE_SUCCEEDED)
    published_artifacts = _event_artifacts(events, EVENT_PUBLISH_SUCCEEDED)
    appraised_artifacts = _event_artifacts(events, EVENT_INFUSE_SUCCEEDED)

    cohort_count = len(all_actors)
    entry_denominator = cohort_count
    forge_denominator = max(len(entry_actors), len(forge_actors))
    publish_denominator = max(len(forged_artifacts), len(published_artifacts))
    appraisal_denominator = max(len(published_artifacts), len(appraised_artifacts))
    refine_denominator = max(len(forge_actors), len(refine_actors))
    contribution_actors = forge_actors | refine_actors | _event_actors(events, EVENT_PUBLISH_SUCCEEDED) | _event_actors(
        events, EVENT_INFUSE_SUCCEEDED
    )
    share_denominator = max(len(contribution_actors), len(share_actors))

    return [
        ActivationStage(
            label="IssueOps 回流",
            value=f"{len(referral_actors)} 位",
            rate=_rate(len(referral_actors), max(len(entry_actors), len(referral_actors))),
            next_action=(
                '`record_growth_referral(route="growth", '
                'source_url="https://github.com/owner/repo/issues/1")`'
            ),
            denominator=max(len(entry_actors), len(referral_actors)),
        ),
        ActivationStage(
            label="入口曝光",
            value=f"{len(entry_actors)} 位",
            rate=_rate(len(entry_actors), entry_denominator),
            next_action='`start_cultivation(username="your_github_username")`',
            denominator=entry_denominator,
        ),
        ActivationStage(
            label="首件法宝激活",
            value=f"{len(forge_actors)}/{forge_denominator}",
            rate=_rate(len(forge_actors), forge_denominator),
            next_action='`forge_agent(name="your-first-artifact", description="...")`',
            denominator=forge_denominator,
        ),
        ActivationStage(
            label="发布出世",
            value=f"{len(published_artifacts)}/{publish_denominator}",
            rate=_rate(len(published_artifacts), publish_denominator),
            next_action='`publish_agent(artifact_name="artifact-name")`',
            denominator=publish_denominator,
        ),
        ActivationStage(
            label="鉴定回流",
            value=f"{len(appraised_artifacts)}/{appraisal_denominator}",
            rate=_rate(len(appraised_artifacts), appraisal_denominator),
            next_action='`infuse_spirit(artifact_name="artifact-name")`',
            denominator=appraisal_denominator,
        ),
        ActivationStage(
            label="淬炼复访",
            value=f"{len(refine_actors)}/{refine_denominator}",
            rate=_rate(len(refine_actors), refine_denominator),
            next_action='`refine_agent(agent_id="artifact-id", changes="...")`',
            denominator=refine_denominator,
        ),
        ActivationStage(
            label="贡献分享",
            value=f"{len(share_actors)}/{share_denominator}",
            rate=_rate(len(share_actors), share_denominator),
            next_action=format_share_attribution_command(contribution="forge", actor="you", artifact_name="artifact-name"),
            denominator=share_denominator,
        ),
    ]


def _select_bottleneck(stages: list[ActivationStage]) -> ActivationStage:
    candidates = [stage for stage in stages[1:] if stage.denominator > 0]
    if candidates:
        return min(candidates, key=lambda stage: stage.rate)
    for stage in stages:
        if stage.label == "入口曝光":
            return stage
    return stages[0]


def format_activation_funnel(
    events: list[ActivationEvent],
    *,
    source_path: str | Path | None = None,
    username: str = "",
) -> str:
    """Format a real local activation funnel from recorded event facts."""
    filtered_events = events
    if username:
        filtered_events = [event for event in events if event.actor == username]

    stages = _build_activation_stages(filtered_events)
    bottleneck = _select_bottleneck(stages)
    actor_count = len({event.actor for event in filtered_events if event.actor})
    artifact_count = len({event.artifact_name for event in filtered_events if event.artifact_name})
    path = Path(source_path) if source_path is not None else get_activation_event_path()
    scope = f"@{username}" if username else "全部本地事件"

    lines = [
        "# TianGong 真实激活漏斗",
        "",
        f"> 数据源: `{path}`；范围: {scope}。",
        f"> 当前事件日志: {len(filtered_events)} 条激活事件、{actor_count} 位参与者、{artifact_count} 件法宝。",
        "> 不伪造下载量、留存、转介绍或外部传播数据；这里只统计本地 MCP 工具已经真实记录的事件。",
        "",
    ]
    if not filtered_events:
        lines.extend(
            [
                "> 当前日志不能证明真实激活；先让用户看到入口，再完成第一件法宝。",
                "",
            ]
        )

    lines.extend(
        [
            "## 漏斗转化表",
            "",
            "| 环节 | 真实事件 | 转化率 | 下一动作 |",
            "|---|---:|---:|---|",
        ]
    )
    for stage in stages:
        lines.append(f"| {stage.label} | {stage.value} | {_format_percent(stage.rate)} | {stage.next_action} |")

    lines.extend(
        [
            "",
            "## 当前瓶颈",
            "",
            f"- 最薄弱环节: {bottleneck.label}",
            f"- 真实转化率: {_format_percent(bottleneck.rate)}",
            f"- 第一手行动: {bottleneck.next_action}",
            "",
            "## 闭环复查",
            "",
            "- 查看真实激活漏斗: `activation_funnel()`",
            "- 查看增长飞轮: `growth_flywheel()`",
            "- 发起 72 小时爆发战役: `growth_campaign()`",
            "- 验证公开牵引力: `public_growth_report()`",
            "- 公开发布预检: `public_launch_preflight()`",
            "- 生成首个公开证明包: `public_proof_pack()`",
            "- 查看赛季追赶: `leaderboard(type=\"season\")`",
            "",
            "## 复制激活战报",
            "",
            "```text",
            (
                f"TianGong 真实激活漏斗: {len(filtered_events)} 条事件、{actor_count} 位参与者、"
                f"{artifact_count} 件法宝。当前瓶颈是 {bottleneck.label}，下一步 {bottleneck.next_action}。"
            ),
            f"加入修炼: {_current_candidate_install_command()}",
            "安装后复查: tiangong-mcp public-install-command",
            "PyPI 追平后安装: pip install -U tiangong-mcp",
            "复查激活: activation_funnel()",
            "复查飞轮: growth_flywheel()",
            "发起战役: growth_campaign()",
            "验证公开证明: public_growth_report()",
            "公开发布预检: public_launch_preflight()",
            "首个公开证明包: public_proof_pack()",
            "```",
        ]
    )
    return "\n".join(lines)
