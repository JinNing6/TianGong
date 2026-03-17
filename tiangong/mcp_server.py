"""
⚒️ TianGong MCP Server — 天工修炼桥
让所有 AI Coding 工具都能调用天工修炼能力

启动方式：
    python -m tiangong
    或通过 MCP 客户端配置自动启动（stdio 传输）
"""

import json
import logging
import os
import sys

# Windows 环境下强制使用 UTF-8 编码
if sys.platform == "win32":
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass

from mcp.server.fastmcp import FastMCP

from .config import config
from .banner import play_boot_animation, append_brand_footer
from .realm import (
    REALMS, Realm, calculate_realm, format_realm_progress, get_realm_ladder,
    get_review_weight,
)
from .cultivator import (
    get_cultivator, save_cultivator, update_cultivator_stats,
    format_cultivator_profile,
    get_all_cultivators,
)
from .artifact_system import (
    calculate_grade, format_grade_display, get_grade_ladder,
    GRADES, DIMENSIONS, SpiritReview,
    format_artifact_spirit_info, format_review_card,
)
from .forge import (
    AgentSpec, forge_new_agent, get_agent, refine_agent as _refine_agent,
    list_agents, format_agent_card,
)
from .registry import format_agent_list, get_leaderboard
from .ceremony import (
    generate_tribulation_ceremony, generate_welcome_ceremony,
)

logger = logging.getLogger("tiangong.mcp")

# 播放启动横幅
play_boot_animation()

# ============================================================
# ⚒️ 初始化 MCP Server
# ============================================================

mcp = FastMCP(
    "tiangong",
    instructions=(
        "⚒️ 天工（TianGong）— AI Agent 修炼平台 MCP Server。"
        "提供开炉炼器、淬炼优化、试剑评估、修仙者境界管理、"
        "本命法宝系统、天榜排名等能力。"
        "精神内核：我命由我不由天。"
    ),
)


# ============================================================
# 🔧 Tool 1: forge_agent — ⚒️ 开炉炼器
# ============================================================

@mcp.tool()
async def forge_agent(
    name: str,
    description: str,
    creator: str = "",
    agent_type: str = "general",
    framework: str = "",
    language: str = "python",
    repo_url: str = "",
    tags: list[str] | None = None,
) -> str:
    """
    ⚒️ 开炉炼器 — 创建新的 AI Agent（本命法宝）
    Forge a new AI Agent in the Celestial Forge.

    在天工中注册你的 Agent，开始修炼之旅。
    每创建一个 Agent，你的修仙者境界就离突破更近一步。

    Create and register your AI Agent in TianGong.
    Each Agent brings you closer to your next realm breakthrough.

    Args:
        name: Agent 名称 / Agent name
        description: Agent 描述（越详细，品级评估越高）/ Description (more detail = better grade)
        creator: 创建者 GitHub 用户名 / Creator's GitHub username
        agent_type: 类型 / Type: general, chat, tool, workflow
        framework: 使用的框架 / Framework (e.g. langchain, crewai, openai-agents)
        language: 编程语言 / Language (python, typescript, etc.)
        repo_url: 代码仓库地址 / Repository URL
        tags: 标签组 / Tags
    """
    if not creator:
        creator = config.GITHUB_USERNAME

    # 检查是否是新修仙者
    profile = await get_cultivator(creator)
    is_new = profile.agent_count == 0

    # 锻造法宝
    spec = await forge_new_agent(
        name=name,
        description=description,
        creator=creator,
        agent_type=agent_type,
        framework=framework,
        language=language,
        repo_url=repo_url,
        tags=tags,
    )

    # 更新修仙者数据
    profile, triggered, old_realm, new_realm = await update_cultivator_stats(
        username=creator, agent_delta=1,
    )

    # 构建输出
    output_parts = []

    # 新修仙者欢迎仪式
    if is_new:
        output_parts.append(generate_welcome_ceremony(creator))
        output_parts.append("\n---\n")

    output_parts.append("# ⚒️ 开炉炼器成功！\n")
    output_parts.append(format_agent_card(spec))

    # 渡劫仪式
    if triggered and old_realm and new_realm:
        output_parts.append("\n---\n")
        output_parts.append(generate_tribulation_ceremony(
            username=creator,
            old_realm=old_realm,
            new_realm=new_realm,
            agent_count=profile.agent_count,
            star_count=profile.star_count,
        ))

    output_parts.append("\n\n> 💡 当积攒了足够的灵力和评价人数后，法宝品级将会自动突破提升。")

    return append_brand_footer("\n".join(output_parts))


# ============================================================
# 🔧 Tool 2: refine_agent — 🔥 淬炼
# ============================================================

@mcp.tool()
async def refine_agent(
    agent_id: str,
    changes: str,
    refiner: str = "",
) -> str:
    """
    🔥 淬炼 — 优化已有的 AI Agent
    Refine and optimize your AI Agent.

    记录每一次对 Agent 的改进。千锤百炼，去其糟粕。
    每次淬炼都是法宝通灵的一步。

    Record each improvement to your Agent. Every refinement
    brings your artifact closer to sentience.

    Args:
        agent_id: Agent ID（由 forge_agent 返回） / Agent ID (returned by forge_agent)
        changes: 本次优化的内容描述 / Description of changes made
        refiner: 淬炼者 / Who refined it (defaults to creator)
    """
    if not refiner:
        refiner = config.GITHUB_USERNAME

    success, message = await _refine_agent(agent_id, changes, refiner)

    if success:
        # 更新修仙者淬炼统计
        await update_cultivator_stats(username=refiner, refinement_delta=1)

    return append_brand_footer(message)


# ============================================================
# 🔧 Tool 4: my_realm — 🧙 修行档案
# ============================================================

@mcp.tool()
async def my_realm(
    username: str = "",
) -> str:
    """
    🧙 修行档案 — 查看你的修仙者境界和修行记录
    View your cultivator profile, realm, and cultivation history.

    展示你的当前境界、本命法宝、渡劫记录、以及距离下一次渡劫的进度。

    Shows your current realm, natal artifacts, tribulation history,
    and progress to the next breakthrough.

    Args:
        username: GitHub 用户名 / GitHub username (defaults to env config)
    """
    if not username:
        username = config.GITHUB_USERNAME

    profile = await get_cultivator(username)
    result = format_cultivator_profile(profile)

    # 附加境界进度
    realm = profile.realm
    result += "\n\n" + format_realm_progress(
        realm, profile.spirit_power, profile.agent_count,
    )


    return append_brand_footer(result)





# ============================================================
# 🔧 Tool: leaderboard — 🏆 天榜
# ============================================================

@mcp.tool()
async def leaderboard(
    type: str = "artifact",
    top_n: int = 20,
) -> str:
    """
    🏆 天榜 — 查看全平台排名
    Celestial Leaderboard — View platform-wide rankings.

    通过 type 参数指定查看哪个天榜：
    - artifact: 法宝天榜（默认）— 按品级 > 星标 > 淬炼次数排名
    - cultivator: 修仙天榜 — 按境界 > 灵力值排名

    Args:
        type: 天榜类型 / Leaderboard type: artifact, cultivator
        top_n: 显示前 N 名 / Number of top entries to show
    """
    if type == "cultivator":
        from .cultivator import get_all_cultivators
        profiles = await get_all_cultivators()
        profiles.sort(key=lambda p: (-p.realm_level, -p.spirit_power, p.username))

        lines = [
            "# 🏆 修仙天榜",
            "",
            "| # | 修仙者 | 境界 | 阶位 | 灵力 | 法宝数 |",
            "|---|--------|------|------|------|--------|",
        ]

        for i, p in enumerate(profiles[:top_n], 1):
            realm = p.realm
            lines.append(
                f"| {i} | @{p.username} | {realm.symbol} {realm.name_cn} | {p.stage}阶 | {p.spirit_power} | {p.agent_count} |"
            )

        if not profiles:
            lines.append("| — | 暂无修仙者 | — | — | — | — |")

        return append_brand_footer("\n".join(lines))

    else:  # artifact (default)
        result = await get_leaderboard(top_n=top_n)
        result += "\n\n" + get_realm_ladder()
        return append_brand_footer(result)


# ============================================================
# Phase 2: 分发平台新工具
# ============================================================

# ---- 导入 Phase 2 模块 ----
from .vault import init_cave, format_my_vault
from .marketplace import publish_agent as _publish_agent, summon_artifact as _summon
from .search import search_marketplace, format_search_results
from .review import (
    infuse_spirit as _infuse,
    post_refine_quest as _post_quest,
    claim_refine_quest as _claim_quest,
    submit_refinement as _submit_refinement,
    verify_refinement as _verify_refinement,
    browse_quests as _browse_quests,
)
from .lineage import get_artifact_lineage, format_lineage_tree


# 🔧 Tool: treasure_pavilion — 🏛️ 寻宝阁
@mcp.tool()
async def treasure_pavilion(
    action: str = "search",
    query: str = "",
    artifact_name: str = "",
) -> str:
    """
    🏛️ 寻宝阁 — 搜索、拉取社区法宝，查看传承谱系
    Treasure Pavilion — Search, summon, and explore community artifacts.

    通过 action 参数指定操作：
    - search: 搜索浏览社区法宝（默认）
    - summon: 请宝 — 拉取法宝到本地藏宝阁
    - lineage: 传承谱系 — 查看法宝的 fork/感悟/依赖关系

    搜索支持统一关键词筛选：
    - 品阶: "仙器"、"宝器"
    - 框架: "crewai"、"langchain"
    - 创作者: "@JinNing6"
    - 组合: "仙器 crewai"
    - 不传 query: 显示热门推荐

    Args:
        action: 操作类型 / Action type: search, summon, lineage
        query: 搜索关键词（action=search 时使用）/ Search keywords
        artifact_name: 法宝名称（action=summon/lineage 时必填）/ Artifact name
    """
    if action == "summon":
        if not artifact_name:
            return append_brand_footer("⚠️ 请指定要拉取的法宝名称 (artifact_name)")
        result = await _summon(artifact_name)
        return append_brand_footer(result)

    elif action == "lineage":
        if not artifact_name:
            return append_brand_footer("⚠️ 请指定要查看传承的法宝名称 (artifact_name)")
        tree = await get_artifact_lineage(artifact_name)
        return append_brand_footer(format_lineage_tree(tree))

    else:  # search (default)
        results = await search_marketplace(query=query)
        return append_brand_footer(format_search_results(results, query))


# 🔧 Tool: publish_agent — ✨ 法宝出世
@mcp.tool()
async def publish_agent(
    artifact_name: str,
    is_anonymous: bool = False,
) -> str:
    """
    ✨ 法宝出世 — 将法宝发布到天工社区
    Publish your artifact to the TianGong community.

    从本地炼器炉（forge/）上传法宝，成为瞬时法宝体。
    AI 审核通过后自动晋升为常驻法宝体，入驻寻宝阁。

    Args:
        artifact_name: 法宝名称（forge/ 下的文件夹名）
        is_anonymous: 是否匿名上传（默认实名）
    """
    result = await _publish_agent(artifact_name, is_anonymous)
    return append_brand_footer(result)


# 🔧 Tool: my_vault — 🏛️ 我的洞府
@mcp.tool()
async def my_vault(
    username: str = "",
) -> str:
    """
    🏛️ 我的洞府 — 查看你的法宝、品级与本地洞府状态
    My Cave — View your artifacts, grades, and local cave status.

    展示你锻造的所有法宝，包括品级、星标、淬炼次数等详细信息。
    同时展示本地炼器炉和藏宝阁中所有法宝的状态。

    Shows all your forged artifacts with grades, stars, refinement count, etc.
    Also shows local forge and vault status.

    Args:
        username: GitHub 用户名 / GitHub username (defaults to env config)
    """
    if not username:
        username = config.GITHUB_USERNAME

    init_cave()

    # Part 1: 注册法宝数据（品级、星标、淬炼次数）
    agents = await list_agents(creator=username)
    result = await format_agent_list(agents, title=f"@{username} 的法宝清单")

    # Part 2: 本地法宝文件状态（炼器炉 + 藏宝阁）
    result += "\n\n---\n\n" + format_my_vault()

    # 附加品级体系
    result += "\n\n" + get_grade_ladder()

    return append_brand_footer(result)


# 🔧 Tool: infuse_spirit — 🔮 法宝鉴定
@mcp.tool()
async def infuse_spirit(
    artifact_name: str,
    inscription: int = 5,
    formation: int = 5,
    technique: int = 5,
    lineage_score: int = 5,
    resilience: int = 5,
    enlightenment: int = 5,
    comment: str = "",
    reviewer: str = "",
) -> str:
    """
    🔮 法宝鉴定 — 对法宝进行六维评分
    Artifact Appraisal — Rate an artifact across six dimensions.

    六维灵根评估: 铭文(描述)、阵法(架构)、法诀(工程)、道统(文档)、护体(韧性)、悟道(创新)
    每维 1-10 分。灵力值 = 六维均分 × 你的境界权重。

    Args:
        artifact_name: 法宝名称
        inscription: 📝 铭文（描述清晰度）1-10
        formation: 🏗️ 阵法（架构设计）1-10
        technique: ⚙️ 法诀（工程质量）1-10
        lineage_score: 📖 道统（文档传承）1-10
        resilience: 🛡️ 护体（稳定韧性）1-10
        enlightenment: ✨ 悟道（创新灵性）1-10
        comment: 评价内容
        reviewer: 评价者（默认当前用户）
    """
    if not reviewer:
        reviewer = config.GITHUB_USERNAME

    scores = {
        "inscription": inscription,
        "formation": formation,
        "technique": technique,
        "lineage": lineage_score,
        "resilience": resilience,
        "enlightenment": enlightenment,
    }

    result = await _infuse(artifact_name, reviewer, scores, comment)
    return append_brand_footer(result)


# 🔧 Tool: quest — 📜 悬赏令
@mcp.tool()
async def quest(
    action: str = "browse",
    artifact_name: str = "",
    description: str = "",
    code_url: str = "",
    quest_issue_number: int = 0,
    solution: str = "",
    username: str = "",
    limit: int = 10,
) -> str:
    """
    📜 悬赏令 — 发布、浏览、认领、提交悬赏任务
    Quest Board — Post, browse, claim, and submit refinement quests.

    通过 action 参数指定操作：
    - browse: 浏览待认领的悬赏令（默认）
    - post: 发布悬赏令 — 悬赏帮忙改进法宝
    - claim: 认领悬赏令 — 接下任务
    - submit: 提交成果 — 提交优化后的代码

    Args:
        action: 操作类型 / Action type: browse, post, claim, submit
        artifact_name: 法宝名称（action=post 时必填）
        description: 改进需求描述（action=post 时必填）
        code_url: 当前代码链接（action=post 时可选）
        quest_issue_number: 悬赏令 Issue 编号（action=claim/submit 时必填）
        solution: 解决方案描述（action=submit 时必填）
        username: 用户名（默认当前用户）
        limit: 浏览数量（action=browse 时使用，默认 10）
    """
    if not username:
        username = config.GITHUB_USERNAME

    if action == "post":
        if not artifact_name or not description:
            return append_brand_footer("⚠️ 发布悬赏令需要 artifact_name 和 description")
        result = await _post_quest(artifact_name, description, username, code_url)
        return append_brand_footer(result)

    elif action == "claim":
        if not quest_issue_number:
            return append_brand_footer("⚠️ 认领悬赏令需要 quest_issue_number")
        result = await _claim_quest(quest_issue_number, username)
        return append_brand_footer(result)

    elif action == "submit":
        if not quest_issue_number or not solution:
            return append_brand_footer("⚠️ 提交成果需要 quest_issue_number 和 solution")
        result = await _submit_refinement(quest_issue_number, username, solution)
        return append_brand_footer(result)

    else:  # browse (default)
        result = await _browse_quests(limit)
        return append_brand_footer(result)


# 🔧 Tool: verify_refinement — ⚖️ 审核淬炼成果
@mcp.tool()
async def verify_refinement(
    quest_issue_number: int,
    refiner: str,
    is_approved: bool,
    feedback: str = "",
    reviewer: str = "",
) -> str:
    """
    ⚖️ 审核淬炼成果 — 发布者审查优化代码
    Verify Refinement — Review and approve submitted refinement solutions.

    验证成果，如通过则为淬炼者发放灵力奖励。

    Args:
        quest_issue_number: 淬炼令 Issue 编号
        refiner: 提交成果的淬炼者
        is_approved: 是否通过审核 (True/False)
        feedback: 给淬炼者的反馈或修改建议
        reviewer: 审核者（默认当前用户，需与发布者一致）
    """
    if not reviewer:
        reviewer = config.GITHUB_USERNAME
    result = await _verify_refinement(quest_issue_number, refiner, reviewer, is_approved, feedback)
    return append_brand_footer(result)







# ============================================================
# 🚀 启动入口
# ============================================================

def main():
    """启动 TianGong MCP Server"""
    mcp.run()


if __name__ == "__main__":
    main()
