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
    profile = get_cultivator(creator)
    is_new = profile.agent_count == 0

    # 锻造法宝
    spec = forge_new_agent(
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
    profile, triggered, old_realm, new_realm = update_cultivator_stats(
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

    success, message = _refine_agent(agent_id, changes, refiner)

    if success:
        # 更新修仙者淬炼统计
        update_cultivator_stats(username=refiner, refinement_delta=1)

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

    profile = get_cultivator(username)
    result = format_cultivator_profile(profile)

    # 附加境界进度
    realm = profile.realm
    result += "\n\n" + format_realm_progress(
        realm, profile.agent_count, profile.star_count,
    )


    return append_brand_footer(result)


# ============================================================
# 🔧 Tool 5: my_artifacts — 🔮 法宝清单
# ============================================================

@mcp.tool()
async def my_artifacts(
    username: str = "",
) -> str:
    """
    🔮 法宝清单 — 查看你的所有 Agent 及品级
    View all your Agents and their grades.

    展示你锻造的所有法宝，包括品级、星标、淬炼次数等详细信息。

    Shows all your forged artifacts with grades, stars, refinement count, etc.

    Args:
        username: GitHub 用户名 / GitHub username (defaults to env config)
    """
    if not username:
        username = config.GITHUB_USERNAME

    agents = list_agents(creator=username)
    result = format_agent_list(agents, title=f"@{username} 的法宝清单")

    # 附加品级体系
    result += "\n\n" + get_grade_ladder()

    return append_brand_footer(result)


# ============================================================
# 🔧 Tool: artifact_leaderboard — 🏆 法宝天榜
# ============================================================

@mcp.tool()
async def artifact_leaderboard(
    top_n: int = 20,
) -> str:
    """
    🏆 天榜 — 查看全平台最强 Agent 排名
    View the Celestial Leaderboard — top Agents across the platform.

    天榜以品级 > 星标 > 淬炼次数综合排名，
    展示天工平台上最强大的法宝。

    Rankings based on grade > stars > refinement count,
    showing the most powerful artifacts on the TianGong platform.

    Args:
        top_n: 显示前 N 名 / Number of top entries to show
    """
    result = get_leaderboard(top_n=top_n)

    # 附加修仙者境界阶梯（参考）
    result += "\n\n" + get_realm_ladder()

    return append_brand_footer(result)


# ============================================================
# Phase 2: 分发平台新工具
# ============================================================

# ---- 导入 Phase 2 模块 ----
from .vault import init_cave, format_my_vault, format_vault_status
from .marketplace import publish_agent as _publish_agent, summon_artifact as _summon, banish_artifact
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


# 🔧 Tool 9: treasure_pavilion — 🏛️ 寻宝阁
@mcp.tool()
async def treasure_pavilion(query: str = "") -> str:
    """
    🏛️ 寻宝阁 — 搜索浏览社区法宝
    Search and browse community artifacts in the Treasure Pavilion.

    统一关键词搜索，一个 query 搞定所有筛选：
    - 品阶: "仙器"、"宝器"
    - 框架: "crewai"、"langchain"
    - 创作者: "@JinNing6"
    - 组合: "仙器 crewai"
    - 不传参: 显示热门推荐

    Args:
        query: 搜索关键词 / Search keywords
    """
    results = await search_marketplace(query=query)
    return append_brand_footer(format_search_results(results, query))


# 🔧 Tool: publish_agent — ✨ 飞升上界
@mcp.tool()
async def publish_agent(
    artifact_name: str,
    is_anonymous: bool = False,
) -> str:
    """
    ✨ 飞升上界 — 将法宝发布到天工社区
    Publish your artifact to the TianGong community.

    从本地炼器炉（forge/）上传法宝，成为瞬时法宝体。
    AI 审核通过后自动晋升为常驻法宝体，入驻寻宝阁。

    Args:
        artifact_name: 法宝名称（forge/ 下的文件夹名）
        is_anonymous: 是否匿名上传（默认实名）
    """
    result = await _publish_agent(artifact_name, is_anonymous)
    return append_brand_footer(result)


# 🔧 Tool 11: summon_artifact — 📥 请宝下凡
@mcp.tool()
async def summon_artifact(artifact_name: str) -> str:
    """
    📥 请宝下凡 — 从寻宝阁拉取法宝到本地藏宝阁
    Summon an artifact from the Treasure Pavilion to your local vault.

    自动下载法宝到 ~/.tiangong/vault/法宝名/ 目录。

    Args:
        artifact_name: 法宝名称
    """
    result = await _summon(artifact_name)
    return append_brand_footer(result)


# 🔧 Tool: my_vault — 📦 我的法宝
@mcp.tool()
async def my_vault() -> str:
    """
    📦 我的法宝 — 查看本地缓存的 Agent
    My Vault — View locally summoned and forged artifacts.

    展示炼器炉和藏宝阁中所有法宝的状态。
    """
    init_cave()
    return append_brand_footer(format_my_vault())


# 🔧 Tool: vault_status — 🏛️ 洞府状态查询
@mcp.tool()
async def vault_status() -> str:
    """
    🏛️ 洞府状态查询 — 检查运行环境与连接
    Vault Status — Check host environment resources and client connection.
    """
    init_cave()
    return append_brand_footer(format_vault_status())


# 🔧 Tool: infuse_spirit — 💫 灌注灵力
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
    💫 灌注灵力 — 对法宝进行六维评分
    Infuse Spirit Power — Rate an artifact across six dimensions.

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


# 🔧 Tool: post_refine_quest — 🔥 发布淬炼令
@mcp.tool()
async def post_refine_quest(
    artifact_name: str,
    description: str,
    code_url: str = "",
    creator: str = "",
) -> str:
    """
    🔥 发布淬炼令 — 悬赏帮忙改进法宝
    Post a Refinement Quest — Request help to improve an artifact.

    发布需求，等待有缘人认领并帮助优化你的法宝。

    Args:
        artifact_name: 需要改进的法宝名称
        description: 改进需求描述
        code_url: 当前代码链接
        creator: 发布者（默认当前用户）
    """
    if not creator:
        creator = config.GITHUB_USERNAME
    result = await _post_quest(artifact_name, description, creator, code_url)
    return append_brand_footer(result)


# 🔧 Tool 15: claim_quest — 🙋 认领淬炼令
@mcp.tool()
async def claim_quest(
    quest_issue_number: int,
    refiner: str = "",
) -> str:
    """
    🙋 认领淬炼令 — 接下这道悬赏，承诺帮忙优化法宝。
    Claim a Refinement Quest — Accept the bounty to optimize an artifact.

    Args:
        quest_issue_number: 淬炼令 Issue 编号
        refiner: 认领者（默认当前用户）
    """
    if not refiner:
        refiner = config.GITHUB_USERNAME
    result = await _claim_quest(quest_issue_number, refiner)
    return append_brand_footer(result)


# 🔧 Tool: submit_refinement — 🛠️ 提交淬炼成果
@mcp.tool()
async def submit_refinement(
    quest_issue_number: int,
    solution: str,
    refiner: str = "",
) -> str:
    """
    🛠️ 提交淬炼成果 — 提交优化后的法宝代码
    Submit Refinement — Deliver your refinement solution.

    Args:
        quest_issue_number: 淬炼令 Issue 编号
        solution: 解决方案描述
        refiner: 淬炼者（默认当前用户）
    """
    if not refiner:
        refiner = config.GITHUB_USERNAME
    result = await _submit_refinement(quest_issue_number, refiner, solution)
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


# 🔧 Tool: browse_quests — 📜 悬赏布告栏
@mcp.tool()
async def browse_quests(limit: int = 10) -> str:
    """
    📜 悬赏布告栏 — 浏览待认领的淬炼令
    Browse Quests — View active refinement quests waiting to be claimed.

    寻找可以优化改进的法宝，获取淬炼任务。

    Args:
        limit: 返回的淬炼令数量（默认 10）
    """
    result = await _browse_quests(limit)
    return append_brand_footer(result)


# 🔧 Tool 17: artifact_lineage — 📜 传承谱系
@mcp.tool()
async def artifact_lineage(artifact_name: str) -> str:
    """
    📜 传承谱系 — 查看法宝的传承关系
    View Lineage Tree — See an artifact's fork/inspire/depend relationships.

    展示法宝的传承谱系: fork(分支传承)、inspired(悟道传承)、depends(法宝联动)。

    Args:
        artifact_name: 法宝名称
    """
    tree = await get_artifact_lineage(artifact_name)
    return append_brand_footer(format_lineage_tree(tree))


# 🔧 Tool: banish_artifact — 🔒 封印法宝
@mcp.tool()
async def banish_artifact(artifact_name: str) -> str:
    """
    🔒 封印法宝 — 归档藏宝阁中的法宝
    Banish Artifact — Archive an artifact from your vault.

    将法宝移到 .archive/ 目录，释放空间。

    Args:
        artifact_name: 要封印的法宝名称
    """
    return append_brand_footer(banish_artifact(artifact_name))


# 🔧 Tool 19: cultivator_leaderboard — 🏆 修仙天榜
@mcp.tool()
async def cultivator_leaderboard(top_n: int = 20) -> str:
    """
    🏆 修仙天榜 — 修仙者境界排名
    Cultivator Leaderboard — Rankings by realm and spirit power.

    按境界降序 → 同境界按灵力值降序 → 同灵力按用户名字母序。

    Args:
        top_n: 显示前 N 名
    """
    from .cultivator import get_all_cultivators
    profiles = get_all_cultivators()

    # 排序
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


# ============================================================
# 🚀 启动入口
# ============================================================

def main():
    """启动 TianGong MCP Server"""
    mcp.run()


if __name__ == "__main__":
    main()
