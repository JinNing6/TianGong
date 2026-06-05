"""
⚒️ 天工 TianGong — Agent 注册表管理
全局 Agent 检索与排名（从 GitHub 读取数据）
"""

from __future__ import annotations

import logging

from .artifact_system import calculate_grade
from .forge import AgentSpec, format_agent_card, list_agents
from .install_bridge import format_candidate_join_lines, format_candidate_join_text

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
            "> 真实注册表快照：来自 GitHub 全局 Agent registry 当前筛选结果，不伪造已拥有法宝。\n\n"
            "当前筛选结果为 0 件法宝。\n\n"
            "暂无注册法宝。\n\n"
            "---\n\n"
            "## 📣 复制招募\n\n"
            "```text\n"
            "我在 TianGong 还没有注册法宝。"
            "第一件法宝就是入道凭证：开炉、发布、请人鉴定，马上进入天榜循环。\n"
            f"{format_candidate_join_text()}\n"
            "```\n\n"
            "## 下一步\n\n"
            "- 开炉炼器: `forge_agent(name=\"my-first-artifact\", description=\"My first TianGong artifact\")`\n"
            "- 发布悬赏: `quest(action=\"post\", artifact_name=\"my-first-artifact\", description=\"需要一件适合新手入道的法宝\")`\n"
            "- 浏览寻宝阁: `treasure_pavilion(action=\"search\")`\n"
            "- 查看法宝天榜: `leaderboard(type=\"artifact\")`"
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
            "# 🏆 天榜 · Celestial Leaderboard\n\n"
            "> 真实注册表快照：来自 GitHub 全局 Agent registry 当前读取结果，不伪造历史排名。\n"
            "> 排序依据: 品级 > 星标 > 淬炼次数。\n\n"
            "*0 件法宝竞逐天下*\n\n"
            "天榜空空如也——还没有修仙者在此留名。\n\n"
            "---\n\n"
            "## 📣 复制招募\n\n"
            "```text\n"
            "我在 TianGong 法宝天榜看到第一席空缺。"
            "谁先开炉炼成第一件法宝，谁就先在天榜留名。\n"
            f"{format_candidate_join_text()}\n"
            "```\n\n"
            "## 下一步\n\n"
            "- 抢占法宝首席: `forge_agent(name=\"first-artifact\", description=\"A TianGong artifact racing for the first artifact leaderboard rank\")`\n"
            "- 发布首席悬赏: `quest(action=\"post\", artifact_name=\"first-artifact\", description=\"需要一件冲击法宝天榜首席的法宝\")`\n"
            "- 浏览寻宝阁: `treasure_pavilion(action=\"search\")`\n"
            "- 刷新法宝天榜: `leaderboard(type=\"artifact\")`"
        )

    # 排名：品级 > 星标 > 淬炼次数
    def sort_key(a: AgentSpec) -> tuple:
        grade = calculate_grade(getattr(a, 'spirit_power', a.stars), 0, a.passed_trial)
        return (grade.level, a.stars, len(a.refinement_log))

    ranked = sorted(agents, key=sort_key, reverse=True)[:top_n]
    top_agent = ranked[0] if ranked else None

    lines = [
        "# 🏆 天榜 · Celestial Leaderboard",
        "",
        "> 真实注册表快照：来自 GitHub 全局 Agent registry 当前读取结果，不伪造历史排名。",
        "> 排序依据: 品级 > 星标 > 淬炼次数。",
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

    lines.extend([
        "",
        "---",
        "",
        "## 📣 复制分享",
        "",
        "```text",
    ])

    if top_agent:
        lines.append(
            f"我在 TianGong 看到 {top_agent.name} 暂列法宝天榜第一，"
            f"创建者 @{top_agent.creator}。"
        )
    else:
        lines.append("TianGong 法宝天榜等待第一件逆天法宝出世。")

    lines.extend([
        *format_candidate_join_lines(),
        "```",
        "",
        "## 下一步",
        "",
    ])

    if top_agent:
        lines.extend([
            f"- 请宝下凡: `treasure_pavilion(action=\"summon\", artifact_name=\"{top_agent.name}\")`",
            f"- 灌注灵力: `infuse_spirit(artifact_name=\"{top_agent.name}\")`",
            f"- 继续淬炼: `refine_agent(agent_id=\"{top_agent.agent_id}\", changes=\"...\")`",
        ])
    else:
        lines.append("- 开炉炼器: `forge_agent`")

    lines.append("- 查看法宝天榜: `leaderboard(type=\"artifact\")`")

    return "\n".join(lines)
