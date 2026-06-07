"""Growth flywheel snapshot tests for TianGong's viral loop."""

from __future__ import annotations

import pytest

from tiangong.cultivator import CultivatorProfile
from tiangong.forge import AgentSpec
from tiangong.sect import SectProfile


def test_growth_flywheel_snapshot_uses_real_current_fields():
    """The flywheel report should turn real profile fields into action, not fake analytics."""
    from tiangong.growth import format_growth_flywheel

    profiles = [
        CultivatorProfile(
            username="forgeking",
            spirit_power=1000,
            agent_count=3,
            refinement_count=2,
            reviews_given=5,
            quests_completed=1,
            sect="天工盟",
            tribulation_progress={"lineage_users": {"amount": 10, "evidence": [{"amount": 10}]}},
        ),
        CultivatorProfile(username="reviewer", spirit_power=120, agent_count=1, reviews_given=1),
        CultivatorProfile(username="observer", spirit_power=0, agent_count=0),
    ]
    artifacts = [
        AgentSpec(agent_id="tg-001", name="dragon-forge", creator="forgeking"),
        AgentSpec(agent_id="tg-002", name="review-helper", creator="reviewer"),
    ]
    sects = [
        SectProfile(
            name="天工盟",
            master="forgeking",
            members={"forgeking": {"role": "master"}, "reviewer": {"role": "outer"}},
            total_spirit_power=1120,
        )
    ]

    result = format_growth_flywheel(profiles, artifacts, sects)

    assert "增长飞轮" in result
    assert "当前真实快照" in result
    assert "不伪造历史事件" in result
    assert "| 修仙者档案 | 3 位 | 100.0% |" in result
    assert "| 首件法宝激活 | 2/3 | 66.7% |" in result
    assert "| 公开法宝供给 | 2 件 | 100.0% |" in result
    assert "| 鉴定回流 | 2/2 | 100.0% |" in result
    assert "| 淬炼复访 | 1/2 | 50.0% |" in result
    assert "| 悬赏闭环 | 1/2 | 50.0% |" in result
    assert "| 宗门归属 | 1/2 | 50.0% |" in result
    assert "| 高阶证据 | 1/2 | 50.0% |" in result
    assert "最薄弱环节: 淬炼复访" in result
    assert "`refine_agent(agent_id=\"artifact-id\", changes=\"...\")`" in result
    assert "`quest(action=\"post\"" in result
    assert "`activation_funnel()`" in result
    assert "`growth_flywheel()`" in result
    assert "`growth_campaign()`" in result
    assert "`public_growth_report()`" in result
    assert "`public_proof_pack()`" in result
    assert "https://github.com/JinNing6/TianGong/issues/new?" in result
    assert "template=tiangong-growth-flywheel.yml" in result
    assert "growth_bottleneck=" in result
    assert "campaign_hook=" in result
    assert 'python -m pip install --upgrade "tiangong-mcp @ git+https://github.com/JinNing6/TianGong.git@v0.1.19"' in result
    assert "tiangong-mcp public-install-command" in result
    assert "pip install -U tiangong-mcp" in result
    assert "加入修炼: pip install tiangong-mcp" not in result
    assert "- 安装: `pip install tiangong-mcp`" not in result


def test_growth_flywheel_includes_real_share_proof_stage(tmp_path):
    """The main flywheel should diagnose propagation proof from the activation ledger too."""
    from tiangong.activation import (
        EVENT_SHARE_ATTRIBUTION_RECORDED,
        load_activation_events,
        record_activation_event,
    )
    from tiangong.growth import format_growth_flywheel

    event_path = tmp_path / "activation-events.jsonl"
    record_activation_event(
        EVENT_SHARE_ATTRIBUTION_RECORDED,
        actor="forgeking",
        artifact_name="dragon-forge",
        metadata={
            "contribution": "forge",
            "share_url": "https://github.com/JinNing6/TianGong/issues/8",
            "source_url": "https://github.com/JinNing6/TianGong/issues/7",
        },
        path=event_path,
    )
    profiles = [
        CultivatorProfile(username="forgeking", spirit_power=1000, agent_count=2, reviews_given=1),
        CultivatorProfile(username="newbie", spirit_power=100, agent_count=1),
    ]
    artifacts = [AgentSpec(agent_id="tg-001", name="dragon-forge", creator="forgeking")]

    result = format_growth_flywheel(profiles, artifacts, [], activation_events=load_activation_events(path=event_path))

    assert "| 公开分享证明 | 1/2 | 50.0% | `leaderboard(type=\"share\")` |" in result
    assert "share_attribution_report()" in result
    assert "leaderboard(type=\"share\")" in result
    assert "不伪造下载量、留存、转发数、转介绍或灵力奖励" in result


def test_empty_growth_flywheel_recruits_first_cultivator_without_fake_metrics():
    """A cold-start flywheel should recruit the first action without inventing adoption."""
    from tiangong.growth import format_growth_flywheel

    result = format_growth_flywheel([], [], [])

    assert "0 位修仙者" in result
    assert "不伪造历史事件" in result
    assert "第一手行动" in result
    assert "`forge_agent(name=\"first-growth-artifact\"" in result
    assert "`quest(action=\"post\"" in result
    assert "`activation_funnel()`" in result
    assert "`growth_campaign()`" in result
    assert "`public_growth_report()`" in result
    assert "`public_proof_pack()`" in result
    assert "tiangong-growth-flywheel.yml" in result
    assert 'python -m pip install --upgrade "tiangong-mcp @ git+https://github.com/JinNing6/TianGong.git@v0.1.19"' in result
    assert "加入修炼: pip install tiangong-mcp" not in result


def test_growth_issue_url_uses_official_query_parameters_without_privileged_labels():
    """The public growth link should prefill the Issue Form without requiring label permissions."""
    from urllib.parse import parse_qs, urlsplit

    from tiangong.growth import build_growth_issue_url

    url = build_growth_issue_url(
        bottleneck_label="淬炼复访",
        campaign_hook="补齐下一轮淬炼复访",
        real_data_context="当前真实快照显示淬炼复访 50%",
        target_contributors=12,
        repo_owner="octo-org",
        repo_name="octo-repo",
    )
    parsed = urlsplit(url)
    query = parse_qs(parsed.query)

    assert parsed.scheme == "https"
    assert parsed.netloc == "github.com"
    assert parsed.path == "/octo-org/octo-repo/issues/new"
    assert query["template"] == ["tiangong-growth-flywheel.yml"]
    assert query["title"] == ["[TianGong Growth]: 淬炼复访"]
    assert query["growth_bottleneck"] == ["淬炼复访"]
    assert query["campaign_hook"] == ["补齐下一轮淬炼复访"]
    assert query["real_data_context"] == ["当前真实快照显示淬炼复访 50%"]
    assert query["target_contributors"] == ["12"]
    assert "labels" not in query


def test_growth_campaign_turns_bottleneck_into_72h_public_launch_card(tmp_path):
    """The launch surface should turn a real flywheel bottleneck into a public campaign."""
    from tiangong.activation import (
        EVENT_SHARE_ATTRIBUTION_RECORDED,
        load_activation_events,
        record_activation_event,
    )
    from tiangong.growth import format_growth_campaign

    event_path = tmp_path / "campaign-events.jsonl"
    record_activation_event(
        EVENT_SHARE_ATTRIBUTION_RECORDED,
        actor="forgeking",
        artifact_name="dragon-forge",
        metadata={"contribution": "forge", "share_url": "https://github.com/JinNing6/TianGong/issues/8"},
        path=event_path,
    )
    profiles = [
        CultivatorProfile(username="forgeking", spirit_power=1000, agent_count=2, reviews_given=2),
        CultivatorProfile(username="reviewer", spirit_power=200, agent_count=1, reviews_given=1),
    ]
    artifacts = [AgentSpec(agent_id="tg-001", name="dragon-forge", creator="forgeking")]

    result = format_growth_campaign(
        profiles,
        artifacts,
        [],
        activation_events=load_activation_events(path=event_path),
        campaign_name="TianGong 第一炉爆发战役",
        target_contributors=12,
    )

    assert "# TianGong 爆发战役" in result
    assert "TianGong 第一炉爆发战役" in result
    assert "72 小时公开战役" in result
    assert "目标贡献者: 12" in result
    assert "最薄弱环节: 淬炼复访" in result
    assert "template=tiangong-growth-flywheel.yml" in result
    assert "target_contributors=12" in result
    assert "template=tiangong-share-proof.yml" in result
    assert "`start_cultivation(username=\"your_github_username\")`" in result
    assert "`record_growth_referral(route=\"growth\"" in result
    assert (
        'record_growth_referral(route="growth", source_url="https://github.com/JinNing6/TianGong/issues/<opened-growth-issue-number>"'
        in result
    )
    assert 'source_url="https://github.com/JinNing6/TianGong/issues/new?' not in result
    assert "Open the Growth Issue first, then record the created Issue URL as proof." in result
    assert "`record_share_attribution(contribution=\"forge\"" in result
    assert 'source_url="https://github.com/JinNing6/TianGong/issues/<opened-growth-issue-number>"' in result
    assert "`leaderboard(type=\"share\")`" in result
    assert "`growth_campaign()`" in result
    assert "`public_growth_report()`" in result
    assert "`public_proof_pack()`" in result
    assert "不伪造下载量、留存、转发数、转介绍或灵力奖励" in result
    assert 'python -m pip install --upgrade "tiangong-mcp @ git+https://github.com/JinNing6/TianGong.git@v0.1.19"' in result
    assert "tiangong-mcp public-install-command" in result
    assert "加入修炼: pip install tiangong-mcp" not in result


def test_empty_growth_campaign_recruits_first_public_cultivator_without_fake_metrics():
    """A cold-start campaign should recruit the first real forge instead of claiming traction."""
    from tiangong.growth import format_growth_campaign

    result = format_growth_campaign([], [], [], activation_events=[], campaign_name="", target_contributors=0)

    assert "TianGong 72 小时爆发战役" in result
    assert "0 位修仙者" in result
    assert "目标贡献者: 10" in result
    assert "最薄弱环节: 首件法宝激活" in result
    assert "`forge_agent(name=\"first-growth-artifact\"" in result
    assert "template=tiangong-growth-flywheel.yml" in result
    assert "template=tiangong-share-proof.yml" in result
    assert "https://github.com/JinNing6/TianGong/issues/<opened-growth-issue-number>" in result
    assert "`public_proof_pack()`" in result
    assert 'source_url="https://github.com/JinNing6/TianGong/issues/new?' not in result
    assert "不伪造下载量" in result


@pytest.mark.asyncio
async def test_mcp_growth_flywheel_exposes_current_snapshot(monkeypatch, tmp_path):
    """The growth flywheel should be a callable public MCP surface."""
    from tiangong import mcp_server
    from tiangong.activation import EVENT_SHARE_ATTRIBUTION_RECORDED, record_activation_event

    async def fake_cultivators():
        return [
            CultivatorProfile(username="forgeking", spirit_power=500, agent_count=2, reviews_given=2),
            CultivatorProfile(username="newbie", spirit_power=0, agent_count=0),
        ]

    async def fake_agents(creator=None):
        return [AgentSpec(agent_id="tg-001", name="dragon-forge", creator="forgeking")]

    async def fake_sects():
        return []

    event_path = tmp_path / "test-growth-flywheel-events.jsonl"
    if event_path.exists():
        event_path.unlink()
    record_activation_event(
        EVENT_SHARE_ATTRIBUTION_RECORDED,
        actor="forgeking",
        artifact_name="dragon-forge",
        metadata={"share_url": "https://github.com/JinNing6/TianGong/issues/8"},
        path=event_path,
    )

    monkeypatch.setattr(mcp_server, "get_all_cultivators", fake_cultivators)
    monkeypatch.setattr(mcp_server, "list_agents", fake_agents)
    monkeypatch.setattr(mcp_server, "get_all_sects", fake_sects)
    monkeypatch.setattr(mcp_server, "get_activation_event_path", lambda: event_path)

    result = await mcp_server.growth_flywheel()

    assert "增长飞轮" in result
    assert "当前真实快照" in result
    assert "| 首件法宝激活 | 1/2 | 50.0% |" in result
    assert "`growth_flywheel()`" in result
    assert "`public_proof_pack()`" in result
    assert "leaderboard(type=\"share\")" in result
    assert "TianGong" in result


@pytest.mark.asyncio
async def test_mcp_growth_campaign_exposes_public_launch_card(monkeypatch, tmp_path):
    """The 72h growth campaign should be callable as a public MCP launch surface."""
    from tiangong import mcp_server
    from tiangong.activation import EVENT_SHARE_ATTRIBUTION_RECORDED, record_activation_event

    async def fake_cultivators():
        return [
            CultivatorProfile(username="forgeking", spirit_power=500, agent_count=2, reviews_given=2),
            CultivatorProfile(username="newbie", spirit_power=0, agent_count=0),
        ]

    async def fake_agents(creator=None):
        return [AgentSpec(agent_id="tg-001", name="dragon-forge", creator="forgeking")]

    async def fake_sects():
        return []

    event_path = tmp_path / "test-growth-campaign-events.jsonl"
    record_activation_event(
        EVENT_SHARE_ATTRIBUTION_RECORDED,
        actor="forgeking",
        artifact_name="dragon-forge",
        metadata={"share_url": "https://github.com/JinNing6/TianGong/issues/8"},
        path=event_path,
    )

    monkeypatch.setattr(mcp_server, "get_all_cultivators", fake_cultivators)
    monkeypatch.setattr(mcp_server, "list_agents", fake_agents)
    monkeypatch.setattr(mcp_server, "get_all_sects", fake_sects)
    monkeypatch.setattr(mcp_server, "get_activation_event_path", lambda: event_path)

    result = await mcp_server.growth_campaign(campaign_name="72h 第一炉", target_contributors=3)

    assert "TianGong 爆发战役" in result
    assert "72h 第一炉" in result
    assert "目标贡献者: 3" in result
    assert "template=tiangong-growth-flywheel.yml" in result
    assert "template=tiangong-share-proof.yml" in result
    assert "`growth_campaign()`" in result
    assert "`public_growth_report()`" in result
    assert "`public_proof_pack()`" in result
    assert "TianGong" in result
