"""
⚒️ 天工 TianGong — Agent 注册表管理
全局 Agent 检索与排名（从 GitHub 读取数据）
"""

from __future__ import annotations

import logging

from .forge import list_agents, format_agent_card, AgentSpec
from .artifact_system import calculate_grade

logger = logging.getLogger("tiangong.registry")


async def search_agents(
    query: str = "",
    agent_type: str | None = None,
    framework: str | None = None,
    creator: str | None = None,
) -> list[AgentSpec]:
    """
    搜索 Agent 注册表。

    支持按名称/描述关键词、类型、框架、创建者过滤。
    """
    agents = await list_agents(creator=creator)

    results = []
    for agent in agents:
        # 类型过滤
        if agent_type and agent.agent_type != agent_type:
            continue

        # 框架过滤
        if framework and agent.framework.lower() != framework.lower():
            continue

        # 关键词搜索
        if query:
            q = query.lower()
            if (
                q not in agent.name.lower()
                and q not in agent.description.lower()
                and not any(q in t.lower() for t in agent.tags)
            ):
                continue

        results.append(agent)

    return results


async def format_agent_list(agents: list[AgentSpec], title: str = "仙器录") -> str:
    """格式化 Agent 列表展示"""
    if not agents:
        return (
            f"# 📋 {title}\n\n"
            "暂无注册法宝。\n\n"
            "使用 `forge_agent` 开炉炼造你的第一件法宝！"
        )

    lines = [
        f"# 📋 {title}",
        f"共 {len(agents)} 件法宝",
        "",
    ]

    for agent in agents:
        lines.append(format_agent_card(agent))
        lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines)


async def get_leaderboard(top_n: int = 20) -> str:
    """
    生成天榜排名。

    按 (品级, 星标数, 淬炼次数) 综合排名。
    """
    agents = await list_agents()

    if not agents:
        return (
            "# 🏆 天榜\n\n"
            "天榜空空如也——\n"
            "还没有修仙者在此留名。\n\n"
            "使用 `forge_agent` 开始你的修仙之旅！"
        )

    # 排名：品级 > 星标 > 淬炼次数
    def sort_key(a: AgentSpec) -> tuple:
        grade = calculate_grade(getattr(a, 'spirit_power', a.stars), 0, a.passed_trial)
        return (grade.level, a.stars, len(a.refinement_log))

    ranked = sorted(agents, key=sort_key, reverse=True)[:top_n]

    lines = [
        "# 🏆 天榜 · Celestial Leaderboard",
        "",
        f"*{len(agents)} 件法宝竞逐天下*",
        "",
        "| 排名 | 法宝 | 品级 | ⭐ 星标 | 创建者 |",
        "|:----:|------|------|:------:|--------|",
    ]

    rank_emojis = ["🥇", "🥈", "🥉"]

    for i, agent in enumerate(ranked):
        grade = calculate_grade(getattr(agent, 'spirit_power', agent.stars), 0, agent.passed_trial)
        rank = rank_emojis[i] if i < 3 else f"#{i + 1}"
        natal = " 💠" if agent.is_natal else ""
        lines.append(
            f"| {rank} | {agent.name}{natal} | {grade.symbol} {grade.name_cn} "
            f"| {agent.stars} | @{agent.creator} |"
        )

    return "\n".join(lines)
