"""
⚒️ TianGong MCP Server — 天工修炼桥
让所有 AI Coding 工具都能调用天工修炼能力

启动方式：
    python -m tiangong
    或通过 MCP 客户端配置自动启动（stdio 传输）
"""

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

from .activation import (
    EVENT_FORGE_SUCCEEDED,
    EVENT_INFUSE_SUCCEEDED,
    EVENT_ISSUEOPS_REFERRAL_RECORDED,
    EVENT_PUBLISH_SUCCEEDED,
    EVENT_REFINE_SUCCEEDED,
    EVENT_SHARE_ATTRIBUTION_RECORDED,
    EVENT_START_CULTIVATION_VIEWED,
    format_activation_funnel,
    format_share_attribution_command,
    format_share_attribution_report,
    format_share_proof_leaderboard,
    get_activation_event_path,
    load_activation_events,
    public_proof_url_problem,
    record_activation_event,
)
from .artifact_system import get_grade_ladder
from .banner import append_brand_footer, play_boot_animation
from .ceremony import (
    generate_tribulation_ceremony,
    generate_welcome_ceremony,
)
from .config import config
from .cultivator import (
    add_tribulation_evidence,
    format_cultivator_profile,
    format_tribulation_check,
    get_all_cultivators,
    get_cultivator,
    get_tribulation_evidence_specs,
    save_cultivator,
    update_cultivator_stats,
)
from .forge import (
    forge_new_agent,
    format_agent_card,
    list_agents,
)
from .forge import (
    refine_agent as _refine_agent,
)
from .growth import format_growth_campaign, format_growth_flywheel
from .install_bridge import DEFAULT_PACKAGE_NAME, git_tag_install_command, local_package_version
from .lineage import format_lineage_tree, get_artifact_lineage
from .marketplace import publish_agent as _publish_agent
from .marketplace import summon_artifact as _summon
from .onboarding import format_start_cultivation
from .proof_pack import format_public_proof_pack
from .public_growth import (
    fetch_public_distribution_readiness,
    fetch_public_growth_snapshot,
    format_public_growth_report,
    format_public_install_command,
    format_public_launch_preflight,
    get_public_growth_snapshot_path,
    load_public_growth_snapshots,
    record_public_growth_snapshot,
)
from .realm import (
    format_realm_progress,
    get_realm_ladder,
)
from .registry import format_agent_list, get_leaderboard
from .review import (
    browse_quests as _browse_quests,
)
from .review import (
    claim_refine_quest as _claim_quest,
)
from .review import (
    infuse_spirit as _infuse,
)
from .review import (
    post_refine_quest as _post_quest,
)
from .review import (
    submit_refinement as _submit_refinement,
)
from .review import (
    verify_refinement as _verify_refinement,
)
from .search import format_search_results, search_marketplace
from .season import (
    format_season_leaderboard,
    format_sect_war_banner,
    format_tournament_board,
    format_tournament_recap,
)
from .sect import (
    create_sect as _create_sect,
)
from .sect import (
    format_sect_card,
    get_all_sects,
)
from .sect import (
    get_sect as _get_sect,
)
from .sect import (
    join_sect as _join_sect,
)
from .sect import (
    leave_sect as _leave_sect,
)
from .sect import (
    manage_sect as _manage_sect,
)
from .vault import format_my_vault, init_cave

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


def _record_activation_event_safely(event_type: str, **kwargs) -> tuple[bool, str]:
    """Record activation telemetry without blocking the public tool result."""
    try:
        record_activation_event(event_type, **kwargs)
        return True, ""
    except OSError as exc:
        logger.warning("Activation telemetry could not be written: %s", exc)
        return False, str(exc)


def _public_proof_url_problem(value: str, *, field_name: str) -> str:
    """Return why a public proof URL is not reviewable enough for the ledger."""
    return public_proof_url_problem(value, field_name=field_name)


def _current_candidate_install_command() -> str:
    """Return the current Git tag candidate install while PyPI may be stale."""
    return git_tag_install_command(
        repo_owner="",
        repo_name="",
        version_or_tag=local_package_version(DEFAULT_PACKAGE_NAME),
        package_name=DEFAULT_PACKAGE_NAME,
    )


# ============================================================
# 🔧 Tool 1: forge_agent — ⚒️ 开炉炼器
# ============================================================

@mcp.tool()
async def start_cultivation(
    username: str = "",
    artifact_name: str = "",
) -> str:
    """
    ⚒️ 起火入道 — 首会话修炼卡，给新用户安装、MCP 配置、第一件法宝和增长回流入口
    Start Cultivation — first-session onboarding card for new TianGong users.

    Args:
        username: GitHub 用户名 / GitHub username (defaults to env config)
        artifact_name: 第一件法宝名称 / First artifact name
    """
    if not username:
        username = config.GITHUB_USERNAME
    _record_activation_event_safely(
        EVENT_START_CULTIVATION_VIEWED,
        actor=username,
        artifact_name=artifact_name,
        metadata={"source_tool": "start_cultivation"},
    )
    return append_brand_footer(format_start_cultivation(username=username, artifact_name=artifact_name))


def _build_forge_share_block(agent_id: str, artifact_name: str, creator: str) -> str:
    """Build a paste-ready share block for successful artifact creation."""
    install_command = _current_candidate_install_command()
    share_text = (
        f"我在 TianGong 开炉炼器：@{creator} 铸成法宝 `{artifact_name}`"
        f"（ID: `{agent_id}`），+100 灵力。"
    )

    return (
        "\n\n---\n\n"
        "## 📣 复制分享\n\n"
        "```text\n"
        f"{share_text}\n"
        f"加入修炼: {install_command}\n"
        "安装后复查: tiangong-mcp public-install-command\n"
        "PyPI 追平后安装: pip install -U tiangong-mcp\n"
        "```\n\n"
        "## 下一步\n\n"
        f"- 继续淬炼: `refine_agent(agent_id=\"{agent_id}\", changes=\"...\")`\n"
        f"- 发布出世: `publish_agent(artifact_name=\"{artifact_name}\")`\n"
        f"- 寻宝阁曝光: `treasure_pavilion(action=\"search\", query=\"{artifact_name}\")`\n"
        f"- 查看修行名片: `my_realm(username=\"{creator}\")`\n"
        "- 冲击法宝天榜: `leaderboard(type=\"artifact\")`\n"
        f"- 记录公开分享归因: {format_share_attribution_command(contribution='forge', actor=creator, artifact_name=artifact_name)}"
    )


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
        username=creator, agent_delta=1, spirit_delta=100,
    )
    _record_activation_event_safely(
        EVENT_FORGE_SUCCEEDED,
        actor=creator,
        artifact_name=spec.name,
        metadata={
            "agent_id": spec.agent_id,
            "agent_type": agent_type,
            "framework": framework,
            "language": language,
            "source_tool": "forge_agent",
        },
    )

    # 构建输出
    output_parts = []

    # 新修仙者欢迎仪式
    if is_new:
        output_parts.append(generate_welcome_ceremony(creator))
        output_parts.append("\n---\n")

    output_parts.append("# ⚒️ 开炉炼器成功！\n")
    output_parts.append(format_agent_card(spec))
    output_parts.append(_build_forge_share_block(spec.agent_id, spec.name, spec.creator))

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

def _build_refine_share_block(agent_id: str, changes: str, refiner: str) -> str:
    """Build a paste-ready share block for successful artifact refinements."""
    install_command = _current_candidate_install_command()
    share_text = (
        f"我在 TianGong 淬炼法宝 `{agent_id}`：@{refiner} 完成一次优化，"
        f"+30 灵力。变化：{changes}"
    )

    return (
        "\n\n---\n\n"
        "## 📣 复制分享\n\n"
        "```text\n"
        f"{share_text}\n"
        f"加入修炼: {install_command}\n"
        "安装后复查: tiangong-mcp public-install-command\n"
        "PyPI 追平后安装: pip install -U tiangong-mcp\n"
        "```\n\n"
        "## 下一步\n\n"
        f"- 发布出世: `publish_agent` with `artifact_name=\"{agent_id}\"`\n"
        f"- 邀请鉴定: `infuse_spirit(artifact_name=\"{agent_id}\")`\n"
        f"- 查看修行名片: `my_realm(username=\"{refiner}\")`\n"
        "- 冲击法宝天榜: `leaderboard(type=\"artifact\")`\n"
        f"- 记录公开分享归因: {format_share_attribution_command(contribution='refine', actor=refiner, artifact_name=agent_id)}"
    )


def _format_cultivator_leaderboard(profiles, top_n: int) -> str:
    """Format the cultivator leaderboard as a shareable competitive surface."""
    profiles.sort(key=lambda p: (-p.realm_level, -p.spirit_power, p.username))
    ranked = profiles[:top_n]
    top_profile = ranked[0] if ranked else None

    lines = [
        "# 🏆 修仙天榜",
        "",
        "> 真实修仙者档案快照：来自当前 cultivators registry，不伪造历史排名。",
        "> 排序依据: 境界 > 灵力 > 用户名。",
        "",
        "| # | 修仙者 | 境界 | 阶位 | 灵力 | 法宝数 |",
        "|---|--------|------|------|------|--------|",
    ]

    for i, p in enumerate(ranked, 1):
        realm = p.realm
        lines.append(
            f"| {i} | @{p.username} | {realm.symbol} {realm.name_cn} | {p.stage}阶 | {p.spirit_power} | {p.agent_count} |"
        )

    if not profiles:
        lines.append("| — | 暂无修仙者 | — | — | — | — |")

    lines.extend([
        "",
        "---",
        "",
        "## 📣 复制分享",
        "",
        "```text",
    ])

    if top_profile:
        lines.append(
            f"我在 TianGong 看到 @{top_profile.username} 暂列修仙天榜第一，"
            f"境界 {top_profile.realm.symbol} {top_profile.realm.name_cn}，灵力 {top_profile.spirit_power}。"
        )
    else:
        lines.append("TianGong 修仙天榜等待第一位修仙者留名。")

    lines.extend([
        "加入修炼: pip install tiangong-mcp",
        "```",
        "",
        "## 下一步",
        "",
    ])

    if top_profile:
        lines.append(f"- 查看第一名名片: `my_realm(username=\"{top_profile.username}\")`")
    else:
        lines.append("- 开炉炼器: `forge_agent`")

    lines.extend([
        "- 查看赛季天榜: `leaderboard(type=\"season\")`",
        "- 查看修仙天榜: `leaderboard(type=\"cultivator\")`",
    ])

    return "\n".join(lines)


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
        await update_cultivator_stats(username=refiner, refinement_delta=1, spirit_delta=30)
        _record_activation_event_safely(
            EVENT_REFINE_SUCCEEDED,
            actor=refiner,
            artifact_name=agent_id,
            metadata={
                "agent_id": agent_id,
                "changes": changes,
                "source_tool": "refine_agent",
            },
        )
        message += _build_refine_share_block(agent_id, changes, refiner)

    return append_brand_footer(message)


# ============================================================
# 🔧 Tool 4: my_realm — 🧙 修行档案
# ============================================================

@mcp.tool()
async def my_realm(
    username: str = "",
    apprentice_username: str = "",
) -> str:
    """
    🧙 修行档案 — 查看你的修仙者境界和修行记录
    View your cultivator profile, realm, and cultivation history.

    展示你的当前境界、本命法宝、渡劫记录、以及距离下一次渡劫的进度。
    可选 apprentice_username 生成一张真实师徒传承邀请。

    Shows your current realm, natal artifacts, tribulation history,
    and progress to the next breakthrough.
    Optionally include apprentice_username to generate a grounded mentor-apprentice invite.

    Args:
        username: GitHub 用户名 / GitHub username (defaults to env config)
        apprentice_username: 徒弟 GitHub 用户名 / apprentice GitHub username
    """
    if not username:
        username = config.GITHUB_USERNAME

    profile = await get_cultivator(username)
    apprentice_profile = await get_cultivator(apprentice_username) if apprentice_username else None
    result = format_cultivator_profile(profile, apprentice=apprentice_profile)

    # 附加境界进度
    realm = profile.realm
    result += "\n\n" + format_realm_progress(
        realm, profile.spirit_power, profile.agent_count,
    )


    return append_brand_footer(result)


@mcp.tool()
async def check_tribulation(username: str = "") -> str:
    """
    ⚡ 渡劫检查 — 查看下一劫条件、缺口与可执行路线
    Check Tribulation — Inspect the next realm gate and action path.

    根据真实修仙者档案生成当前境界、下一劫任务、灵力缺口、可复制命令和分享战书。

    Args:
        username: GitHub 用户名 / GitHub username (defaults to env config)
    """
    if not username:
        username = config.GITHUB_USERNAME

    profile = await get_cultivator(username)
    return append_brand_footer(format_tribulation_check(profile))


def _format_tribulation_evidence_help(message: str) -> str:
    """Build an actionable help card for invalid tribulation evidence submissions."""
    lines = [
        "# ⚡ 渡劫证据入口纠错",
        "",
        f"> {message}",
        "> 公开入口快照：证据必须来自可审查的 http(s) URL；本工具只记录证据，不伪造排名、下载量或传承引用。",
        "",
        "## 可用 evidence_key",
        "",
        "| key | 目标境界 | 需要数量 | 证据含义 |",
        "|---|---|---:|---|",
    ]
    for spec in get_tribulation_evidence_specs():
        lines.append(f"| `{spec['key']}` | {spec['realm_name']} | {spec['required']} | {spec['label']} |")
    lines.extend(
        [
            "",
            "## 可复制命令",
            "",
            (
                "- 提交证据: `submit_tribulation_evidence(username=\"your_github_username\", "
                "evidence_key=\"lineage_users\", amount=1, source_url=\"https://github.com/owner/repo/issues/1\")`"
            ),
            "- 查看渡劫: `check_tribulation(username=\"your_github_username\")`",
            "- 冲击赛季天榜: `leaderboard(type=\"season\")`",
            "",
            "## 📣 复制证据纠错",
            "",
            "```text",
            "我在 TianGong 修正了一次渡劫证据提交：高阶境界必须绑定公开 URL，不靠口头进度越级。",
            "加入修炼: pip install tiangong-mcp",
            "```",
        ]
    )
    return "\n".join(lines)


def _format_tribulation_evidence_card(
    profile,
    evidence_key: str,
    amount: int,
    source_url: str,
    note: str,
    old_realm,
    new_realm,
) -> str:
    """Build a shareable card for a recorded tribulation evidence event."""
    progress = profile.tribulation_progress[evidence_key]
    current_amount = progress["amount"] if isinstance(progress, dict) else progress
    realm_shift = f"{old_realm.name_cn} → {new_realm.name_cn}"
    if old_realm.level == new_realm.level:
        realm_shift = f"暂未突破，仍为 {new_realm.name_cn}"
    note_line = f"- 证据说明: {note}" if note else "- 证据说明: 未填写，详见公开来源"
    return "\n".join(
        [
            f"# ⚡ 渡劫证据已记录 · @{profile.username}",
            "",
            f"> 真实证据快照：`{evidence_key}` +{amount}，当前累计 {current_amount}。",
            "> 没有伪造渡劫成功；此进度绑定公开 URL，可由社区审查。",
            "",
            "## 证据",
            "",
            f"- 修仙者: @{profile.username}",
            f"- 证据键: `{evidence_key}`",
            f"- 本次数量: {amount}",
            f"- 当前累计: {current_amount}",
            f"- 公开来源: {source_url}",
            note_line,
            f"- 境界变化: {realm_shift}",
            "",
            "## 下一步",
            "",
            f"- 查看渡劫: `check_tribulation(username=\"{profile.username}\")`",
            f"- 查看修行名片: `my_realm(username=\"{profile.username}\")`",
            "- 冲击赛季天榜: `leaderboard(type=\"season\")`",
            "- 进入天骄擂台: `leaderboard(type=\"tournament\")`",
            "",
            "## 📣 复制渡劫证据",
            "",
            "```text",
            (
                f"我在 TianGong 记录渡劫证据：@{profile.username} 的 `{evidence_key}` "
                f"+{amount}，公开来源 {source_url}。境界变化：{realm_shift}。"
            ),
            "加入修炼: pip install tiangong-mcp",
            f"查看渡劫: check_tribulation(username=\"{profile.username}\")",
            "```",
        ]
    )


@mcp.tool()
async def submit_tribulation_evidence(
    evidence_key: str,
    amount: int,
    source_url: str,
    username: str = "",
    note: str = "",
) -> str:
    """
    ⚡ 提交渡劫证据 — 记录高阶境界所需的公开、可审查证据
    Submit Tribulation Evidence — Record public evidence for high-realm gates.

    Args:
        evidence_key: 证据键，例如 lineage_users、artifact_downloads、dependent_projects
        amount: 本次公开证据证明的数量，必须为正整数
        source_url: 可公开审查的 http(s) 来源 URL
        username: GitHub 用户名 / GitHub username (defaults to env config)
        note: 证据说明 / one-line evidence note
    """
    if not username:
        username = config.GITHUB_USERNAME

    profile = await get_cultivator(username)
    try:
        old_realm, new_realm = add_tribulation_evidence(
            profile=profile,
            evidence_key=evidence_key,
            amount=amount,
            source_url=source_url,
            note=note,
        )
    except ValueError as exc:
        return append_brand_footer(_format_tribulation_evidence_help(str(exc)))

    await save_cultivator(profile, message=f"⚡ tribulation evidence: @{username} {evidence_key}")
    return append_brand_footer(
        _format_tribulation_evidence_card(
            profile=profile,
            evidence_key=evidence_key,
            amount=amount,
            source_url=source_url,
            note=note,
            old_realm=old_realm,
            new_realm=new_realm,
        )
    )





# ============================================================
# 🔧 Tool: leaderboard — 🏆 天榜
# ============================================================

def _format_leaderboard_type_help(message: str) -> str:
    """Build an actionable correction card for unsupported leaderboard types."""
    return "\n".join([
        "# 🏆 天榜类型纠错",
        "",
        f"> {message}",
        "> 公开入口快照：`leaderboard` 只支持 `artifact`、`cultivator`、`season`、`tournament`、`tournament_recap`、`sect`、`growth`、`share`。",
        "> 没有伪造排行榜，也没有静默切换到默认天榜；请使用下面任一公开命令继续修炼。",
        "",
        "## 可复制命令",
        "",
        "- 法宝天榜: `leaderboard(type=\"artifact\")`",
        "- 修仙天榜: `leaderboard(type=\"cultivator\")`",
        "- 赛季天榜: `leaderboard(type=\"season\")`",
        "- 天骄擂台: `leaderboard(type=\"tournament\")`",
        "- 擂台复盘: `leaderboard(type=\"tournament_recap\")`",
        "- 宗门战榜: `leaderboard(type=\"sect\")`",
        "- 增长飞轮: `leaderboard(type=\"growth\")` 或 `growth_flywheel()`",
        "- 分享证明天榜: `leaderboard(type=\"share\")`",
        "",
        "## 📣 复制天榜纠错",
        "",
        "```text",
        "我在 TianGong 修正了一次天榜入口：公开 type 是 artifact / cultivator / season / tournament / tournament_recap / sect / growth / share。",
        "加入修炼: pip install tiangong-mcp",
        "```",
    ])


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
    - season: 赛季天榜 — 按当前修仙档案快照战力排名
    - sect: 宗门战 — 按当前宗门档案快照战力排名
    - tournament: 天骄擂台 — 按当前修仙档案快照战力生成首轮挑战板
    - tournament_recap: 擂台复盘 — 按当前修仙档案快照生成胜者、差距与下一轮钩子
    - growth: 增长飞轮 — 按当前真实快照评估闭环与瓶颈
    - share: 分享证明天榜 — 按真实公开贡献分享证明排名

    Args:
        type: 天榜类型 / Leaderboard type: artifact, cultivator, season, sect, tournament, tournament_recap, growth, share
        top_n: 显示前 N 名 / Number of top entries to show
    """
    leaderboard_type = (type or "artifact").strip().lower()

    if leaderboard_type in ("share", "share_proof", "share-proof", "sharing"):
        event_path = get_activation_event_path()
        events = load_activation_events(path=event_path)
        return append_brand_footer(format_share_proof_leaderboard(events, source_path=event_path, top_n=top_n))

    if leaderboard_type in ("growth", "flywheel", "growth_flywheel"):
        profiles = await get_all_cultivators()
        artifacts = await list_agents()
        all_sects = await get_all_sects()
        event_path = get_activation_event_path()
        events = load_activation_events(path=event_path)
        return append_brand_footer(format_growth_flywheel(profiles, artifacts, all_sects, activation_events=events))

    if leaderboard_type == "season":
        profiles = await get_all_cultivators()
        return append_brand_footer(format_season_leaderboard(profiles, top_n=top_n))

    if leaderboard_type in ("tournament", "arena", "duel"):
        profiles = await get_all_cultivators()
        return append_brand_footer(format_tournament_board(profiles, top_n=top_n))

    if leaderboard_type in ("tournament_recap", "tournament-recap", "arena_recap", "arena-recap", "cup_recap", "cup-recap"):
        profiles = await get_all_cultivators()
        return append_brand_footer(format_tournament_recap(profiles, top_n=top_n))

    if leaderboard_type in ("sect", "sect_war", "sect-war"):
        all_sects = await get_all_sects()
        return append_brand_footer(format_sect_war_banner(all_sects, top_n=top_n))

    if leaderboard_type == "cultivator":
        profiles = await get_all_cultivators()
        return append_brand_footer(_format_cultivator_leaderboard(profiles, top_n=top_n))

    if leaderboard_type == "artifact":
        result = await get_leaderboard(top_n=top_n)
        result += "\n\n" + get_realm_ladder()
        return append_brand_footer(result)

    return append_brand_footer(
        _format_leaderboard_type_help(f"未知天榜 type: `{type}`。请改用公开 type 参数。")
    )


@mcp.tool()
async def growth_flywheel() -> str:
    """
    🌀 增长飞轮 — 查看当前真实闭环快照、最薄弱环节和下一步命令
    Growth Flywheel — Evaluate the current real growth loop snapshot.
    """
    profiles = await get_all_cultivators()
    artifacts = await list_agents()
    all_sects = await get_all_sects()
    event_path = get_activation_event_path()
    events = load_activation_events(path=event_path)
    return append_brand_footer(format_growth_flywheel(profiles, artifacts, all_sects, activation_events=events))


@mcp.tool()
async def growth_campaign(
    campaign_name: str = "",
    target_contributors: int = 10,
) -> str:
    """
    🚀 爆发战役 — 生成 72 小时公开增长战役卡
    Growth Campaign — Turn the current real flywheel bottleneck into a public launch card.

    Args:
        campaign_name: 战役名称 / campaign name
        target_contributors: 72 小时目标贡献者数量 / target contributors in 72 hours
    """
    profiles = await get_all_cultivators()
    artifacts = await list_agents()
    all_sects = await get_all_sects()
    event_path = get_activation_event_path()
    events = load_activation_events(path=event_path)
    return append_brand_footer(
        format_growth_campaign(
            profiles,
            artifacts,
            all_sects,
            activation_events=events,
            campaign_name=campaign_name,
            target_contributors=target_contributors,
        )
    )


@mcp.tool()
async def public_proof_pack(
    repo_owner: str = "",
    repo_name: str = "",
    target_contributors: int = 10,
    actor: str = "",
    artifact_name: str = "first-growth-artifact",
    contribution: str = "forge",
) -> str:
    """
    Public Proof Pack - no-network Growth/Share proof kit and external contributor invite.

    Args:
        repo_owner: GitHub repository owner; defaults to config.
        repo_name: GitHub repository name; defaults to config.
        target_contributors: 72-hour public campaign target used in proof URLs and recheck commands.
        actor: GitHub actor used in paste-ready ledger commands.
        artifact_name: artifact name used in the first Share Proof Issue and ledger command.
        contribution: contribution type for the Share Proof route.
    """
    return append_brand_footer(
        format_public_proof_pack(
            repo_owner=repo_owner,
            repo_name=repo_name,
            target_contributors=target_contributors,
            actor=actor,
            artifact_name=artifact_name,
            contribution=contribution,
        )
    )


@mcp.tool()
async def public_growth_report(record_snapshot: bool = False, target_contributors: int = 0) -> str:
    """
    Public Growth Report - compare real GitHub public traction with the local MCP growth ledger.

    Args:
        record_snapshot: when true, append the fetched public GitHub snapshot to the local growth history ledger.
        target_contributors: optional public campaign target contributor count for progress tracking.
    """
    event_path = get_activation_event_path()
    events = load_activation_events(path=event_path)
    snapshot_path = get_public_growth_snapshot_path()
    history = load_public_growth_snapshots(path=snapshot_path)
    try:
        snapshot = fetch_public_growth_snapshot()
    except Exception as exc:
        return append_brand_footer(
            format_public_growth_report(
                None,
                activation_events=events,
                source_path=event_path,
                history=history,
                history_path=snapshot_path,
                target_contributors=target_contributors,
                fetch_error=str(exc),
            )
        )
    snapshot_recorded = False
    if record_snapshot:
        record_public_growth_snapshot(snapshot, activation_events=events, path=snapshot_path)
        snapshot_recorded = True
    return append_brand_footer(
        format_public_growth_report(
            snapshot,
            activation_events=events,
            source_path=event_path,
            history=history,
            history_path=snapshot_path,
            snapshot_recorded=snapshot_recorded,
            target_contributors=target_contributors,
        )
    )


@mcp.tool()
async def public_install_command() -> str:
    """
    Public Install Command - shortest current install path based on real PyPI readiness.
    """
    distribution = fetch_public_distribution_readiness()
    return append_brand_footer(format_public_install_command(distribution))


@mcp.tool()
async def public_launch_preflight(target_contributors: int = 10) -> str:
    """
    Public Launch Preflight - direct release runbook for closing the public TianGong growth loop.

    Args:
        target_contributors: public campaign target contributor count used in recheck commands.
    """
    event_path = get_activation_event_path()
    events = load_activation_events(path=event_path)
    try:
        snapshot = fetch_public_growth_snapshot()
    except Exception as exc:
        return append_brand_footer(
            format_public_launch_preflight(
                None,
                activation_events=events,
                source_path=event_path,
                target_contributors=target_contributors,
                fetch_error=str(exc),
            )
        )
    return append_brand_footer(
        format_public_launch_preflight(
            snapshot,
            activation_events=events,
            source_path=event_path,
            target_contributors=target_contributors,
        )
    )


def _format_growth_referral_source_help(route: str, source_url: str) -> str:
    """Build an actionable correction card for invalid public referral sources."""
    route_arg = (route or "growth").replace("\\", "\\\\").replace('"', '\\"')
    source_arg = source_url or "https://github.com/owner/repo/issues/1"
    return "\n".join(
        [
            "# 📈 IssueOps 回流来源纠错",
            "",
            "> source_url 必须是公开 http(s) URL，才能作为可审查的外部回流来源。",
            "> 本次没有写入激活事件，也没有伪造下载量、留存或转介绍。",
            "",
            "## 可复制命令",
            "",
            (
                f"- 记录回流: `record_growth_referral(route=\"{route_arg}\", "
                f"source_url=\"{source_arg}\", actor=\"your_github_username\")`"
            ),
            "- 查看激活漏斗: `activation_funnel()`",
            "- 查看增长飞轮: `growth_flywheel()`",
            "- 发起 72 小时爆发战役: `growth_campaign()`",
            "- 验证公开牵引力: `public_growth_report()`",
            "- Invite next external contributor: `public_proof_pack()`",
            "",
            "## 📣 复制回流纠错",
            "",
            "```text",
            "我在 TianGong 记录外部回流前校准了来源：必须绑定公开 GitHub Issue/PR/Discussion URL，不能用不可审查的口头来源。",
            "加入修炼: pip install tiangong-mcp",
            "```",
        ]
        + [
            "> Use the created public Issue/PR/Discussion URL after submission; do not use issues/new form entrypoints or placeholder URLs.",
        ]
    )


@mcp.tool()
async def record_growth_referral(
    route: str = "growth",
    source_url: str = "",
    actor: str = "",
    issue_number: int = 0,
    campaign_hook: str = "",
) -> str:
    """
    📈 记录增长回流 — 把 GitHub IssueOps 外部入口回到 MCP 的动作写入真实激活账本
    Record Growth Referral — log a public IssueOps-to-MCP return event.

    Args:
        route: IssueOps 路由，例如 growth/quest/season/tournament/mentor/sect
        source_url: 公开 GitHub Issue/PR/Discussion URL
        actor: GitHub 用户名 / GitHub username
        issue_number: 可选 GitHub Issue 编号
        campaign_hook: 可选活动钩子
    """
    if not actor:
        actor = config.GITHUB_USERNAME
    normalized_route = (route or "growth").strip().lower()
    public_source = (source_url or "").strip()
    source_problem = _public_proof_url_problem(public_source, field_name="source_url")
    if source_problem:
        return append_brand_footer(_format_growth_referral_source_help(normalized_route, public_source))

    written, write_error = _record_activation_event_safely(
        EVENT_ISSUEOPS_REFERRAL_RECORDED,
        actor=actor,
        metadata={
            "route": normalized_route,
            "source_url": public_source,
            "issue_number": issue_number,
            "campaign_hook": campaign_hook,
            "source_tool": "record_growth_referral",
        },
    )

    if not written:
        return append_brand_footer(
            "\n".join(
                [
                    f"# 📈 IssueOps 回流未写入 · @{actor}",
                    "",
                    f"> 真实回流来源: {public_source}",
                    f"> 本地激活账本写入失败: {write_error}",
                    "> 没有伪造已记录事件，也没有伪造下载量、留存、转介绍或灵力奖励。",
                    "",
                    "## 下一步",
                    "",
                    "- 修复本地日志目录权限或设置可写的 `TIANGONG_CAVE_DIR` 后重试",
                    "- 查看真实激活漏斗: `activation_funnel()`",
                    "- 查看增长飞轮: `growth_flywheel()`",
                    "- 发起 72 小时爆发战役: `growth_campaign()`",
                    "- 验证公开牵引力: `public_growth_report()`",
                    "- Invite next external contributor: `public_proof_pack()`",
                    "",
                    "## 📣 复制回流恢复",
                    "",
                    "```text",
                    "我从 TianGong GitHub IssueOps 回到 MCP，但本地激活账本暂时不可写；先修复日志权限，再记录真实回流。",
                    "加入修炼: pip install tiangong-mcp",
                    "```",
                ]
            )
        )

    lines = [
        f"# 📈 IssueOps 回流已记录 · @{actor}",
        "",
        f"> 真实回流来源: {public_source}",
        "> 本工具只记录外部入口回到 MCP 的事实；不伪造下载量、留存、转介绍或灵力奖励。",
        "",
        "## 回流快照",
        "",
        f"- 路由: `{normalized_route}`",
        f"- 来源 Issue: #{issue_number}" if issue_number else "- 来源 Issue: 未提供编号，以 source_url 为准",
        f"- 活动钩子: {campaign_hook}" if campaign_hook else "- 活动钩子: 未填写",
        "",
        "## 下一步",
        "",
        "- 查看真实激活漏斗: `activation_funnel()`",
        "- 查看增长飞轮: `growth_flywheel()`",
        "- 发起 72 小时爆发战役: `growth_campaign()`",
        "- 验证公开牵引力: `public_growth_report()`",
        "- Invite next external contributor: `public_proof_pack()`",
        '- 首件法宝激活: `forge_agent(name="your-first-artifact", description="...")`',
        '- 发布增长悬赏: `quest(action="post", artifact_name="growth-referral-bounty", description="把这次 IssueOps 回流转成真实贡献")`',
        "- 查看赛季追赶: `leaderboard(type=\"season\")`",
        "",
        "## 📣 复制回流战报",
        "",
        "```text",
        (
            f"我从 TianGong GitHub IssueOps 回到 MCP：@{actor} 记录 `{normalized_route}` 回流，"
            "下一步用真实开炉、悬赏或鉴定补齐增长闭环。"
        ),
        "加入修炼: pip install tiangong-mcp",
        "复查激活: activation_funnel()",
        "复查飞轮: growth_flywheel()",
        "发起战役: growth_campaign()",
        "验证公开证明: public_growth_report()",
        "Next contributor invite: public_proof_pack()",
        "```",
    ]
    return append_brand_footer("\n".join(lines))


def _format_share_attribution_source_help(contribution: str, share_url: str, source_url: str = "") -> str:
    """Build an actionable correction card for invalid public share attribution sources."""
    contribution_arg = (contribution or "forge").replace("\\", "\\\\").replace('"', '\\"')
    share_arg = share_url or "https://github.com/owner/repo/issues/1"
    source_line = (
        "> source_url 如填写，也必须是公开 http(s) URL。"
        if source_url and not (source_url.startswith("https://") or source_url.startswith("http://"))
        else "> share_url 必须是公开 http(s) URL，才能作为可审查的贡献分享来源。"
    )
    return "\n".join(
        [
            "# 📣 贡献分享来源纠错",
            "",
            source_line,
            "> 本次没有写入激活事件，也没有伪造已分享、下载量、留存或转介绍。",
            "",
            "## 可复制命令",
            "",
            (
                f"- 记录分享: `record_share_attribution(contribution=\"{contribution_arg}\", "
                f"share_url=\"{share_arg}\", actor=\"your_github_username\")`"
            ),
            "- 查看激活漏斗: `activation_funnel()`",
            "- 查看增长飞轮: `growth_flywheel()`",
            "- 验证公开牵引力: `public_growth_report()`",
            "- Invite next external contributor: `public_proof_pack()`",
            "",
            "## 📣 复制分享纠错",
            "",
            "```text",
            "我在 TianGong 记录贡献分享前校准了公开来源：必须绑定可审查的 http(s) URL，不能用不可验证的私聊位置。",
            "加入修炼: pip install tiangong-mcp",
            "```",
        ]
        + [
            "> Use a created public post/Issue/PR/Discussion URL after submission; do not use issues/new form entrypoints or placeholder URLs.",
        ]
    )


@mcp.tool()
async def record_share_attribution(
    contribution: str,
    share_url: str,
    actor: str = "",
    artifact_name: str = "",
    source_url: str = "",
    issue_number: int = 0,
    campaign_hook: str = "",
) -> str:
    """
    📣 记录贡献分享归因 — 把一次真实贡献后的公开分享写入激活账本
    Record Share Attribution — bind a public share URL to a real TianGong contribution.

    Args:
        contribution: 贡献类型，例如 forge/refine/publish/infuse/quest/sect
        share_url: 公开可审查的分享 URL
        actor: GitHub 用户名 / GitHub username
        artifact_name: 相关法宝名称或 ID
        source_url: 可选 IssueOps 回流来源 URL
        issue_number: 可选 GitHub Issue 编号
        campaign_hook: 可选活动钩子
    """
    if not actor:
        actor = config.GITHUB_USERNAME
    normalized_contribution = (contribution or "forge").strip().lower()
    public_share_url = (share_url or "").strip()
    public_source_url = (source_url or "").strip()
    share_problem = _public_proof_url_problem(public_share_url, field_name="share_url")
    if share_problem:
        return append_brand_footer(
            _format_share_attribution_source_help(normalized_contribution, public_share_url, public_source_url)
        )
    source_problem = (
        _public_proof_url_problem(public_source_url, field_name="source_url") if public_source_url else ""
    )
    if source_problem:
        return append_brand_footer(
            _format_share_attribution_source_help(normalized_contribution, public_share_url, public_source_url)
        )

    written, write_error = _record_activation_event_safely(
        EVENT_SHARE_ATTRIBUTION_RECORDED,
        actor=actor,
        artifact_name=artifact_name,
        metadata={
            "contribution": normalized_contribution,
            "share_url": public_share_url,
            "source_url": public_source_url,
            "issue_number": issue_number,
            "campaign_hook": campaign_hook,
            "source_tool": "record_share_attribution",
        },
    )

    if not written:
        return append_brand_footer(
            "\n".join(
                [
                    f"# 📣 贡献分享未写入 · @{actor}",
                    "",
                    f"> 公开分享来源: {public_share_url}",
                    f"> 本地激活账本写入失败: {write_error}",
                    "> 没有伪造已记录分享，也没有伪造下载量、留存、转介绍或灵力奖励。",
                    "",
                    "## 下一步",
                    "",
                    "- 修复本地日志目录权限或设置可写的 `TIANGONG_CAVE_DIR` 后重试",
                    "- 查看真实激活漏斗: `activation_funnel()`",
                    "- 查看增长飞轮: `growth_flywheel()`",
                    "- 验证公开牵引力: `public_growth_report()`",
                    "- Invite next external contributor: `public_proof_pack()`",
                    "",
                    "## 📣 复制分享恢复",
                    "",
                    "```text",
                    "我已经完成 TianGong 贡献并准备公开分享，但本地激活账本暂时不可写；先修复日志权限，再记录真实分享归因。",
                    "加入修炼: pip install tiangong-mcp",
                    "```",
                ]
            )
        )

    lines = [
        f"# 📣 贡献分享已记录 · @{actor}",
        "",
        f"> 公开分享来源: {public_share_url}",
        "> 本工具只记录真实贡献后的公开分享归因；不伪造下载量、留存、转介绍或灵力奖励。",
        "",
        "## 分享快照",
        "",
        f"- 贡献类型: `{normalized_contribution}`",
        f"- 法宝: `{artifact_name}`" if artifact_name else "- 法宝: 未提供，以贡献类型为准",
        f"- 来源回流: {public_source_url}" if public_source_url else "- 来源回流: 未填写",
        f"- 来源 Issue: #{issue_number}" if issue_number else "- 来源 Issue: 未提供编号",
        f"- 活动钩子: {campaign_hook}" if campaign_hook else "- 活动钩子: 未填写",
        "",
        "## 下一步",
        "",
        "- 查看真实激活漏斗: `activation_funnel()`",
        "- 查看增长飞轮: `growth_flywheel()`",
        "- 验证公开牵引力: `public_growth_report()`",
        "- Invite next external contributor: `public_proof_pack()`",
        "- 继续公开贡献: `quest(action=\"browse\")`",
        "- 查看赛季追赶: `leaderboard(type=\"season\")`",
        "",
        "## 📣 复制分享战报",
        "",
        "```text",
        (
            f"我在 TianGong 完成 `{normalized_contribution}` 贡献并公开分享：{public_share_url}。"
            "这次传播已写入真实激活账本。"
        ),
        "加入修炼: pip install tiangong-mcp",
        "复查激活: activation_funnel()",
        "复查飞轮: growth_flywheel()",
        "Next contributor invite: public_proof_pack()",
        "```",
    ]
    return append_brand_footer("\n".join(lines))


@mcp.tool()
async def activation_funnel(username: str = "") -> str:
    """
    📈 真实激活漏斗 — 查看本地 MCP 事件账本中的首会话转化
    Activation Funnel — Evaluate real local first-session conversion events.

    Args:
        username: 可选 GitHub 用户名过滤 / optional GitHub username filter
    """
    event_path = get_activation_event_path()
    events = load_activation_events(path=event_path)
    return append_brand_footer(
        format_activation_funnel(
            events,
            source_path=event_path,
            username=username,
        )
    )


@mcp.tool()
async def share_attribution_report(username: str = "") -> str:
    """
    Share Attribution Report - summarize public contribution-share proof from the local MCP event ledger.

    Args:
        username: optional GitHub username filter
    """
    event_path = get_activation_event_path()
    events = load_activation_events(path=event_path)
    return append_brand_footer(
        format_share_attribution_report(
            events,
            source_path=event_path,
            username=username,
        )
    )


# ============================================================
# Phase 2: 分发平台新工具
# ============================================================

def _format_treasure_pavilion_action_help(message: str) -> str:
    """Build an actionable correction card for Treasure Pavilion input errors."""
    return "\n".join([
        "# 🏛️ 寻宝阁行动纠错",
        "",
        f"> {message}",
        "> 公开入口快照：`treasure_pavilion` 只支持 `search`、`summon`、`lineage`。",
        "> 没有伪造搜索结果；请使用下面任一公开工具命令继续修炼。",
        "",
        "## 可复制命令",
        "",
        "- 搜索法宝: `treasure_pavilion(action=\"search\")`",
        "- 请宝下凡: `treasure_pavilion(action=\"summon\", artifact_name=\"artifact-name\")`",
        "- 追溯传承: `treasure_pavilion(action=\"lineage\", artifact_name=\"artifact-name\")`",
        "- 冲击法宝天榜: `leaderboard(type=\"artifact\")`",
        "",
        "## 📣 复制寻宝纠错",
        "",
        "```text",
        "我在 TianGong 寻宝阁修正了一次请宝路径：公开入口是 treasure_pavilion(action=\"search|summon|lineage\")。",
        "加入修炼: pip install tiangong-mcp",
        "```",
    ])


def _format_summon_artifact_recovery(message: str, artifact_name: str) -> str:
    """Build an actionable correction card for failed artifact summons."""
    artifact = artifact_name or "artifact-name"
    artifact_arg = artifact.replace("\\", "\\\\").replace('"', '\\"')
    return "\n".join([
        "# 🏛️ 请宝下凡纠错",
        "",
        f"> {message}",
        "> 真实请宝失败快照：本次请宝只读取公开寻宝阁元数据，并尝试写入本地 vault/。",
        "> 没有写入本地藏宝阁，也没有伪造已安装法宝；请使用下面任一公开命令继续修炼。",
        "",
        "## 可复制命令",
        "",
        f"- 搜索同名法宝: `treasure_pavilion(action=\"search\", query=\"{artifact_arg}\")`",
        (
            f"- 发布悬赏: `quest(action=\"post\", artifact_name=\"{artifact_arg}\", "
            f"description=\"需要一件可召唤的 {artifact_arg} 法宝\")`"
        ),
        (
            f"- 亲自开炉: `forge_agent(name=\"{artifact_arg}\", "
            f"description=\"A TianGong artifact for {artifact_arg}\")`"
        ),
        "- 查看洞府: `my_vault()`",
        "- 冲击法宝天榜: `leaderboard(type=\"artifact\")`",
        "",
        "## 📣 复制请宝纠错",
        "",
        "```text",
        f"我在 TianGong 请宝「{artifact}」时发现寻宝阁空位：正在公开搜索、发悬赏或亲自开炉补齐这条道统。",
        "加入修炼: pip install tiangong-mcp",
        "```",
    ])


def _should_recover_summon_failure(result: str) -> bool:
    """Return True for failed summons, while preserving the existing-local guidance."""
    if result.startswith("❌"):
        return True
    return result.startswith("⚠️") and "已存在于藏宝阁" not in result


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
    normalized_action = (action or "search").strip().lower()
    allowed_actions = {"search", "summon", "lineage"}
    if normalized_action not in allowed_actions:
        return append_brand_footer(
            _format_treasure_pavilion_action_help(
                f"未知寻宝阁 action: `{action}`。请改用公开 action 参数。"
            )
        )

    if normalized_action == "summon":
        if not artifact_name:
            return append_brand_footer(
                _format_treasure_pavilion_action_help(
                    "请指定要拉取的法宝名称 (artifact_name)。"
                )
            )
        result = await _summon(artifact_name)
        if _should_recover_summon_failure(result):
            result = _format_summon_artifact_recovery(result, artifact_name)
        return append_brand_footer(result)

    elif normalized_action == "lineage":
        if not artifact_name:
            return append_brand_footer(
                _format_treasure_pavilion_action_help(
                    "请指定要查看传承的法宝名称 (artifact_name)。"
                )
            )
        tree = await get_artifact_lineage(artifact_name)
        return append_brand_footer(format_lineage_tree(tree))

    else:  # search (default)
        results = await search_marketplace(query=query)
        return append_brand_footer(format_search_results(results, query))


# 🔧 Tool: publish_agent — ✨ 法宝出世
def _format_publish_agent_recovery(message: str, artifact_name: str) -> str:
    """Build an actionable correction card for failed publish attempts."""
    artifact = artifact_name or "artifact-name"
    artifact_arg = artifact.replace("\\", "\\\\").replace('"', '\\"')
    return "\n".join([
        "# ✨ 法宝出世纠错",
        "",
        f"> {message}",
        "> 真实本地发布失败快照：发布只检查当前 forge/ 目录、本地法宝元数据和发布配置。",
        "> 没有伪造发布结果，也没有写入寻宝阁；请使用下面任一公开命令继续修炼。",
        "",
        "## 可复制命令",
        "",
        (
            f"- 开炉炼器: `forge_agent(name=\"{artifact_arg}\", "
            f"description=\"A TianGong artifact for {artifact_arg}\")`"
        ),
        "- 查看洞府: `my_vault()`",
        (
            f"- 发布悬赏: `quest(action=\"post\", artifact_name=\"{artifact_arg}\", "
            f"description=\"需要一件可发布的 {artifact_arg} 法宝\")`"
        ),
        f"- 搜索同名法宝: `treasure_pavilion(action=\"search\", query=\"{artifact_arg}\")`",
        "- 冲击法宝天榜: `leaderboard(type=\"artifact\")`",
        "",
        "## 📣 复制发布纠错",
        "",
        "```text",
        f"我在 TianGong 发布「{artifact}」前修正了本地炼器路径：先开炉、再飞升、再入天榜。",
        "加入修炼: pip install tiangong-mcp",
        "```",
    ])


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
    if result.startswith(("⚠️", "❌")):
        result = _format_publish_agent_recovery(result, artifact_name)
    else:
        _record_activation_event_safely(
            EVENT_PUBLISH_SUCCEEDED,
            actor="anonymous" if is_anonymous else config.GITHUB_USERNAME,
            artifact_name=artifact_name,
            metadata={
                "is_anonymous": is_anonymous,
                "source_tool": "publish_agent",
            },
        )
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
def _format_infuse_spirit_recovery(message: str, artifact_name: str, reviewer: str) -> str:
    """Build an actionable correction card for appraisal validation failures."""
    artifact = artifact_name or "artifact-name"
    realm_command = f"`my_realm(username=\"{reviewer}\")`" if reviewer else "`my_realm()`"
    return "\n".join([
        "# 🔮 法宝鉴定纠错",
        "",
        f"> {message}",
        "> 公开入口快照：`infuse_spirit` 六维评分必须全部是 1-10 的整数。",
        "> 没有伪造鉴定结果，也没有授予灵力；请使用下面任一公开命令继续修炼。",
        "",
        "## 可复制命令",
        "",
        (
            f"- 重新鉴定: `infuse_spirit(artifact_name=\"{artifact}\", inscription=5, "
            "formation=5, technique=5, lineage_score=5, resilience=5, "
            "enlightenment=5, comment=\"...\")`"
        ),
        f"- 搜索法宝: `treasure_pavilion(action=\"search\", query=\"{artifact}\")`",
        f"- 请宝下凡: `treasure_pavilion(action=\"summon\", artifact_name=\"{artifact}\")`",
        (
            f"- 发布鉴定悬赏: `quest(action=\"post\", artifact_name=\"{artifact}\", "
            "description=\"需要更高质量的鉴定样例\")`"
        ),
        "- 冲击赛季天榜: `leaderboard(type=\"season\")`",
        f"- 查看修行名片: {realm_command}",
        "",
        "## 📣 复制鉴定纠错",
        "",
        "```text",
        f"我在 TianGong 重新校准了「{artifact}」的六维鉴定：公开评分范围是 1-10。",
        "加入修炼: pip install tiangong-mcp",
        "```",
    ])


def _is_infuse_spirit_score_failure(message: str) -> bool:
    """Return True only for score-shape failures, not reviewer eligibility failures."""
    return "评分必须为 1-10" in message or "缺少维度" in message


def _format_infuse_spirit_eligibility_recovery(
    message: str,
    artifact_name: str,
    reviewer: str,
) -> str:
    """Build an onboarding recovery card for reviewer eligibility failures."""
    artifact = artifact_name or "artifact-name"
    artifact_arg = artifact.replace("\\", "\\\\").replace('"', '\\"')
    reviewer_arg = reviewer.replace("\\", "\\\\").replace('"', '\\"') if reviewer else ""
    realm_command = f"`my_realm(username=\"{reviewer_arg}\")`" if reviewer_arg else "`my_realm()`"
    first_artifact = "my-first-artifact"
    return "\n".join([
        "# 🔮 法宝鉴定资格恢复",
        "",
        f"> {message}",
        "> 真实鉴定资格失败快照：本次鉴定只检查当前修仙者档案、法宝数量和每日评价上限。",
        "> 没有伪造鉴定结果，也没有授予灵力；请先完成入门/冷却动作后再鉴定。",
        "",
        "## 可复制命令",
        "",
        (
            f"- 开炉炼器: `forge_agent(name=\"{first_artifact}\", "
            f"description=\"A TianGong artifact for {first_artifact}\")`"
        ),
        f"- 发布出世: `publish_agent(artifact_name=\"{first_artifact}\")`",
        f"- 搜索待鉴定法宝: `treasure_pavilion(action=\"search\", query=\"{artifact_arg}\")`",
        "- 浏览悬赏: `quest(action=\"browse\")`",
        "- 冲击赛季天榜: `leaderboard(type=\"season\")`",
        f"- 查看修行名片: {realm_command}",
        "",
        "## 📣 复制鉴定资格恢复",
        "",
        "```text",
        (
            f"我在 TianGong 鉴定「{artifact}」前补齐修仙资格："
            "先开炉发布本命法宝，再以修仙者身份为道友灌注灵力。"
        ),
        "加入修炼: pip install tiangong-mcp",
        "```",
    ])


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
    if result.startswith("# 💫 灵力灌注成功"):
        _record_activation_event_safely(
            EVENT_INFUSE_SUCCEEDED,
            actor=reviewer,
            artifact_name=artifact_name,
            metadata={
                "avg_score": round(sum(scores.values()) / len(scores), 2),
                "source_tool": "infuse_spirit",
            },
        )
    elif result.startswith("⚠️"):
        if _is_infuse_spirit_score_failure(result):
            result = _format_infuse_spirit_recovery(result, artifact_name, reviewer)
        else:
            result = _format_infuse_spirit_eligibility_recovery(result, artifact_name, reviewer)
    return append_brand_footer(result)


# 🔧 Tool: quest — 📜 悬赏令
def _format_quest_action_help(message: str, quest_issue_number: int = 0) -> str:
    """Build an actionable correction card for Quest Board input errors."""
    example_issue = quest_issue_number or 88
    return "\n".join([
        "# 📜 悬赏令行动纠错",
        "",
        f"> {message}",
        "> 公开入口快照：`quest` 只支持 `browse`、`post`、`claim`、`submit`。",
        "> 没有伪造悬赏榜，也没有伪造成果提交；请使用下面任一公开命令继续修炼。",
        "",
        "## 可复制命令",
        "",
        "- 浏览悬赏: `quest(action=\"browse\")`",
        "- 发布悬赏: `quest(action=\"post\", artifact_name=\"artifact-name\", description=\"需要改进的内容\")`",
        f"- 认领悬赏: `quest(action=\"claim\", quest_issue_number={example_issue})`",
        f"- 提交成果: `quest(action=\"submit\", quest_issue_number={example_issue}, solution=\"...\")`",
        "- 验收成果: `verify_refinement`",
        "- 冲击赛季天榜: `leaderboard(type=\"season\")`",
        "",
        "## 📣 复制悬赏纠错",
        "",
        "```text",
        "我在 TianGong 悬赏令修正了一次任务路径：公开入口是 quest(action=\"browse|post|claim|submit\")。",
        "加入修炼: pip install tiangong-mcp",
        "```",
    ])


def _format_quest_side_effect_recovery(
    message: str,
    action: str,
    artifact_name: str = "",
    description: str = "",
    quest_issue_number: int = 0,
    solution: str = "",
    username: str = "",
) -> str:
    """Build an actionable correction card for failed Quest Board side effects."""
    artifact = artifact_name or "artifact-name"
    artifact_arg = artifact.replace("\\", "\\\\").replace('"', '\\"')
    description_arg = (description or "需要改进的内容").replace("\\", "\\\\").replace('"', '\\"')
    solution_arg = (solution or "...").replace("\\", "\\\\").replace('"', '\\"')
    example_issue = quest_issue_number or 88
    realm_command = f"`my_realm(username=\"{username}\")`" if username else "`my_realm()`"
    action_labels = {
        "post": "发布悬赏",
        "claim": "认领悬赏",
        "submit": "提交成果",
    }
    action_label = action_labels.get(action, "执行悬赏令")

    return "\n".join([
        "# 📜 悬赏令失败恢复",
        "",
        f"> {message}",
        (
            f"> 真实悬赏失败快照：本次{action_label}只尝试写入 GitHub Issue/评论；"
            "失败时没有写入 GitHub Issue，也没有发放灵力。"
        ),
        "> 没有伪造悬赏榜，也没有伪造成果提交；请使用下面任一公开命令继续修炼。",
        "",
        "## 可复制命令",
        "",
        "- 补全配置: 在 `.env` 配置 `GITHUB_TOKEN` 后重试公开命令",
        "- 浏览悬赏: `quest(action=\"browse\")`",
        (
            f"- 重新发布悬赏: `quest(action=\"post\", artifact_name=\"{artifact_arg}\", "
            f"description=\"{description_arg}\")`"
        ),
        f"- 搜索法宝: `treasure_pavilion(action=\"search\", query=\"{artifact_arg}\")`",
        f"- 认领悬赏: `quest(action=\"claim\", quest_issue_number={example_issue})`",
        (
            f"- 提交成果: `quest(action=\"submit\", quest_issue_number={example_issue}, "
            f"solution=\"{solution_arg}\")`"
        ),
        "- 冲击赛季天榜: `leaderboard(type=\"season\")`",
        f"- 查看修行名片: {realm_command}",
        "",
        "## 📣 复制悬赏失败恢复",
        "",
        "```text",
        (
            f"我在 TianGong {action_label}时发现 IssueOps 尚未打通："
            "先补 GITHUB_TOKEN，再把这张悬赏令变成公开招募入口。"
        ),
        "加入修炼: pip install tiangong-mcp",
        "```",
    ])


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

    normalized_action = (action or "browse").strip().lower()
    allowed_actions = {"browse", "post", "claim", "submit"}
    if normalized_action not in allowed_actions:
        return append_brand_footer(
            _format_quest_action_help(
                f"未知悬赏令 action: `{action}`。请改用公开 action 参数。",
                quest_issue_number=quest_issue_number,
            )
        )

    if normalized_action == "post":
        if not artifact_name or not description:
            return append_brand_footer(
                _format_quest_action_help(
                    "发布悬赏令需要 artifact_name 和 description。",
                    quest_issue_number=quest_issue_number,
                )
            )
        result = await _post_quest(artifact_name, description, username, code_url)
        if result.startswith(("⚠️", "❌")):
            result = _format_quest_side_effect_recovery(
                result,
                action="post",
                artifact_name=artifact_name,
                description=description,
                username=username,
            )
        return append_brand_footer(result)

    elif normalized_action == "claim":
        if not quest_issue_number:
            return append_brand_footer(
                _format_quest_action_help(
                    "认领悬赏令需要 quest_issue_number。",
                    quest_issue_number=quest_issue_number,
                )
            )
        result = await _claim_quest(quest_issue_number, username)
        if result.startswith(("⚠️", "❌")):
            result = _format_quest_side_effect_recovery(
                result,
                action="claim",
                quest_issue_number=quest_issue_number,
                username=username,
            )
        return append_brand_footer(result)

    elif normalized_action == "submit":
        if not quest_issue_number or not solution:
            return append_brand_footer(
                _format_quest_action_help(
                    "提交成果需要 quest_issue_number 和 solution。",
                    quest_issue_number=quest_issue_number,
                )
            )
        result = await _submit_refinement(quest_issue_number, username, solution)
        if result.startswith(("⚠️", "❌")):
            result = _format_quest_side_effect_recovery(
                result,
                action="submit",
                quest_issue_number=quest_issue_number,
                solution=solution,
                username=username,
            )
        return append_brand_footer(result)

    else:  # browse (default)
        result = await _browse_quests(limit)
        return append_brand_footer(result)


# 🔧 Tool: verify_refinement — ⚖️ 审核淬炼成果
def _format_verify_refinement_recovery(
    message: str,
    quest_issue_number: int,
    refiner: str,
    is_approved: bool,
    feedback: str,
) -> str:
    """Build an actionable correction card for failed refinement verification."""
    example_issue = quest_issue_number or 88
    refiner_arg = refiner.replace("\\", "\\\\").replace('"', '\\"') if refiner else "refiner"
    feedback_arg = (feedback or "...").replace("\\", "\\\\").replace('"', '\\"')
    return "\n".join([
        "# ⚖️ 淬炼验收失败恢复",
        "",
        f"> {message}",
        (
            "> 真实验收失败快照：本次验收只尝试写入 GitHub Issue 评论；"
            "审核通过时才会关闭 Issue 并发放 +50 灵力。"
        ),
        "> 没有写入 GitHub Issue 评论，没有关闭 Issue，也没有发放灵力；请使用下面任一公开命令继续修炼。",
        "",
        "## 可复制命令",
        "",
        "- 补全配置: 在 `.env` 配置 `GITHUB_TOKEN` 后重试验收",
        (
            f"- 重新验收: `verify_refinement(quest_issue_number={example_issue}, "
            f"refiner=\"{refiner_arg}\", is_approved={is_approved}, feedback=\"{feedback_arg}\")`"
        ),
        f"- 提交成果: `quest(action=\"submit\", quest_issue_number={example_issue}, solution=\"...\")`",
        "- 浏览悬赏: `quest(action=\"browse\")`",
        f"- 查看淬炼者名片: `my_realm(username=\"{refiner_arg}\")`",
        "- 冲击赛季天榜: `leaderboard(type=\"season\")`",
        "",
        "## 📣 复制验收失败恢复",
        "",
        "```text",
        (
            f"我在 TianGong 验收 Issue #{example_issue} 时发现 IssueOps 尚未打通："
            "先补 GITHUB_TOKEN，再正式发放灵力与关闭悬赏。"
        ),
        "加入修炼: pip install tiangong-mcp",
        "```",
    ])


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
    if result.startswith(("⚠️", "❌")):
        result = _format_verify_refinement_recovery(
            result,
            quest_issue_number=quest_issue_number,
            refiner=refiner,
            is_approved=is_approved,
            feedback=feedback,
        )
    return append_brand_footer(result)


# ============================================================
# Phase 2.5: 宗门系统
# ============================================================

def _format_sect_action_help(message: str, username: str = "") -> str:
    """Build an actionable correction card for Sect command routing errors."""
    realm_command = f"`my_realm(username=\"{username}\")`" if username else "`my_realm()`"
    return "\n".join([
        "# ⛰️ 宗门行动纠错",
        "",
        f"> {message}",
        "> 公开入口快照：`sect` 只支持 `info`、`leaderboard`、`create`、`join`、`leave`、`manage`。",
        "> 没有伪造宗门信息，也没有伪造宗门战结果；请使用下面任一公开命令继续修炼。",
        "",
        "## 可复制命令",
        "",
        "- 开宗立派: `sect(action=\"create\", sect_name=\"天工盟\", motto=\"以凡人之躯，铸逆天之器\")`",
        "- 拜入宗门: `sect(action=\"join\", sect_name=\"sect-name\")`",
        "- 查看宗门: `sect(action=\"info\", sect_name=\"sect-name\")`",
        "- 查看宗门战报: `sect(action=\"leaderboard\")`",
        "- 冲击宗门战榜: `leaderboard(type=\"sect\")`",
        f"- 查看修行名片: {realm_command}",
        "",
        "## 📣 复制宗门纠错",
        "",
        "```text",
        "我在 TianGong 宗门系统修正了一次入宗路径：公开入口是 sect(action=\"info|leaderboard|create|join|leave|manage\")。",
        "加入修炼: pip install tiangong-mcp",
        "```",
    ])


@mcp.tool()
async def sect(
    action: str = "info",
    sect_name: str = "",
    motto: str = "",
    target_user: str = "",
    manage_action: str = "",
    username: str = "",
    top_n: int = 10,
) -> str:
    """
    ⛰️ 宗门系统 — 开宗立派、拜入宗门、宗门管理
    Sect System — Create, join, manage, and view cultivation sects.

    通过 action 参数指定操作：
    - info: 查看宗门信息（需 sect_name），如属于某宗门则传自己的 sect_name
    - leaderboard: 宗门天榜 — 按宗门总灵力排行
    - create: 开宗立派（需 sect_name, 可选 motto），要求境界 ≥ 结丹期
    - join: 拜入宗门（需 sect_name）
    - leave: 退出当前宗门（有 7 天冷却期）
    - manage: 宗门管理（需 target_user 和 manage_action）

    管理操作 (manage_action) 支持：
    - promote_elder: 任命长老 (仅宗主)
    - promote_inner: 升为内门弟子 (宗主/长老)
    - demote: 降为外门弟子 (宗主/长老)
    - kick: 踢出宗门 (宗主/长老)
    - transfer: 传位 (仅宗主)
    - disband: 解散宗门 (仅宗主)

    Args:
        action: 操作类型 (info/leaderboard/create/join/leave/manage)
        sect_name: 宗门名称 (create/join/info 必填)
        motto: 宗门宣言 (create 可填)
        target_user: 目标成员用户名 (manage 必填)
        manage_action: 管理操作 (manage 必填)
        username: 当前操作者 GitHub 用户名
        top_n: 排行榜显示数量 (leaderboard 默认 10)
    """
    if not username:
        username = config.GITHUB_USERNAME

    normalized_action = (action or "info").strip().lower()
    allowed_actions = {"info", "leaderboard", "create", "join", "leave", "manage"}
    if normalized_action not in allowed_actions:
        return append_brand_footer(
            _format_sect_action_help(
                f"未知宗门 action: `{action}`。请改用公开 action 参数。",
                username=username,
            )
        )

    # 1. 宗门天榜
    if normalized_action == "leaderboard":
        all_sects = await get_all_sects()
        return append_brand_footer(format_sect_war_banner(all_sects, top_n=top_n))

    # 2. 从当前修仙者获取宗门
    from .cultivator import get_cultivator
    profile = await get_cultivator(username)

    # 如果没传 sect_name，默认用自己当前的宗门
    target_sect = sect_name if sect_name else profile.sect

    # 3. 创建宗门
    if normalized_action == "create":
        if not sect_name:
            return append_brand_footer(
                _format_sect_action_help(
                    "开宗立派需要指定宗门名称 `sect_name`。",
                    username=username,
                )
            )
        success, msg = await _create_sect(sect_name, username, motto)
        return append_brand_footer(msg)

    # 4. 拜入宗门
    elif normalized_action == "join":
        if not sect_name:
            return append_brand_footer(
                _format_sect_action_help(
                    "拜入宗门需要指定目标宗门名称 `sect_name`。",
                    username=username,
                )
            )
        success, msg = await _join_sect(sect_name, username)
        return append_brand_footer(msg)

    # 5. 退出宗门
    elif normalized_action == "leave":
        success, msg = await _leave_sect(username)
        return append_brand_footer(msg)

    # 6. 管理宗门
    elif normalized_action == "manage":
        if not target_sect:
            return append_brand_footer(
                _format_sect_action_help(
                    "你当前不属于任何宗门，无法执行宗门管理。",
                    username=username,
                )
            )
        if not target_user:
            return append_brand_footer(
                _format_sect_action_help(
                    "请指定要管理的目标用户 `target_user`。",
                    username=username,
                )
            )
        if not manage_action:
            return append_brand_footer(
                _format_sect_action_help(
                    "请指定具体的管理操作 `manage_action`。",
                    username=username,
                )
            )

        success, msg = await _manage_sect(target_sect, manage_action, target_user, username)
        return append_brand_footer(msg)

    # 7. 查看宗门信息
    else:  # info
        if not target_sect:
            return append_brand_footer(
                _format_sect_action_help(
                    "请指定要查看的宗门名称 `sect_name`，或先拜入/创建宗门。",
                    username=username,
                )
            )

        # 顺便刷新一下灵力
        from .sect import refresh_sect_spirit
        await refresh_sect_spirit(target_sect)

        sect_profile = await _get_sect(target_sect)
        if not sect_profile:
            return append_brand_footer(
                _format_sect_action_help(
                    f"宗门「{target_sect}」不存在。",
                    username=username,
                )
            )

        candidate_profile = profile if profile.username not in sect_profile.members else None
        return append_brand_footer(format_sect_card(sect_profile, candidate=candidate_profile))




# ============================================================
# 🚀 启动入口
# ============================================================

def main():
    """启动 TianGong MCP Server"""
    mcp.run()


if __name__ == "__main__":
    main()
