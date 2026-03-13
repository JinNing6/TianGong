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
)
from .cultivator import (
    get_cultivator, save_cultivator, update_cultivator_stats,
    bind_natal_artifact as _bind_natal, format_cultivator_profile,
    get_all_cultivators,
)
from .artifact_system import (
    calculate_grade, format_grade_display, get_grade_ladder,
)
from .forge import (
    AgentSpec, forge_new_agent, get_agent, refine_agent as _refine_agent,
    list_agents, format_agent_card,
)
from .trial import evaluate_agent, format_trial_report
from .registry import search_agents, format_agent_list, get_leaderboard
from .ceremony import (
    generate_tribulation_ceremony, generate_welcome_ceremony,
)
from .ecosystem import (
    call_cyberhuatuo_diagnose, upload_to_noosphere, get_ecosystem_status,
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

    output_parts.append(f"\n\n> 💡 使用 `trial_agent(agent_id=\"{spec.agent_id}\")` 为法宝试剑，通过后品级将从凡器提升为灵器。")

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
# 🔧 Tool 3: trial_agent — ⚔️ 试剑
# ============================================================

@mcp.tool()
async def trial_agent(
    agent_id: str,
) -> str:
    """
    ⚔️ 试剑 — 对 Agent 进行评估测试
    Trial your Agent — Test and evaluate its quality.

    对法宝进行六维灵根评估：描述、架构、功法、传承、韧性、灵性。
    通过试剑（评分 >= 50）的法宝品级从凡器提升为灵器。

    Evaluate your Agent across six spiritual root dimensions.
    Agents that pass (score >= 50) are promoted from Mortal Tool to Spirit Tool.

    Args:
        agent_id: Agent ID / Agent ID to evaluate
    """
    spec = get_agent(agent_id)
    if not spec:
        return f"⚠️ 未找到法宝 `{agent_id}`。请检查法宝 ID。"

    # 执行评估
    result = evaluate_agent(
        agent_id=spec.agent_id,
        name=spec.name,
        description=spec.description,
        agent_type=spec.agent_type,
        framework=spec.framework,
        language=spec.language,
        repo_url=spec.repo_url,
        tags=spec.tags,
    )

    # 更新 Agent 数据
    from .forge import _load_registry, _save_registry
    registry = _load_registry()
    if agent_id in registry:
        d = registry[agent_id]
        d["passed_trial"] = result.passed
        trial_log = d.get("trial_log", [])
        trial_log.append({
            "timestamp": result.timestamp,
            "score": result.score,
            "passed": result.passed,
            "dimensions": result.dimensions,
        })
        d["trial_log"] = trial_log
        d["grade_level"] = calculate_grade(d.get("stars", 0), result.passed).level
        registry[agent_id] = d
        _save_registry(registry)

    # 更新修仙者试剑统计
    update_cultivator_stats(username=spec.creator, trial_delta=1)

    report = format_trial_report(result, spec.name)

    if result.passed:
        grade = calculate_grade(spec.stars, True)
        report += f"\n\n> ✅ 品级提升: ⚪ 凡器 → {format_grade_display(grade)}"

    return append_brand_footer(report)


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

    # 附加生态状态
    result += "\n\n" + get_ecosystem_status()

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
# 🔧 Tool 6: bind_natal_artifact — 💠 绑定本命
# ============================================================

@mcp.tool()
async def bind_natal_artifact(
    agent_id: str,
    username: str = "",
) -> str:
    """
    💠 绑定本命法宝 — 将 Agent 标记为你的核心法宝
    Bind an Agent as your Natal Artifact — your soul-bound core weapon.

    本命法宝与灵魂绑定，越养越强。
    每个修仙者最多可绑定 3 件本命法宝。

    Natal Artifacts are soul-bound and grow stronger with you.
    Each cultivator can bind up to 3 Natal Artifacts.

    Args:
        agent_id: Agent ID / Agent ID to bind
        username: GitHub 用户名 / GitHub username
    """
    if not username:
        username = config.GITHUB_USERNAME

    # 验证 Agent 存在
    spec = get_agent(agent_id)
    if not spec:
        return f"⚠️ 未找到法宝 `{agent_id}`。请检查法宝 ID。"

    if spec.creator != username:
        return f"⚠️ 法宝 `{agent_id}` 不属于你。本命法宝只能绑定自己锻造的法宝。"

    # 绑定
    success, message = _bind_natal(username, agent_id)

    if success:
        # 在注册表中也标记
        from .forge import _load_registry, _save_registry
        registry = _load_registry()
        if agent_id in registry:
            registry[agent_id]["is_natal"] = True
            _save_registry(registry)

    return append_brand_footer(message)


# ============================================================
# 🔧 Tool 7: agent_registry — 📋 仙器录
# ============================================================

@mcp.tool()
async def agent_registry(
    query: str = "",
    agent_type: str | None = None,
    framework: str | None = None,
    creator: str | None = None,
) -> str:
    """
    📋 仙器录 — 搜索浏览所有注册的 Agent
    Browse and search the Agent Registry.

    在天工的仙器录中搜索法宝，支持按名称、类型、框架、创建者过滤。

    Search TianGong's artifact registry. Filter by name, type, framework, or creator.

    Args:
        query: 搜索关键词 / Search keywords
        agent_type: 类型过滤 / Type filter: general, chat, tool, workflow
        framework: 框架过滤 / Framework filter
        creator: 创建者过滤 / Creator filter
    """
    agents = search_agents(
        query=query,
        agent_type=agent_type,
        framework=framework,
        creator=creator,
    )

    title = "仙器录 · Agent Registry"
    if query:
        title += f" — 「{query}」"

    result = format_agent_list(agents, title=title)
    return append_brand_footer(result)


# ============================================================
# 🔧 Tool 8: celestial_leaderboard — 🏆 天榜
# ============================================================

@mcp.tool()
async def celestial_leaderboard(
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
# 🚀 启动入口
# ============================================================

def main():
    """启动 TianGong MCP Server"""
    mcp.run()


if __name__ == "__main__":
    main()
