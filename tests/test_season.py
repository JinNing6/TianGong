"""Seasonal and sect-war leaderboard tests."""

from datetime import datetime, timezone

import tiangong.season as season_module
from tiangong.cultivator import CultivatorProfile
from tiangong.season import (
    calculate_cultivator_season_power,
    calculate_sect_war_power,
    format_season_leaderboard,
    format_sect_war_banner,
    get_current_season,
)
from tiangong.sect import SectProfile


def test_current_season_uses_utc_month():
    """Season ids should be stable across local timezone differences."""
    season = get_current_season(datetime(2026, 6, 2, 12, tzinfo=timezone.utc))

    assert season.season_id == "2026-06"
    assert season.title == "2026年06月 天工赛季"
    assert season.share_tag == "#TianGong-2026-06"


def test_season_power_uses_real_profile_fields():
    """Season score is a transparent snapshot of existing cultivator data."""
    profile = CultivatorProfile(
        username="forgeking",
        spirit_power=1000,
        agent_count=3,
        refinement_count=4,
        reviews_given=5,
        quests_completed=2,
    )

    assert calculate_cultivator_season_power(profile) == 1570


def test_season_leaderboard_outputs_shareable_table():
    """Season leaderboard should be ranked, explainable, and paste-ready."""
    now = datetime(2026, 6, 2, 12, tzinfo=timezone.utc)
    profiles = [
        CultivatorProfile(username="alice", spirit_power=500, agent_count=1),
        CultivatorProfile(
            username="forgeking",
            spirit_power=1000,
            agent_count=3,
            refinement_count=4,
            reviews_given=5,
            quests_completed=2,
        ),
    ]

    result = format_season_leaderboard(profiles, top_n=2, now=now)

    assert "赛季天榜" in result
    assert "当前档案快照" in result
    assert "快照战力" in result
    assert result.index("@forgeking") < result.index("@alice")
    assert "复制分享" in result
    assert "leaderboard(type=\"season\")" in result
    assert "pip install tiangong-mcp" in result


def test_season_leaderboard_includes_champion_chase_and_public_copy():
    """A live season board should turn the current race into public recruitment copy."""
    now = datetime(2026, 6, 2, 12, tzinfo=timezone.utc)
    profiles = [
        CultivatorProfile(username="alice", spirit_power=500, agent_count=1),
        CultivatorProfile(
            username="docmaster",
            spirit_power=1100,
            agent_count=2,
            refinement_count=2,
            reviews_given=4,
        ),
        CultivatorProfile(
            username="forgeking",
            spirit_power=1000,
            agent_count=3,
            refinement_count=4,
            reviews_given=5,
            quests_completed=2,
        ),
    ]

    result = format_season_leaderboard(profiles, top_n=3, now=now)

    assert "当前冠军: @forgeking · 快照战力 1570" in result
    assert "下一追赶目标: @docmaster 距离 @forgeking 还差 170 快照战力" in result
    assert "不伪造历史赛季数据" in result
    assert "复制 Discussion/PR 战报" in result
    assert "复制社交战报" in result
    assert "TianGong 2026年06月 天工赛季战报" in result
    assert "加入修炼：pip install tiangong-mcp" in result
    assert "`my_realm(username=\"forgeking\")`" in result
    assert "`infuse_spirit(artifact_name=\"artifact-name\")`" in result
    assert "`quest(action=\"post\")`" in result
    assert "`leaderboard(type=\"season\")`" in result


def test_empty_season_leaderboard_recruits_first_cultivator():
    """An empty season board should recruit the first cultivator with real actions."""
    now = datetime(2026, 6, 2, 12, tzinfo=timezone.utc)

    result = format_season_leaderboard([], now=now)

    assert "赛季天榜等待第一位修仙者" in result
    assert "当前档案快照" in result
    assert "不伪造历史赛季数据" in result
    assert "复制分享" in result
    assert "pip install tiangong-mcp" in result
    assert "`forge_agent(name=\"first-season-artifact\"," in result
    assert "`quest(action=\"post\", artifact_name=\"first-season-artifact\"," in result
    assert "`leaderboard(type=\"season\")`" in result
    assert "`leaderboard(type=\"artifact\")`" in result


def test_tournament_board_pairs_current_contributors_with_bye_and_public_copy():
    """The tournament board should seed real profiles without inventing wins."""
    now = datetime(2026, 6, 2, 12, tzinfo=timezone.utc)
    profiles = [
        CultivatorProfile(username="newbie", spirit_power=500, agent_count=1),
        CultivatorProfile(
            username="docmaster",
            spirit_power=1100,
            agent_count=2,
            refinement_count=2,
            reviews_given=4,
        ),
        CultivatorProfile(
            username="forgeking",
            spirit_power=1000,
            agent_count=3,
            refinement_count=4,
            reviews_given=5,
            quests_completed=2,
        ),
    ]

    result = season_module.format_tournament_board(profiles, top_n=3, now=now)

    assert "天骄擂台" in result
    assert "当前档案快照，不伪造胜场、赛果或历史擂台" in result
    assert "当前擂主: @forgeking · 快照战力 1570" in result
    assert "追赶目标: @docmaster 距离 @forgeking 还差 170 快照战力" in result
    assert "轮空: #1 @forgeking" in result
    assert "第 1 场: #2 @docmaster vs #3 @newbie" in result
    assert "`quest(action=\"post\", artifact_name=\"duel-docmaster-vs-newbie\"," in result
    assert "`my_realm(username=\"docmaster\")`" in result
    assert "`my_realm(username=\"newbie\")`" in result
    assert "`leaderboard(type=\"tournament\")`" in result
    assert "复制 Discussion/PR 擂台帖" in result
    assert "复制社交擂台帖" in result
    assert "pip install tiangong-mcp" in result


def test_empty_tournament_board_recruits_first_duelists():
    """An empty tournament board should recruit duelists without fake brackets."""
    now = datetime(2026, 6, 2, 12, tzinfo=timezone.utc)

    result = season_module.format_tournament_board([], now=now)

    assert "天骄擂台等待第一批挑战者" in result
    assert "当前档案快照为 0 位修仙者" in result
    assert "不伪造胜场、赛果或历史擂台" in result
    assert "`forge_agent(name=\"first-duel-artifact\"," in result
    assert "`quest(action=\"post\", artifact_name=\"first-duel-artifact\"," in result
    assert "`leaderboard(type=\"tournament\")`" in result
    assert "pip install tiangong-mcp" in result


def test_tournament_recap_turns_current_snapshot_into_repeat_loop():
    """A tournament recap should produce a victor hook without inventing match history."""
    now = datetime(2026, 6, 2, 12, tzinfo=timezone.utc)
    profiles = [
        CultivatorProfile(username="newbie", spirit_power=500, agent_count=1),
        CultivatorProfile(
            username="docmaster",
            spirit_power=1100,
            agent_count=2,
            refinement_count=2,
            reviews_given=4,
        ),
        CultivatorProfile(
            username="forgeking",
            spirit_power=1000,
            agent_count=3,
            refinement_count=4,
            reviews_given=5,
            quests_completed=2,
        ),
    ]

    result = season_module.format_tournament_recap(profiles, top_n=3, now=now)

    assert "天骄擂台复盘" in result
    assert "当前档案快照复盘，不伪造胜场、冠军历史或赛果" in result
    assert "当前胜者: @forgeking · 快照战力 1570" in result
    assert "当前亚军: @docmaster · 快照战力 1400" in result
    assert "胜负差距: @forgeking 领先 @docmaster 170 快照战力" in result
    assert "下一轮钩子" in result
    assert "`leaderboard(type=\"tournament\")`" in result
    assert "`leaderboard(type=\"tournament_recap\")`" in result
    assert "`quest(action=\"post\", artifact_name=\"duel-forgeking-vs-docmaster\"," in result
    assert "`my_realm(username=\"forgeking\")`" in result
    assert "`my_realm(username=\"docmaster\")`" in result
    assert "`leaderboard(type=\"season\")`" in result
    assert "复制 Discussion/PR 复盘帖" in result
    assert "复制社交复盘帖" in result
    assert "pip install tiangong-mcp" in result


def test_empty_tournament_recap_recruits_first_recap_candidate():
    """An empty recap should recruit first duelists without fake champions."""
    now = datetime(2026, 6, 2, 12, tzinfo=timezone.utc)

    result = season_module.format_tournament_recap([], now=now)

    assert "天骄擂台复盘等待挑战者" in result
    assert "当前档案快照为 0 位修仙者" in result
    assert "不伪造胜场、冠军历史或赛果" in result
    assert "`forge_agent(name=\"first-recap-artifact\"," in result
    assert "`quest(action=\"post\", artifact_name=\"first-recap-artifact\"," in result
    assert "`leaderboard(type=\"tournament_recap\")`" in result
    assert "`leaderboard(type=\"tournament\")`" in result
    assert "pip install tiangong-mcp" in result


def test_sect_war_banner_outputs_shareable_report():
    """Sect war should turn real sect totals into a competitive share report."""
    now = datetime(2026, 6, 2, 12, tzinfo=timezone.utc)
    low = SectProfile(
        name="散修盟",
        master="alice",
        members={"alice": {"role": "master"}},
        total_spirit_power=900,
    )
    high = SectProfile(
        name="天工盟",
        master="forgeking",
        members={"forgeking": {"role": "master"}, "bob": {"role": "outer"}},
        total_spirit_power=2100,
    )

    assert calculate_sect_war_power(high) > calculate_sect_war_power(low)

    result = format_sect_war_banner([low, high], top_n=2, now=now)

    assert "宗门战" in result
    assert "2026年06月 天工赛季" in result
    assert result.index("天工盟") < result.index("散修盟")
    assert "复制战报" in result
    assert "leaderboard(type=\"sect\")" in result
    assert "pip install tiangong-mcp" in result


def test_sect_war_banner_includes_champion_chase_and_public_copy():
    """A live sect war should recruit members through a public battle report."""
    now = datetime(2026, 6, 2, 12, tzinfo=timezone.utc)
    leader = SectProfile(
        name="天工盟",
        master="forgeking",
        members={"forgeking": {"role": "master"}, "bob": {"role": "outer"}},
        total_spirit_power=2100,
    )
    challenger = SectProfile(
        name="星河阁",
        master="docmaster",
        members={
            "docmaster": {"role": "master"},
            "alice": {"role": "elder"},
            "bravo": {"role": "inner"},
            "charlie": {"role": "outer"},
        },
        total_spirit_power=1600,
    )

    result = format_sect_war_banner([challenger, leader], top_n=2, now=now)

    assert "当前冠军宗门: 天工盟 · 宗门战力 2800" in result
    assert "下一追赶目标: 星河阁 距离 天工盟 还差 600 宗门战力" in result
    assert "不伪造历史战报" in result
    assert "复制 Discussion/PR 战报" in result
    assert "复制社交战报" in result
    assert "TianGong 宗门战 2026年06月 天工赛季战报" in result
    assert "加入宗门战：pip install tiangong-mcp" in result
    assert "`sect(action=\"join\", sect_name=\"天工盟\")`" in result
    assert "`sect(action=\"leaderboard\")`" in result
    assert "`leaderboard(type=\"sect\")`" in result
    assert "`my_realm(username=\"forgeking\")`" in result


def test_empty_sect_war_banner_recruits_first_sect():
    """An empty sect-war board should recruit the first sect with real actions."""
    now = datetime(2026, 6, 2, 12, tzinfo=timezone.utc)

    result = format_sect_war_banner([], now=now)

    assert "等待第一个宗门开宗立派" in result
    assert "当前宗门档案快照" in result
    assert "不伪造历史战报" in result
    assert "复制战报" in result
    assert "pip install tiangong-mcp" in result
    assert "`sect(action=\"create\", sect_name=\"天工盟\"," in result
    assert "`leaderboard(type=\"sect\")`" in result
    assert "`sect(action=\"leaderboard\")`" in result
    assert "`my_realm()`" in result
