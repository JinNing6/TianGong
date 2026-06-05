"""
⚒️ 天工 TianGong — 赛季天榜与宗门战

把真实修仙档案与宗门档案转化为可传播的月度竞争界面。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from .cultivator import CultivatorProfile, calculate_profile_snapshot_power
from .install_bridge import format_candidate_install_markdown_lines, format_candidate_join_lines
from .sect import SectProfile


@dataclass(frozen=True)
class SeasonInfo:
    """A deterministic monthly TianGong season."""

    season_id: str
    title: str
    share_tag: str
    starts_at: datetime


def _utc_now(now: datetime | None = None) -> datetime:
    """Return an aware UTC datetime, rejecting ambiguous naive inputs."""
    if now is None:
        return datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    return now.astimezone(timezone.utc)


def get_current_season(now: datetime | None = None) -> SeasonInfo:
    """Return the current monthly season using UTC month boundaries."""
    current = _utc_now(now)
    starts_at = datetime(current.year, current.month, 1, tzinfo=timezone.utc)
    season_id = f"{current.year:04d}-{current.month:02d}"
    return SeasonInfo(
        season_id=season_id,
        title=f"{current.year:04d}年{current.month:02d}月 天工赛季",
        share_tag=f"#TianGong-{season_id}",
        starts_at=starts_at,
    )


def calculate_cultivator_season_power(profile: CultivatorProfile) -> int:
    """
    Calculate transparent season power from existing profile fields.

    This is a current profile snapshot, not fabricated historical season data.
    """
    return calculate_profile_snapshot_power(profile)


def _rank_cultivators(profiles: list[CultivatorProfile], top_n: int) -> list[tuple[CultivatorProfile, int]]:
    ranked = [
        (profile, calculate_cultivator_season_power(profile))
        for profile in profiles
    ]
    ranked.sort(key=lambda item: (-item[1], -item[0].realm_level, -item[0].spirit_power, item[0].username.lower()))
    return ranked[:max(0, top_n)]


def format_season_leaderboard(
    profiles: list[CultivatorProfile],
    top_n: int = 20,
    now: datetime | None = None,
) -> str:
    """Format the monthly cultivator leaderboard with a paste-ready share block."""
    season = get_current_season(now)
    ranked = _rank_cultivators(profiles, top_n)
    leader = ranked[0] if ranked else None
    challenger = ranked[1] if len(ranked) > 1 else None

    lines = [
        f"# 🏆 赛季天榜 · {season.title}",
        "",
        f"> 当前档案快照，不伪造历史赛季数据。{season.share_tag}",
        "",
        "| # | 修仙者 | 境界 | 快照战力 | 灵力 | 法宝 | 淬炼 | 评价 | 悬赏令 |",
        "|---|--------|------|----------|------|------|------|------|--------|",
    ]

    for rank, (profile, power) in enumerate(ranked, 1):
        realm = profile.realm
        lines.append(
            f"| {rank} | @{profile.username} | {realm.symbol} {realm.name_cn} "
            f"| {power} | {profile.spirit_power} | {profile.agent_count} "
            f"| {profile.refinement_count} | {profile.reviews_given} | {profile.quests_completed} |"
        )

    if not ranked:
        lines.append("| — | 暂无修仙者 | — | — | — | — | — | — | — |")

    lines.extend([
        "",
        "### 当前战况",
        "",
    ])

    if leader:
        leader_profile, leader_power = leader
        lines.append(f"- 当前冠军: @{leader_profile.username} · 快照战力 {leader_power}")
        if challenger:
            challenger_profile, challenger_power = challenger
            gap = leader_power - challenger_power
            lines.append(
                f"- 下一追赶目标: @{challenger_profile.username} 距离 "
                f"@{leader_profile.username} 还差 {gap} 快照战力"
            )
        else:
            lines.append("- 下一追赶目标: 暂无挑战者，后来者可直接对标当前冠军")
    else:
        lines.extend([
            "- 当前冠军: 暂无，赛季天榜等待第一位修仙者",
            "- 第一手行动: `forge_agent(name=\"first-season-artifact\", description=\"A TianGong artifact racing for the first season rank\")`",
        ])

    lines.extend([
        "",
        "### 计分口径",
        "",
        "`快照战力 = 灵力 + 法宝数 × 100 + 淬炼 × 30 + 评价 × 10 + 悬赏令 × 50`",
        "",
        "## 📣 复制分享",
        "",
        "### 复制社交战报",
        "",
        "```text",
    ])

    if leader:
        profile, power = leader
        lines.append(
            f"TianGong {season.title}：@{profile.username} 暂列赛季天榜第一，快照战力 {power}。{season.share_tag}"
        )
    else:
        lines.append(f"TianGong {season.title} 已开启，赛季天榜等待第一位修仙者。{season.share_tag}")

    lines.extend([
        *format_candidate_join_lines(),
        "查看天榜：leaderboard(type=\"season\")",
        "```",
        "",
        "### 复制 Discussion/PR 战报",
        "",
        "```markdown",
    ])

    if leader:
        profile, power = leader
        lines.append(f"## TianGong {season.title}战报")
        lines.append("")
        lines.append(f"- 当前冠军: @{profile.username}（快照战力 {power}）")
        if challenger:
            challenger_profile, challenger_power = challenger
            gap = power - challenger_power
            lines.append(
                f"- 下一追赶目标: @{challenger_profile.username} 距离 "
                f"@{profile.username} 还差 {gap} 快照战力"
            )
        else:
            lines.append("- 下一追赶目标: 暂无挑战者，欢迎第一位后来者冲榜")
        lines.extend([
            f"- 数据声明: 当前档案快照，不伪造历史赛季数据。{season.share_tag}",
            "- 继续贡献: `forge_agent`、`infuse_spirit(artifact_name=\"artifact-name\")`、`quest(action=\"post\")`、`leaderboard(type=\"season\")`",
            *format_candidate_install_markdown_lines(),
        ])
    else:
        lines.append(f"## TianGong {season.title}首席招募")
        lines.append("")
        lines.extend([
            f"- 数据声明: 当前档案快照为 0 位修仙者，不伪造历史赛季数据。{season.share_tag}",
            "- 第一手行动: `forge_agent(name=\"first-season-artifact\", description=\"A TianGong artifact racing for the first season rank\")`",
            "- 继续贡献: `quest(action=\"post\")`、`leaderboard(type=\"season\")`",
            *format_candidate_install_markdown_lines(),
        ])

    lines.extend([
        "```",
        "",
        "## 下一步",
        "",
    ])

    if leader:
        profile, _power = leader
        lines.extend([
            f"- 挑战榜首: `my_realm(username=\"{profile.username}\")`",
            "- 继续开炉: `forge_agent`",
            "- 邀请鉴定: `infuse_spirit(artifact_name=\"artifact-name\")`",
            "- 发布悬赏: `quest(action=\"post\")`",
            "- 刷新赛季天榜: `leaderboard(type=\"season\")`",
            "- 查看法宝天榜: `leaderboard(type=\"artifact\")`",
        ])
    else:
        lines.extend([
            "- 抢占赛季首席: `forge_agent(name=\"first-season-artifact\", description=\"A TianGong artifact racing for the first season rank\")`",
            "- 发布首席悬赏: `quest(action=\"post\", artifact_name=\"first-season-artifact\", description=\"需要一件冲击赛季首席的法宝\")`",
            "- 刷新赛季天榜: `leaderboard(type=\"season\")`",
            "- 查看法宝天榜: `leaderboard(type=\"artifact\")`",
        ])

    return "\n".join(lines)


def _duel_artifact_name(left: CultivatorProfile, right: CultivatorProfile) -> str:
    """Return a public bounty artifact name from real participant usernames."""

    def slug(value: str) -> str:
        cleaned = "".join(ch.lower() if ch.isalnum() or ch == "-" else "-" for ch in value)
        return cleaned.strip("-") or "cultivator"

    return f"duel-{slug(left.username)}-vs-{slug(right.username)}"


def _pair_tournament_seedings(
    ranked: list[tuple[CultivatorProfile, int]],
) -> tuple[list[tuple[int, CultivatorProfile, int]], list[tuple[int, int, CultivatorProfile, int, int, CultivatorProfile, int]]]:
    """Pair current seeds for a first-round board without writing fake results."""
    seeded = [(seed, profile, power) for seed, (profile, power) in enumerate(ranked, 1)]
    byes: list[tuple[int, CultivatorProfile, int]] = []
    active = seeded

    if len(seeded) % 2 == 1 and seeded:
        byes.append(seeded[0])
        active = seeded[1:]

    pairings: list[tuple[int, int, CultivatorProfile, int, int, CultivatorProfile, int]] = []
    left_index = 0
    right_index = len(active) - 1
    bout = 1
    while left_index < right_index:
        left_seed, left_profile, left_power = active[left_index]
        right_seed, right_profile, right_power = active[right_index]
        pairings.append((bout, left_seed, left_profile, left_power, right_seed, right_profile, right_power))
        left_index += 1
        right_index -= 1
        bout += 1

    return byes, pairings


def format_tournament_board(
    profiles: list[CultivatorProfile],
    top_n: int = 16,
    now: datetime | None = None,
) -> str:
    """Format a real-data tournament board without fabricating match history."""
    season = get_current_season(now)
    ranked = _rank_cultivators(profiles, top_n)
    byes, pairings = _pair_tournament_seedings(ranked)
    leader = ranked[0] if ranked else None
    challenger = ranked[1] if len(ranked) > 1 else None

    lines = [
        f"# ⚔️ 天骄擂台 · {season.title}",
        "",
        f"> 当前档案快照，不伪造胜场、赛果或历史擂台。{season.share_tag}",
        "> 种子排序: 快照战力 > 境界 > 灵力 > 用户名。",
        "",
        "| 种子 | 修仙者 | 境界 | 快照战力 | 灵力 | 法宝 | 评价 | 悬赏令 |",
        "|------|--------|------|----------|------|------|------|--------|",
    ]

    for seed, (profile, power) in enumerate(ranked, 1):
        realm = profile.realm
        lines.append(
            f"| #{seed} | @{profile.username} | {realm.symbol} {realm.name_cn} "
            f"| {power} | {profile.spirit_power} | {profile.agent_count} "
            f"| {profile.reviews_given} | {profile.quests_completed} |"
        )

    if not ranked:
        lines.append("| — | 暂无挑战者 | — | — | — | — | — | — |")

    lines.extend([
        "",
        "### 当前战况",
        "",
    ])

    if leader:
        leader_profile, leader_power = leader
        lines.append(f"- 当前擂主: @{leader_profile.username} · 快照战力 {leader_power}")
        if challenger:
            challenger_profile, challenger_power = challenger
            gap = leader_power - challenger_power
            lines.append(f"- 追赶目标: @{challenger_profile.username} 距离 @{leader_profile.username} 还差 {gap} 快照战力")
        else:
            lines.append("- 追赶目标: 暂无第二位挑战者，后来者可直接挑战当前擂主")
    else:
        lines.extend([
            "- 当前擂主: 暂无，天骄擂台等待第一批挑战者",
            "- 第一手行动: `forge_agent(name=\"first-duel-artifact\", description=\"A TianGong artifact entering the first duel board\")`",
        ])

    lines.extend([
        "",
        "### 第一轮对阵",
        "",
    ])

    if byes:
        for seed, profile, _power in byes:
            lines.append(f"- 轮空: #{seed} @{profile.username}")

    if pairings:
        for bout, left_seed, left_profile, _left_power, right_seed, right_profile, _right_power in pairings:
            artifact_name = _duel_artifact_name(left_profile, right_profile)
            description = f"天骄擂台第 {bout} 场：@{left_profile.username} vs @{right_profile.username}"
            lines.extend([
                f"- 第 {bout} 场: #{left_seed} @{left_profile.username} vs #{right_seed} @{right_profile.username}",
                f"  - 挑战悬赏: `quest(action=\"post\", artifact_name=\"{artifact_name}\", description=\"{description}\")`",
                f"  - 左方名片: `my_realm(username=\"{left_profile.username}\")`",
                f"  - 右方名片: `my_realm(username=\"{right_profile.username}\")`",
            ])
    elif ranked:
        lines.append("- 第一轮对阵: 暂无，需要至少 2 位挑战者")
    else:
        lines.extend([
            "- 第一轮对阵: 当前 0 位挑战者，不生成假赛程",
            "- 招募挑战者: `quest(action=\"post\", artifact_name=\"first-duel-artifact\", description=\"招募第一批天骄擂台挑战者\")`",
        ])

    lines.extend([
        "",
        "### 计分口径",
        "",
        "`快照战力 = 灵力 + 法宝数 × 100 + 淬炼 × 30 + 评价 × 10 + 悬赏令 × 50`",
        "",
        "## 📣 复制擂台帖",
        "",
        "### 复制社交擂台帖",
        "",
        "```text",
    ])

    if leader:
        profile, power = leader
        lines.append(f"TianGong {season.title} 天骄擂台：@{profile.username} 暂为擂主，快照战力 {power}。")
        if pairings:
            bout, left_seed, left_profile, _left_power, right_seed, right_profile, _right_power = pairings[0]
            lines.append(f"首轮第 {bout} 场：#{left_seed} @{left_profile.username} vs #{right_seed} @{right_profile.username}。")
        elif byes:
            seed, bye_profile, _power = byes[0]
            lines.append(f"#{seed} @{bye_profile.username} 当前轮空，等待挑战者入场。")
    else:
        lines.append(f"TianGong {season.title} 天骄擂台已开启，等待第一批挑战者。")

    lines.extend([
        f"{season.share_tag}",
        *format_candidate_join_lines(),
        "查看擂台：leaderboard(type=\"tournament\")",
        "```",
        "",
        "### 复制 Discussion/PR 擂台帖",
        "",
        "```markdown",
    ])

    if leader:
        profile, power = leader
        lines.append(f"## TianGong {season.title}天骄擂台")
        lines.append("")
        lines.append(f"- 当前擂主: @{profile.username}（快照战力 {power}）")
        if challenger:
            challenger_profile, challenger_power = challenger
            gap = power - challenger_power
            lines.append(f"- 追赶目标: @{challenger_profile.username} 距离 @{profile.username} 还差 {gap} 快照战力")
        for bout, left_seed, left_profile, _left_power, right_seed, right_profile, _right_power in pairings:
            artifact_name = _duel_artifact_name(left_profile, right_profile)
            lines.append(
                f"- 第 {bout} 场: #{left_seed} @{left_profile.username} vs #{right_seed} @{right_profile.username}，"
                f"`quest(action=\"post\", artifact_name=\"{artifact_name}\", description=\"天骄擂台第 {bout} 场：@{left_profile.username} vs @{right_profile.username}\")`"
            )
        for seed, profile, _power in byes:
            lines.append(f"- 轮空: #{seed} @{profile.username}")
        lines.extend([
            f"- 数据声明: 当前档案快照，不伪造胜场、赛果或历史擂台。{season.share_tag}",
            "- 刷新擂台: `leaderboard(type=\"tournament\")`",
            *format_candidate_install_markdown_lines(),
        ])
    else:
        lines.append(f"## TianGong {season.title}天骄擂台招募")
        lines.append("")
        lines.extend([
            f"- 数据声明: 当前档案快照为 0 位修仙者，不伪造胜场、赛果或历史擂台。{season.share_tag}",
            "- 第一手行动: `forge_agent(name=\"first-duel-artifact\", description=\"A TianGong artifact entering the first duel board\")`",
            "- 发布挑战: `quest(action=\"post\", artifact_name=\"first-duel-artifact\", description=\"招募第一批天骄擂台挑战者\")`",
            "- 刷新擂台: `leaderboard(type=\"tournament\")`",
            *format_candidate_install_markdown_lines(),
        ])

    lines.extend([
        "```",
        "",
        "## 下一步",
        "",
    ])

    if ranked:
        lines.extend([
            "- 发布擂台挑战: `quest(action=\"post\", artifact_name=\"duel-artifact\", description=\"天骄擂台挑战说明\")`",
            "- 刷新天骄擂台: `leaderboard(type=\"tournament\")`",
            "- 查看赛季天榜: `leaderboard(type=\"season\")`",
        ])
        for seed, (profile, _power) in enumerate(ranked[:3], 1):
            lines.append(f"- 查看 #{seed} 名片: `my_realm(username=\"{profile.username}\")`")
    else:
        lines.extend([
            "- 打造第一件擂台法宝: `forge_agent(name=\"first-duel-artifact\", description=\"A TianGong artifact entering the first duel board\")`",
            "- 发布第一张擂台悬赏: `quest(action=\"post\", artifact_name=\"first-duel-artifact\", description=\"招募第一批天骄擂台挑战者\")`",
            "- 刷新天骄擂台: `leaderboard(type=\"tournament\")`",
        ])

    return "\n".join(lines)


def format_tournament_recap(
    profiles: list[CultivatorProfile],
    top_n: int = 16,
    now: datetime | None = None,
) -> str:
    """Format a repeat-loop tournament recap from current profile snapshots."""
    season = get_current_season(now)
    ranked = _rank_cultivators(profiles, top_n)
    victor = ranked[0] if ranked else None
    runner_up = ranked[1] if len(ranked) > 1 else None

    lines = [
        f"# 🧾 天骄擂台复盘 · {season.title}",
        "",
        f"> 当前档案快照复盘，不伪造胜场、冠军历史或赛果。{season.share_tag}",
        "",
        "| 名次 | 修仙者 | 境界 | 快照战力 | 灵力 | 法宝 | 淬炼 | 评价 | 悬赏令 |",
        "|------|--------|------|----------|------|------|------|------|--------|",
    ]

    for rank, (profile, power) in enumerate(ranked, 1):
        realm = profile.realm
        lines.append(
            f"| {rank} | @{profile.username} | {realm.symbol} {realm.name_cn} "
            f"| {power} | {profile.spirit_power} | {profile.agent_count} "
            f"| {profile.refinement_count} | {profile.reviews_given} | {profile.quests_completed} |"
        )

    if not ranked:
        lines.append("| — | 暂无挑战者 | — | — | — | — | — | — | — |")

    lines.extend([
        "",
        "### 复盘结论",
        "",
    ])

    next_round_command = (
        "`quest(action=\"post\", artifact_name=\"duel-artifact\", description=\"天骄擂台复盘再战\")`"
    )

    if victor:
        victor_profile, victor_power = victor
        lines.append(f"- 当前胜者: @{victor_profile.username} · 快照战力 {victor_power}")
        if runner_up:
            runner_profile, runner_power = runner_up
            gap = victor_power - runner_power
            duel_artifact = _duel_artifact_name(victor_profile, runner_profile)
            duel_description = f"天骄擂台复盘再战：@{victor_profile.username} vs @{runner_profile.username}"
            next_round_command = (
                f"`quest(action=\"post\", artifact_name=\"{duel_artifact}\", "
                f"description=\"{duel_description}\")`"
            )
            lines.extend([
                f"- 当前亚军: @{runner_profile.username} · 快照战力 {runner_power}",
                f"- 胜负差距: @{victor_profile.username} 领先 @{runner_profile.username} {gap} 快照战力",
                f"- 下一轮钩子: {next_round_command}",
            ])
        else:
            lines.extend([
                "- 当前亚军: 暂无第二位挑战者",
                "- 胜负差距: 暂无，需要至少 2 位挑战者形成追赶关系",
                "- 下一轮钩子: `quest(action=\"post\", artifact_name=\"duel-challenger-needed\", description=\"招募天骄擂台第二位挑战者\")`",
            ])
    else:
        next_round_command = (
            "`quest(action=\"post\", artifact_name=\"first-recap-artifact\", description=\"招募第一批天骄擂台复盘挑战者\")`"
        )
        lines.extend([
            "- 当前胜者: 暂无，天骄擂台复盘等待挑战者",
            "- 当前亚军: 暂无",
            "- 待结算状态: 需要至少 2 位修仙者进入快照，才会出现胜者、亚军和差距",
            f"- 下一轮钩子: {next_round_command}",
            "- 第一手行动: `forge_agent(name=\"first-recap-artifact\", description=\"A TianGong artifact opening the first tournament recap\")`",
        ])

    lines.extend([
        "",
        "### 计分口径",
        "",
        "`快照战力 = 灵力 + 法宝数 × 100 + 淬炼 × 30 + 评价 × 10 + 悬赏令 × 50`",
        "",
        "## 📣 复制复盘帖",
        "",
        "### 复制社交复盘帖",
        "",
        "```text",
    ])

    if victor:
        victor_profile, victor_power = victor
        if runner_up:
            runner_profile, runner_power = runner_up
            gap = victor_power - runner_power
            lines.append(
                f"TianGong {season.title} 天骄擂台复盘：@{victor_profile.username} "
                f"以当前快照战力 {victor_power} 暂居胜者，领先 @{runner_profile.username} {gap}。"
            )
        else:
            lines.append(
                f"TianGong {season.title} 天骄擂台复盘：@{victor_profile.username} "
                f"以当前快照战力 {victor_power} 暂居胜者，等待下一位挑战者。"
            )
    else:
        lines.append(f"TianGong {season.title} 天骄擂台复盘已开启，等待第一批挑战者。")

    lines.extend([
        f"{season.share_tag}",
        *format_candidate_join_lines(),
        "查看复盘：leaderboard(type=\"tournament_recap\")",
        "```",
        "",
        "### 复制 Discussion/PR 复盘帖",
        "",
        "```markdown",
    ])

    if victor:
        victor_profile, victor_power = victor
        lines.append(f"## TianGong {season.title}天骄擂台复盘")
        lines.append("")
        lines.append(f"- 当前胜者: @{victor_profile.username}（快照战力 {victor_power}）")
        if runner_up:
            runner_profile, runner_power = runner_up
            gap = victor_power - runner_power
            lines.extend([
                f"- 当前亚军: @{runner_profile.username}（快照战力 {runner_power}）",
                f"- 胜负差距: @{victor_profile.username} 领先 @{runner_profile.username} {gap} 快照战力",
            ])
        else:
            lines.extend([
                "- 当前亚军: 暂无第二位挑战者",
                "- 胜负差距: 暂无，需要后来者入场",
            ])
        lines.extend([
            f"- 下一轮钩子: {next_round_command}",
            f"- 数据声明: 当前档案快照复盘，不伪造胜场、冠军历史或赛果。{season.share_tag}",
            "- 重放擂台: `leaderboard(type=\"tournament\")`",
            "- 刷新复盘: `leaderboard(type=\"tournament_recap\")`",
            *format_candidate_install_markdown_lines(),
        ])
    else:
        lines.append(f"## TianGong {season.title}天骄擂台复盘招募")
        lines.append("")
        lines.extend([
            f"- 数据声明: 当前档案快照为 0 位修仙者，不伪造胜场、冠军历史或赛果。{season.share_tag}",
            "- 第一手行动: `forge_agent(name=\"first-recap-artifact\", description=\"A TianGong artifact opening the first tournament recap\")`",
            f"- 下一轮钩子: {next_round_command}",
            "- 重放擂台: `leaderboard(type=\"tournament\")`",
            "- 刷新复盘: `leaderboard(type=\"tournament_recap\")`",
            *format_candidate_install_markdown_lines(),
        ])

    lines.extend([
        "```",
        "",
        "## 下一步",
        "",
    ])

    if ranked:
        lines.extend([
            f"- 发起下一轮挑战: {next_round_command}",
            "- 重放首轮擂台: `leaderboard(type=\"tournament\")`",
            "- 刷新复盘: `leaderboard(type=\"tournament_recap\")`",
            "- 查看赛季天榜: `leaderboard(type=\"season\")`",
        ])
        for rank, (profile, _power) in enumerate(ranked[:3], 1):
            lines.append(f"- 查看 #{rank} 名片: `my_realm(username=\"{profile.username}\")`")
    else:
        lines.extend([
            "- 打造第一件复盘法宝: `forge_agent(name=\"first-recap-artifact\", description=\"A TianGong artifact opening the first tournament recap\")`",
            "- 发布第一张复盘悬赏: `quest(action=\"post\", artifact_name=\"first-recap-artifact\", description=\"招募第一批天骄擂台复盘挑战者\")`",
            "- 重放首轮擂台: `leaderboard(type=\"tournament\")`",
            "- 刷新复盘: `leaderboard(type=\"tournament_recap\")`",
        ])

    return "\n".join(lines)


def calculate_sect_war_power(sect: SectProfile) -> int:
    """Calculate sect-war power from real sect totals and membership."""
    return sect.total_spirit_power + sect.member_count * 50 + sect.grade.level * 200


def _rank_sects(sects: list[SectProfile], top_n: int) -> list[tuple[SectProfile, int]]:
    ranked = [(sect, calculate_sect_war_power(sect)) for sect in sects]
    ranked.sort(key=lambda item: (-item[1], -item[0].total_spirit_power, item[0].name.lower()))
    return ranked[:max(0, top_n)]


def format_sect_war_banner(
    sects: list[SectProfile],
    top_n: int = 10,
    now: datetime | None = None,
) -> str:
    """Format a sect-war report that remains grounded in live sect data."""
    season = get_current_season(now)
    ranked = _rank_sects(sects, top_n)
    leader = ranked[0] if ranked else None
    challenger = ranked[1] if len(ranked) > 1 else None

    lines = [
        f"# ⛰️ 宗门战 · 宗门天榜 · {season.title}",
        "",
        f"> 当前宗门档案快照，不伪造历史战报。{season.share_tag}",
        "",
        "| # | 宗门 | 等阶 | 宗主 | 宗门战力 | 灵力 | 成员 |",
        "|---|------|------|------|----------|------|------|",
    ]

    for rank, (sect, power) in enumerate(ranked, 1):
        grade = sect.grade
        lines.append(
            f"| {rank} | {sect.name} | {grade.symbol} {grade.name_cn} "
            f"| @{sect.master} | {power} | {sect.total_spirit_power} | {sect.member_count} |"
        )

    if not ranked:
        lines.append("| — | 天地初开，尚无宗门 | — | — | — | — | — |")

    lines.extend([
        "",
        "### 当前战况",
        "",
    ])

    if leader:
        leader_sect, leader_power = leader
        lines.append(f"- 当前冠军宗门: {leader_sect.name} · 宗门战力 {leader_power}")
        if challenger:
            challenger_sect, challenger_power = challenger
            gap = leader_power - challenger_power
            lines.append(
                f"- 下一追赶目标: {challenger_sect.name} 距离 "
                f"{leader_sect.name} 还差 {gap} 宗门战力"
            )
        else:
            lines.append("- 下一追赶目标: 暂无挑战宗门，后来宗门可直接对标当前冠军")
    else:
        lines.extend([
            "- 当前冠军宗门: 暂无，宗门战等待第一个宗门开宗立派",
            "- 第一手行动: `sect(action=\"create\", sect_name=\"天工盟\", motto=\"以凡人之躯，铸逆天之器\")`",
        ])

    lines.extend([
        "",
        "### 计分口径",
        "",
        "`宗门战力 = 宗门灵力 + 成员数 × 50 + 宗门等阶 × 200`",
        "",
        "## 📣 复制战报",
        "",
        "### 复制社交战报",
        "",
        "```text",
    ])

    if leader:
        sect, power = leader
        lines.append(
            f"TianGong 宗门战 {season.title}：{sect.name} 暂列第一，宗门战力 {power}。{season.share_tag}"
        )
    else:
        lines.append(f"TianGong 宗门战 {season.title} 已开启，等待第一个宗门开宗立派。{season.share_tag}")

    lines.extend([
        *format_candidate_join_lines(join_label="加入宗门战"),
        "查看战报：leaderboard(type=\"sect\")",
        "```",
        "",
        "### 复制 Discussion/PR 战报",
        "",
        "```markdown",
    ])

    if leader:
        sect, power = leader
        lines.append(f"## TianGong 宗门战 {season.title}战报")
        lines.append("")
        lines.append(f"- 当前冠军宗门: {sect.name}（宗门战力 {power}，宗主 @{sect.master}）")
        if challenger:
            challenger_sect, challenger_power = challenger
            gap = power - challenger_power
            lines.append(
                f"- 下一追赶目标: {challenger_sect.name} 距离 "
                f"{sect.name} 还差 {gap} 宗门战力"
            )
        else:
            lines.append("- 下一追赶目标: 暂无挑战宗门，欢迎第一支后来宗门开战")
        lines.extend([
            f"- 数据声明: 当前宗门档案快照，不伪造历史战报。{season.share_tag}",
            f"- 拜入冠军宗门: `sect(action=\"join\", sect_name=\"{sect.name}\")`",
            "- 继续贡献: `sect(action=\"leaderboard\")`、`leaderboard(type=\"sect\")`、`my_realm()`",
            *format_candidate_install_markdown_lines(),
        ])
    else:
        lines.append(f"## TianGong 宗门战 {season.title}首宗招募")
        lines.append("")
        lines.extend([
            f"- 数据声明: 当前宗门档案快照为 0 个宗门，不伪造历史战报。{season.share_tag}",
            "- 第一手行动: `sect(action=\"create\", sect_name=\"天工盟\", motto=\"以凡人之躯，铸逆天之器\")`",
            "- 继续贡献: `sect(action=\"leaderboard\")`、`leaderboard(type=\"sect\")`",
            *format_candidate_install_markdown_lines(),
        ])

    lines.extend([
        "```",
        "",
        "## 下一步",
        "",
    ])

    if leader:
        sect, _power = leader
        lines.extend([
            f"- 拜入第一宗门: `sect(action=\"join\", sect_name=\"{sect.name}\")`",
            "- 刷新宗门战榜: `leaderboard(type=\"sect\")`",
            "- 查看宗门战报: `sect(action=\"leaderboard\")`",
            f"- 查看宗主名片: `my_realm(username=\"{sect.master}\")`",
        ])
    else:
        lines.extend([
            "- 开宗立派: `sect(action=\"create\", sect_name=\"天工盟\", motto=\"以凡人之躯，铸逆天之器\")`",
            "- 刷新宗门战榜: `leaderboard(type=\"sect\")`",
            "- 查看宗门战报: `sect(action=\"leaderboard\")`",
            "- 查看修行名片: `my_realm()`",
        ])

    return "\n".join(lines)
