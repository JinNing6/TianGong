"""Activation funnel tests for TianGong's real growth telemetry."""

from __future__ import annotations

import pytest

from tiangong.cultivator import CultivatorProfile
from tiangong.forge import AgentSpec


def test_activation_events_are_jsonl_and_round_trip(tmp_path):
    """Activation telemetry should persist real events without inventing adoption."""
    from tiangong.activation import (
        EVENT_FORGE_SUCCEEDED,
        EVENT_START_CULTIVATION_VIEWED,
        load_activation_events,
        record_activation_event,
    )

    event_path = tmp_path / "activation-events.jsonl"

    record_activation_event(
        EVENT_START_CULTIVATION_VIEWED,
        actor="newbie",
        metadata={"source_tool": "start_cultivation"},
        path=event_path,
        now=100.0,
    )
    record_activation_event(
        EVENT_FORGE_SUCCEEDED,
        actor="newbie",
        artifact_name="dragon-forge",
        metadata={"agent_id": "tg-123"},
        path=event_path,
        now=101.0,
    )

    raw_lines = event_path.read_text(encoding="utf-8").splitlines()
    events = load_activation_events(path=event_path)

    assert len(raw_lines) == 2
    assert events[0].event_type == EVENT_START_CULTIVATION_VIEWED
    assert events[0].actor == "newbie"
    assert events[1].event_type == EVENT_FORGE_SUCCEEDED
    assert events[1].artifact_name == "dragon-forge"
    assert events[1].metadata["agent_id"] == "tg-123"


def test_activation_funnel_formats_real_conversion_without_fake_metrics(tmp_path):
    """The funnel should calculate conversion from local event facts only."""
    from tiangong.activation import (
        EVENT_FORGE_SUCCEEDED,
        EVENT_INFUSE_SUCCEEDED,
        EVENT_ISSUEOPS_REFERRAL_RECORDED,
        EVENT_PUBLISH_SUCCEEDED,
        EVENT_REFINE_SUCCEEDED,
        EVENT_SHARE_ATTRIBUTION_RECORDED,
        EVENT_START_CULTIVATION_VIEWED,
        format_activation_funnel,
        load_activation_events,
        record_activation_event,
    )

    event_path = tmp_path / "activation-events.jsonl"
    record_activation_event(
        EVENT_ISSUEOPS_REFERRAL_RECORDED,
        actor="newbie",
        metadata={"route": "growth", "source_url": "https://github.com/JinNing6/TianGong/issues/7"},
        path=event_path,
    )
    for actor in ("newbie", "observer"):
        record_activation_event(EVENT_START_CULTIVATION_VIEWED, actor=actor, path=event_path)
    record_activation_event(
        EVENT_FORGE_SUCCEEDED,
        actor="newbie",
        artifact_name="dragon-forge",
        metadata={"agent_id": "tg-123"},
        path=event_path,
    )
    record_activation_event(EVENT_PUBLISH_SUCCEEDED, actor="newbie", artifact_name="dragon-forge", path=event_path)
    record_activation_event(EVENT_INFUSE_SUCCEEDED, actor="reviewer", artifact_name="dragon-forge", path=event_path)
    record_activation_event(EVENT_REFINE_SUCCEEDED, actor="newbie", artifact_name="dragon-forge", path=event_path)
    record_activation_event(
        EVENT_SHARE_ATTRIBUTION_RECORDED,
        actor="newbie",
        artifact_name="dragon-forge",
        metadata={
            "contribution": "forge",
            "share_url": "https://github.com/JinNing6/TianGong/issues/8",
        },
        path=event_path,
    )

    result = format_activation_funnel(load_activation_events(path=event_path), source_path=event_path)

    assert "真实激活漏斗" in result
    assert "activation-events.jsonl" in result
    assert "不伪造下载量" in result
    assert "| IssueOps 回流 | 1 位 | 50.0% |" in result
    assert "| 入口曝光 | 2 位 | 66.7% |" in result
    assert "| 首件法宝激活 | 1/2 | 50.0% |" in result
    assert "| 发布出世 | 1/1 | 100.0% |" in result
    assert "| 鉴定回流 | 1/1 | 100.0% |" in result
    assert "| 淬炼复访 | 1/1 | 100.0% |" in result
    assert "| 贡献分享 | 1/2 | 50.0% |" in result
    assert "最薄弱环节: 首件法宝激活" in result
    assert "`forge_agent(name=\"your-first-artifact\"" in result
    assert "`growth_flywheel()`" in result
    assert "`growth_campaign()`" in result
    assert "`public_growth_report()`" in result
    assert "`public_launch_preflight()`" in result
    assert "`public_proof_pack()`" in result
    assert 'python -m pip install --upgrade "tiangong-mcp @ git+https://github.com/JinNing6/TianGong.git@v0.1.11"' in result
    assert "tiangong-mcp public-install-command" in result
    assert "pip install -U tiangong-mcp" in result
    assert "pip install tiangong-mcp" not in result


def test_share_attribution_command_is_paste_ready_and_reviewable():
    """Success share cards need a callable way to bind public shares back to telemetry."""
    from tiangong.activation import format_share_attribution_command

    command = format_share_attribution_command(
        contribution="forge",
        actor="newbie",
        artifact_name="dragon-forge",
        source_url="https://github.com/JinNing6/TianGong/issues/7",
    )

    assert command.startswith("`record_share_attribution(")
    assert 'contribution="forge"' in command
    assert 'actor="newbie"' in command
    assert 'artifact_name="dragon-forge"' in command
    assert 'share_url="https://github.com/owner/repo/issues/1"' in command
    assert 'source_url="https://github.com/JinNing6/TianGong/issues/7"' in command


def test_empty_activation_funnel_discloses_missing_history(tmp_path):
    """An empty event log should be a recovery surface, not analytics theater."""
    from tiangong.activation import format_activation_funnel

    event_path = tmp_path / "activation-events.jsonl"

    result = format_activation_funnel([], source_path=event_path)

    assert "0 条激活事件" in result
    assert "不能证明真实激活" in result
    assert "不伪造下载量" in result
    assert "`start_cultivation(username=\"your_github_username\")`" in result
    assert "`forge_agent(name=\"your-first-artifact\"" in result
    assert "`growth_campaign()`" in result
    assert "`public_growth_report()`" in result
    assert "`public_launch_preflight()`" in result
    assert "`public_proof_pack()`" in result

def test_share_attribution_report_scores_public_share_urls(tmp_path):
    """Public share attribution should become a concrete growth proof surface."""
    from tiangong.activation import (
        EVENT_FORGE_SUCCEEDED,
        EVENT_PUBLISH_SUCCEEDED,
        EVENT_SHARE_ATTRIBUTION_RECORDED,
        format_share_attribution_report,
        load_activation_events,
        record_activation_event,
    )

    event_path = tmp_path / "activation-events.jsonl"
    record_activation_event(EVENT_FORGE_SUCCEEDED, actor="newbie", artifact_name="dragon-forge", path=event_path)
    record_activation_event(EVENT_PUBLISH_SUCCEEDED, actor="newbie", artifact_name="dragon-forge", path=event_path)
    record_activation_event(
        EVENT_SHARE_ATTRIBUTION_RECORDED,
        actor="newbie",
        artifact_name="dragon-forge",
        metadata={
            "contribution": "forge",
            "share_url": "https://github.com/JinNing6/TianGong/issues/8",
            "source_url": "https://github.com/JinNing6/TianGong/issues/7",
        },
        path=event_path,
    )
    record_activation_event(
        EVENT_SHARE_ATTRIBUTION_RECORDED,
        actor="newbie",
        artifact_name="dragon-forge",
        metadata={
            "contribution": "publish",
            "share_url": "https://github.com/JinNing6/TianGong/discussions/9",
        },
        path=event_path,
    )

    result = format_share_attribution_report(load_activation_events(path=event_path), source_path=event_path)

    assert "# TianGong Public Growth Attribution" in result
    assert "activation-events.jsonl" in result
    assert "| Public share events | 2 |" in result
    assert "| Unique public share URLs | 2 |" in result
    assert "| Source-to-share bridges | 1 |" in result
    assert "| forge | 1 |" in result
    assert "| publish | 1 |" in result
    assert "https://github.com/JinNing6/TianGong/issues/8" in result
    assert "https://github.com/JinNing6/TianGong/discussions/9" in result
    assert "`record_share_attribution(" in result
    assert "`activation_funnel()`" in result
    assert "`growth_flywheel()`" in result
    assert "https://github.com/JinNing6/TianGong/issues/new?" in result
    assert "template=tiangong-share-proof.yml" in result
    assert "contribution_type=forge" in result
    assert 'python -m pip install --upgrade "tiangong-mcp @ git+https://github.com/JinNing6/TianGong.git@v0.1.11"' in result
    assert "Install decision: tiangong-mcp public-install-command" in result
    assert "Install: pip install tiangong-mcp" not in result
    assert "does not invent downloads, retention, repost counts, or referral conversions" in result


def test_share_proof_issue_url_uses_public_issue_form_query_without_privileged_labels():
    """Share-proof recruitment should open the public Issue Form without requiring label permissions."""
    from urllib.parse import parse_qs, urlsplit

    from tiangong.activation import build_share_proof_issue_url

    url = build_share_proof_issue_url(
        contribution="publish",
        public_share_url="https://github.com/octo-org/octo-repo/discussions/9",
        artifact_name="dragon-forge",
        campaign_hook="Bind one public share back to real proof",
        repo_owner="octo-org",
        repo_name="octo-repo",
    )
    parsed = urlsplit(url)
    query = parse_qs(parsed.query)

    assert parsed.scheme == "https"
    assert parsed.netloc == "github.com"
    assert parsed.path == "/octo-org/octo-repo/issues/new"
    assert query["template"] == ["tiangong-share-proof.yml"]
    assert query["title"] == ["[TianGong Share]: publish"]
    assert query["contribution_type"] == ["publish"]
    assert query["public_share_url"] == ["https://github.com/octo-org/octo-repo/discussions/9"]
    assert query["artifact_name"] == ["dragon-forge"]
    assert query["campaign_hook"] == ["Bind one public share back to real proof"]
    assert "labels" not in query


def test_empty_share_attribution_report_recruits_first_public_proof(tmp_path):
    """An empty share report should recruit the first proof without fake virality."""
    from tiangong.activation import format_share_attribution_report

    event_path = tmp_path / "activation-events.jsonl"

    result = format_share_attribution_report([], source_path=event_path)

    assert "No public contribution share attribution has been recorded yet." in result
    assert "`record_share_attribution(contribution=\"forge\"" in result
    assert "`activation_funnel()`" in result
    assert "`growth_flywheel()`" in result
    assert "template=tiangong-share-proof.yml" in result
    assert "does not invent downloads" in result


def test_share_proof_leaderboard_ranks_real_public_share_proof(tmp_path):
    """Share proof should become a competitive surface from real public URLs only."""
    from tiangong.activation import (
        EVENT_SHARE_ATTRIBUTION_RECORDED,
        format_share_proof_leaderboard,
        load_activation_events,
        record_activation_event,
    )

    event_path = tmp_path / "activation-events.jsonl"
    record_activation_event(
        EVENT_SHARE_ATTRIBUTION_RECORDED,
        actor="alice",
        artifact_name="dragon-forge",
        metadata={
            "contribution": "forge",
            "share_url": "https://github.com/JinNing6/TianGong/issues/8",
            "source_url": "https://github.com/JinNing6/TianGong/issues/7",
        },
        path=event_path,
        now=100.0,
    )
    record_activation_event(
        EVENT_SHARE_ATTRIBUTION_RECORDED,
        actor="alice",
        artifact_name="phoenix-refine",
        metadata={
            "contribution": "publish",
            "share_url": "https://github.com/JinNing6/TianGong/discussions/9",
        },
        path=event_path,
        now=101.0,
    )
    record_activation_event(
        EVENT_SHARE_ATTRIBUTION_RECORDED,
        actor="bob",
        artifact_name="dragon-forge",
        metadata={
            "contribution": "forge",
            "share_url": "https://github.com/JinNing6/TianGong/issues/10",
        },
        path=event_path,
        now=102.0,
    )
    record_activation_event(
        EVENT_SHARE_ATTRIBUTION_RECORDED,
        actor="mallory",
        artifact_name="private-claim",
        metadata={"contribution": "forge", "share_url": "private-chat"},
        path=event_path,
        now=103.0,
    )

    result = format_share_proof_leaderboard(load_activation_events(path=event_path), source_path=event_path, top_n=2)

    assert "# TianGong Share Proof Leaderboard" in result
    assert "proof power = public share events * 100 + unique public URLs * 50 + source-to-share bridges * 75 + artifacts * 25" in result
    assert "| 1 | @alice | 425 | 2 | 2 | 1 | 2 |" in result
    assert "| 2 | @bob | 175 | 1 | 1 | 0 | 1 |" in result
    assert "@mallory" not in result
    assert "private-chat" not in result
    assert "does not invent downloads, retention, repost counts, referrals, or Spirit Power" in result
    assert "`record_share_attribution(" in result
    assert "`share_attribution_report()`" in result
    assert "`leaderboard(type=\"share\")`" in result
    assert "template=tiangong-share-proof.yml" in result
    assert 'python -m pip install --upgrade "tiangong-mcp @ git+https://github.com/JinNing6/TianGong.git@v0.1.11"' in result
    assert "Install decision: tiangong-mcp public-install-command" in result
    assert "Join: pip install tiangong-mcp" not in result


def test_empty_share_proof_leaderboard_recruits_first_public_competitor(tmp_path):
    """An empty share leaderboard should be a recruitment surface, not a fake ranking."""
    from tiangong.activation import format_share_proof_leaderboard

    event_path = tmp_path / "activation-events.jsonl"

    result = format_share_proof_leaderboard([], source_path=event_path)

    assert "# TianGong Share Proof Leaderboard" in result
    assert "No public share proof contender has entered the leaderboard yet." in result
    assert "`record_share_attribution(contribution=\"forge\"" in result
    assert "`share_attribution_report()`" in result
    assert "`leaderboard(type=\"share\")`" in result
    assert "template=tiangong-share-proof.yml" in result
    assert "does not invent downloads" in result


@pytest.mark.asyncio
async def test_mcp_activation_funnel_exposes_local_event_snapshot(monkeypatch, tmp_path):
    """activation_funnel should be callable as a public MCP diagnosis surface."""
    from tiangong import mcp_server
    from tiangong.activation import EVENT_START_CULTIVATION_VIEWED, record_activation_event

    event_path = tmp_path / "activation-events.jsonl"
    record_activation_event(EVENT_START_CULTIVATION_VIEWED, actor="newbie", path=event_path)

    monkeypatch.setattr(mcp_server, "get_activation_event_path", lambda: event_path)

    result = await mcp_server.activation_funnel()

    assert "真实激活漏斗" in result
    assert "1 条激活事件" in result
    assert "`activation_funnel()`" in result
    assert "TianGong" in result


@pytest.mark.asyncio
async def test_mcp_share_attribution_report_exposes_public_growth_proof(monkeypatch, tmp_path):
    """share_attribution_report should be a top-level MCP growth proof surface."""
    from tiangong import mcp_server
    from tiangong.activation import EVENT_SHARE_ATTRIBUTION_RECORDED, record_activation_event

    event_path = tmp_path / "activation-events.jsonl"
    record_activation_event(
        EVENT_SHARE_ATTRIBUTION_RECORDED,
        actor="newbie",
        artifact_name="dragon-forge",
        metadata={
            "contribution": "forge",
            "share_url": "https://github.com/JinNing6/TianGong/issues/8",
        },
        path=event_path,
    )
    monkeypatch.setattr(mcp_server, "get_activation_event_path", lambda: event_path)

    result = await mcp_server.share_attribution_report()

    assert "# TianGong Public Growth Attribution" in result
    assert "| Public share events | 1 |" in result
    assert "`record_share_attribution(" in result
    assert "TianGong" in result


@pytest.mark.asyncio
async def test_mcp_leaderboard_exposes_share_proof_ranking(monkeypatch, tmp_path):
    """The top-level leaderboard tool should expose share proof competition."""
    from tiangong import mcp_server
    from tiangong.activation import EVENT_SHARE_ATTRIBUTION_RECORDED, record_activation_event

    event_path = tmp_path / "activation-events.jsonl"
    record_activation_event(
        EVENT_SHARE_ATTRIBUTION_RECORDED,
        actor="alice",
        artifact_name="dragon-forge",
        metadata={
            "contribution": "forge",
            "share_url": "https://github.com/JinNing6/TianGong/issues/8",
        },
        path=event_path,
    )
    monkeypatch.setattr(mcp_server, "get_activation_event_path", lambda: event_path)

    result = await mcp_server.leaderboard(type="share", top_n=1)

    assert "# TianGong Share Proof Leaderboard" in result
    assert "| 1 | @alice |" in result
    assert "`share_attribution_report()`" in result
    assert "TianGong" in result


@pytest.mark.asyncio
async def test_record_growth_referral_turns_issueops_return_into_event(monkeypatch):
    """External IssueOps attention should be recordable when it returns to MCP."""
    from tiangong import mcp_server
    from tiangong.activation import EVENT_ISSUEOPS_REFERRAL_RECORDED

    recorded = []
    monkeypatch.setattr(mcp_server, "record_activation_event", lambda *args, **kwargs: recorded.append((args, kwargs)))

    result = await mcp_server.record_growth_referral(
        route="growth",
        source_url="https://github.com/JinNing6/TianGong/issues/7",
        actor="newbie",
        issue_number=7,
        campaign_hook="补齐首件法宝激活",
    )

    assert "IssueOps 回流已记录" in result
    assert "`activation_funnel()`" in result
    assert "`growth_flywheel()`" in result
    assert "`growth_campaign()`" in result
    assert "`public_proof_pack()`" in result
    assert "`forge_agent(name=\"your-first-artifact\"" in result
    assert recorded[0][0][0] == EVENT_ISSUEOPS_REFERRAL_RECORDED
    assert recorded[0][1]["actor"] == "newbie"
    assert recorded[0][1]["metadata"]["route"] == "growth"
    assert recorded[0][1]["metadata"]["issue_number"] == 7
    assert recorded[0][1]["metadata"]["source_url"] == "https://github.com/JinNing6/TianGong/issues/7"


@pytest.mark.asyncio
async def test_record_growth_referral_rejects_non_public_source_url(monkeypatch):
    """Referral records need reviewable public http(s) provenance."""
    from tiangong import mcp_server

    recorded = []
    monkeypatch.setattr(mcp_server, "record_activation_event", lambda *args, **kwargs: recorded.append((args, kwargs)))

    result = await mcp_server.record_growth_referral(
        route="growth",
        source_url="not-a-public-url",
        actor="newbie",
    )

    assert "回流来源纠错" in result
    assert "source_url 必须是公开 http(s) URL" in result
    assert "`record_growth_referral(route=\"growth\"" in result
    assert recorded == []


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "bad_url",
    [
        "https://github.com/JinNing6/TianGong/issues/new?template=tiangong-growth-flywheel.yml",
        "https://github.com/JinNing6/TianGong/issues/<opened-growth-issue-number>",
    ],
)
async def test_record_growth_referral_rejects_form_entrypoint_or_placeholder_urls(monkeypatch, bad_url):
    """Referral proof must be a created public URL, not an Issue Form entrypoint or placeholder."""
    from tiangong import mcp_server

    recorded = []
    monkeypatch.setattr(mcp_server, "record_activation_event", lambda *args, **kwargs: recorded.append((args, kwargs)))

    result = await mcp_server.record_growth_referral(
        route="growth",
        source_url=bad_url,
        actor="newbie",
    )

    assert "created public Issue/PR/Discussion URL" in result
    assert "issues/new" in result
    assert "`record_growth_referral(route=\"growth\"" in result
    assert recorded == []


@pytest.mark.asyncio
async def test_record_growth_referral_discloses_unwritten_event(monkeypatch):
    """If the local ledger cannot be written, the referral must not claim success."""
    from tiangong import mcp_server

    def fail_write(*args, **kwargs):
        raise PermissionError("no local ledger access")

    monkeypatch.setattr(mcp_server, "record_activation_event", fail_write)

    result = await mcp_server.record_growth_referral(
        route="growth",
        source_url="https://github.com/JinNing6/TianGong/issues/7",
        actor="newbie",
    )

    assert "IssueOps 回流未写入" in result
    assert "no local ledger access" in result
    assert "没有伪造已记录事件" in result
    assert "`activation_funnel()`" in result


@pytest.mark.asyncio
async def test_record_share_attribution_turns_public_share_into_event(monkeypatch):
    """A public contribution share should become a measurable attribution event."""
    from tiangong import mcp_server
    from tiangong.activation import EVENT_SHARE_ATTRIBUTION_RECORDED

    recorded = []
    monkeypatch.setattr(mcp_server, "record_activation_event", lambda *args, **kwargs: recorded.append((args, kwargs)))

    result = await mcp_server.record_share_attribution(
        contribution="forge",
        share_url="https://github.com/JinNing6/TianGong/issues/8",
        actor="newbie",
        artifact_name="dragon-forge",
        source_url="https://github.com/JinNing6/TianGong/issues/7",
    )

    assert "贡献分享已记录" in result
    assert "`activation_funnel()`" in result
    assert "`growth_flywheel()`" in result
    assert "`public_proof_pack()`" in result
    assert recorded[0][0][0] == EVENT_SHARE_ATTRIBUTION_RECORDED
    assert recorded[0][1]["actor"] == "newbie"
    assert recorded[0][1]["artifact_name"] == "dragon-forge"
    assert recorded[0][1]["metadata"]["contribution"] == "forge"
    assert recorded[0][1]["metadata"]["share_url"] == "https://github.com/JinNing6/TianGong/issues/8"
    assert recorded[0][1]["metadata"]["source_url"] == "https://github.com/JinNing6/TianGong/issues/7"


@pytest.mark.asyncio
async def test_record_share_attribution_requires_public_share_url(monkeypatch):
    """Share attribution should not accept unverifiable local or chat-only locations."""
    from tiangong import mcp_server

    recorded = []
    monkeypatch.setattr(mcp_server, "record_activation_event", lambda *args, **kwargs: recorded.append((args, kwargs)))

    result = await mcp_server.record_share_attribution(
        contribution="forge",
        share_url="private-chat",
        actor="newbie",
        artifact_name="dragon-forge",
    )

    assert "贡献分享来源纠错" in result
    assert "share_url 必须是公开 http(s) URL" in result
    assert "`record_share_attribution(contribution=\"forge\"" in result
    assert recorded == []


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "share_url, source_url",
    [
        ("https://github.com/JinNing6/TianGong/issues/new?template=tiangong-share-proof.yml", ""),
        ("https://github.com/JinNing6/TianGong/issues/<opened-share-issue-number>", ""),
        (
            "https://github.com/JinNing6/TianGong/issues/8",
            "https://github.com/JinNing6/TianGong/issues/new?template=tiangong-growth-flywheel.yml",
        ),
        (
            "https://github.com/JinNing6/TianGong/issues/8",
            "https://github.com/JinNing6/TianGong/issues/<opened-growth-issue-number>",
        ),
    ],
)
async def test_record_share_attribution_rejects_form_entrypoint_or_placeholder_urls(
    monkeypatch, share_url, source_url
):
    """Share proof must use created public URLs instead of Issue Form entrypoints or placeholders."""
    from tiangong import mcp_server

    recorded = []
    monkeypatch.setattr(mcp_server, "record_activation_event", lambda *args, **kwargs: recorded.append((args, kwargs)))

    result = await mcp_server.record_share_attribution(
        contribution="forge",
        share_url=share_url,
        actor="newbie",
        artifact_name="dragon-forge",
        source_url=source_url,
    )

    assert "created public post/Issue/PR/Discussion URL" in result
    assert "issues/new" in result
    assert "`record_share_attribution(contribution=\"forge\"" in result
    assert recorded == []


@pytest.mark.asyncio
async def test_record_share_attribution_discloses_unwritten_event(monkeypatch):
    """If the local ledger cannot be written, share attribution must not claim success."""
    from tiangong import mcp_server

    def fail_write(*args, **kwargs):
        raise PermissionError("no local ledger access")

    monkeypatch.setattr(mcp_server, "record_activation_event", fail_write)

    result = await mcp_server.record_share_attribution(
        contribution="forge",
        share_url="https://github.com/JinNing6/TianGong/issues/8",
        actor="newbie",
        artifact_name="dragon-forge",
    )

    assert "贡献分享未写入" in result
    assert "no local ledger access" in result
    assert "没有伪造已记录分享" in result
    assert "`activation_funnel()`" in result


@pytest.mark.asyncio
async def test_start_cultivation_records_only_entry_exposure(monkeypatch):
    """Showing the onboarding card is an exposure event, not a fake forge success."""
    from tiangong import mcp_server
    from tiangong.activation import EVENT_START_CULTIVATION_VIEWED

    recorded = []
    monkeypatch.setattr(mcp_server, "record_activation_event", lambda *args, **kwargs: recorded.append((args, kwargs)))

    result = await mcp_server.start_cultivation(username="newbie", artifact_name="dragon-forge")

    assert "起火入道" in result
    assert recorded[0][0][0] == EVENT_START_CULTIVATION_VIEWED
    assert recorded[0][1]["actor"] == "newbie"
    assert recorded[0][1]["artifact_name"] == "dragon-forge"
    assert recorded[0][1]["metadata"]["source_tool"] == "start_cultivation"


@pytest.mark.asyncio
async def test_forge_agent_records_activation_success_after_real_write(monkeypatch):
    """A forge event should be recorded only after the forge path succeeds."""
    from tiangong import mcp_server
    from tiangong.activation import EVENT_FORGE_SUCCEEDED

    async def fake_get_cultivator(username):
        return CultivatorProfile(username=username, agent_count=1)

    async def fake_forge_new_agent(**kwargs):
        return AgentSpec(agent_id="tg-123", name=kwargs["name"], creator=kwargs["creator"])

    async def fake_update_cultivator_stats(**kwargs):
        return CultivatorProfile(username=kwargs["username"], agent_count=2), False, None, None

    recorded = []
    monkeypatch.setattr(mcp_server, "get_cultivator", fake_get_cultivator)
    monkeypatch.setattr(mcp_server, "forge_new_agent", fake_forge_new_agent)
    monkeypatch.setattr(mcp_server, "update_cultivator_stats", fake_update_cultivator_stats)
    monkeypatch.setattr(mcp_server, "record_activation_event", lambda *args, **kwargs: recorded.append((args, kwargs)))

    result = await mcp_server.forge_agent(
        name="dragon-forge",
        description="A real first TianGong artifact",
        creator="newbie",
    )

    assert "开炉炼器成功" in result
    assert "record_share_attribution" in result
    assert recorded[0][0][0] == EVENT_FORGE_SUCCEEDED
    assert recorded[0][1]["actor"] == "newbie"
    assert recorded[0][1]["artifact_name"] == "dragon-forge"
    assert recorded[0][1]["metadata"]["agent_id"] == "tg-123"
