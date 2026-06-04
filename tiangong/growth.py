"""Growth flywheel surfaces built from current TianGong registry snapshots."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode

from .activation import EVENT_SHARE_ATTRIBUTION_RECORDED, ActivationEvent, build_share_proof_issue_url
from .config import config
from .cultivator import CultivatorProfile
from .forge import AgentSpec
from .sect import SectProfile

GROWTH_ISSUE_TEMPLATE = "tiangong-growth-flywheel.yml"


@dataclass(frozen=True)
class GrowthStage:
    """One measurable step in the TianGong growth flywheel."""

    label: str
    value: str
    rate: float
    next_action: str
    denominator: int


def _format_percent(value: float) -> str:
    return f"{value * 100:.1f}%"


def _rate(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return min(1.0, max(0.0, numerator / denominator))


def _progress_value(value: Any) -> int:
    """Convert supported evidence shapes into a comparable count."""
    if isinstance(value, bool):
        return 1 if value else 0
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, str):
        stripped = value.strip()
        if stripped.isdigit():
            return int(stripped)
        return 1 if stripped else 0
    if isinstance(value, dict):
        for key in ("amount", "count", "value", "total"):
            if key in value:
                return _progress_value(value.get(key))
        evidence = value.get("evidence")
        if isinstance(evidence, list):
            return sum(
                _progress_value(item.get("amount", 1)) if isinstance(item, dict) else 1
                for item in evidence
            )
        return len(value)
    if isinstance(value, (list, tuple, set)):
        return len(value)
    return 0


def _has_tribulation_evidence(profile: CultivatorProfile) -> bool:
    return any(_progress_value(value) > 0 for value in profile.tribulation_progress.values())


def _build_growth_stages(
    profiles: Sequence[CultivatorProfile],
    artifacts: Sequence[AgentSpec],
    activation_events: Sequence[ActivationEvent] | None = None,
) -> list[GrowthStage]:
    total_profiles = len(profiles)
    activated_profiles = [profile for profile in profiles if profile.agent_count > 0]
    activated_count = len(activated_profiles)
    artifact_supply = min(len(artifacts), activated_count)
    reviewers = sum(1 for profile in activated_profiles if profile.reviews_given > 0)
    refiners = sum(1 for profile in activated_profiles if profile.refinement_count > 0)
    questers = sum(1 for profile in activated_profiles if profile.quests_completed > 0)
    sect_members = sum(1 for profile in activated_profiles if profile.sect)
    evidence_submitters = sum(1 for profile in activated_profiles if _has_tribulation_evidence(profile))
    public_share_actors = {
        event.actor
        for event in (activation_events or ())
        if event.event_type == EVENT_SHARE_ATTRIBUTION_RECORDED
        and event.actor
        and str(event.metadata.get("share_url", "")).startswith(("https://", "http://"))
    }

    stages = [
        GrowthStage(
            label="修仙者档案",
            value=f"{total_profiles} 位",
            rate=1.0 if total_profiles else 0.0,
            next_action='`forge_agent(name="first-growth-artifact", description="...")`',
            denominator=total_profiles,
        ),
        GrowthStage(
            label="首件法宝激活",
            value=f"{activated_count}/{total_profiles}",
            rate=_rate(activated_count, total_profiles),
            next_action='`forge_agent(name="your-first-artifact", description="...")`',
            denominator=total_profiles,
        ),
        GrowthStage(
            label="公开法宝供给",
            value=f"{len(artifacts)} 件",
            rate=_rate(artifact_supply, activated_count),
            next_action='`publish_agent(artifact_name="artifact-name")`',
            denominator=activated_count,
        ),
        GrowthStage(
            label="鉴定回流",
            value=f"{reviewers}/{activated_count}",
            rate=_rate(reviewers, activated_count),
            next_action='`infuse_spirit(artifact_name="artifact-name")`',
            denominator=activated_count,
        ),
        GrowthStage(
            label="淬炼复访",
            value=f"{refiners}/{activated_count}",
            rate=_rate(refiners, activated_count),
            next_action='`refine_agent(agent_id="artifact-id", changes="...")`',
            denominator=activated_count,
        ),
        GrowthStage(
            label="悬赏闭环",
            value=f"{questers}/{activated_count}",
            rate=_rate(questers, activated_count),
            next_action='`quest(action="post", artifact_name="growth-bounty", description="补齐 TianGong 增长飞轮的下一环")`',
            denominator=activated_count,
        ),
        GrowthStage(
            label="宗门归属",
            value=f"{sect_members}/{activated_count}",
            rate=_rate(sect_members, activated_count),
            next_action='`sect(action="join", sect_name="sect-name")`',
            denominator=activated_count,
        ),
        GrowthStage(
            label="高阶证据",
            value=f"{evidence_submitters}/{activated_count}",
            rate=_rate(evidence_submitters, activated_count),
            next_action='`submit_tribulation_evidence(username="you", evidence_key="lineage_users", amount=1, source_url="https://github.com/owner/repo/issues/1")`',
            denominator=activated_count,
        ),
    ]
    if activation_events is not None:
        stages.append(
            GrowthStage(
                label="公开分享证明",
                value=f"{len(public_share_actors)}/{activated_count}",
                rate=_rate(len(public_share_actors), activated_count),
                next_action='`leaderboard(type="share")`',
                denominator=activated_count,
            )
        )
    return stages


def _select_bottleneck(stages: Sequence[GrowthStage]) -> GrowthStage:
    repeat_candidates = [
        stage
        for stage in stages
        if stage.label not in {"修仙者档案", "首件法宝激活", "公开法宝供给"}
        and stage.denominator > 0
    ]
    if repeat_candidates:
        return min(repeat_candidates, key=lambda stage: stage.rate)

    for stage in stages:
        if stage.label == "首件法宝激活":
            return stage

    return stages[0]


def _count_active_sects(sects: Sequence[SectProfile]) -> int:
    return sum(1 for sect in sects if sect.member_count > 0)


def build_growth_issue_url(
    bottleneck_label: str,
    campaign_hook: str,
    real_data_context: str,
    target_contributors: int | None = None,
    repo_owner: str | None = None,
    repo_name: str | None = None,
) -> str:
    """Build a public GitHub new-issue URL for the growth flywheel Issue Form."""
    owner = repo_owner or config.GITHUB_REPO_OWNER
    name = repo_name or config.GITHUB_REPO_NAME
    query_params = {
        "template": GROWTH_ISSUE_TEMPLATE,
        "title": f"[TianGong Growth]: {bottleneck_label}",
        "growth_bottleneck": bottleneck_label,
        "campaign_hook": campaign_hook,
        "real_data_context": real_data_context,
    }
    if target_contributors is not None:
        target = _safe_positive_int(target_contributors)
        query_params["target_contributors"] = str(target)
    query = urlencode(query_params)
    return f"https://github.com/{owner}/{name}/issues/new?{query}"


def build_growth_issue_proof_url_placeholder(
    repo_owner: str | None = None,
    repo_name: str | None = None,
) -> str:
    """Return the reviewable URL shape users should paste after creating a Growth Issue."""
    owner = repo_owner or config.GITHUB_REPO_OWNER
    name = repo_name or config.GITHUB_REPO_NAME
    return f"https://github.com/{owner}/{name}/issues/<opened-growth-issue-number>"


def _clean_campaign_text(value: str, fallback: str, limit: int = 120) -> str:
    text = " ".join(str(value or "").split())
    return text[:limit] or fallback


def _safe_positive_int(value: int, fallback: int = 10) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return fallback
    return number if number > 0 else fallback


def format_growth_campaign(
    profiles: Sequence[CultivatorProfile],
    artifacts: Sequence[AgentSpec],
    sects: Sequence[SectProfile],
    activation_events: Sequence[ActivationEvent] | None = None,
    *,
    campaign_name: str = "",
    target_contributors: int = 10,
) -> str:
    """Format a 72-hour public launch campaign from the real growth flywheel snapshot."""
    campaign = _clean_campaign_text(campaign_name, "TianGong 72 小时爆发战役")
    target = _safe_positive_int(target_contributors)
    stages = _build_growth_stages(profiles, artifacts, activation_events=activation_events)
    bottleneck = _select_bottleneck(stages)
    active_sects = _count_active_sects(sects)
    first_artifact = artifacts[0].name if artifacts else "first-growth-artifact"
    campaign_hook = f"{campaign}: 72 小时补齐 {bottleneck.label}"
    real_data_context = (
        f"当前真实快照: {len(profiles)} 位修仙者 / {len(artifacts)} 件法宝 / "
        f"{active_sects} 个活跃宗门 / {bottleneck.label} {_format_percent(bottleneck.rate)}"
    )
    growth_issue_url = build_growth_issue_url(
        bottleneck_label=bottleneck.label,
        campaign_hook=campaign_hook,
        real_data_context=real_data_context,
        target_contributors=target,
    )
    growth_issue_proof_url = build_growth_issue_proof_url_placeholder()
    share_issue_url = build_share_proof_issue_url(
        contribution="forge",
        artifact_name=first_artifact,
        campaign_hook=f"{campaign}: 提交一条公开贡献分享证明",
    )

    lines = [
        "# TianGong 爆发战役",
        "",
        f"> 战役名称: {campaign}",
        f"> 72 小时公开战役；目标贡献者: {target}。",
        (
            f"> 当前真实快照: {len(profiles)} 位修仙者、{len(artifacts)} 件公开法宝、"
            f"{active_sects}/{len(sects)} 个活跃宗门。"
        ),
        "> 不伪造下载量、留存、转发数、转介绍或灵力奖励；只把真实瓶颈转成公开行动。",
        "",
        "## 战役瓶颈",
        "",
        f"- 最薄弱环节: {bottleneck.label}",
        f"- 真实转化率: {_format_percent(bottleneck.rate)}",
        f"- 第一手行动: {bottleneck.next_action}",
        "",
        "## 72 小时公开行动",
        "",
        "| 时间 | 目标 | 公开动作 |",
        "|---|---|---|",
        (
            "| 第 0-6 小时 | 点燃第一炉 | "
            "`start_cultivation(username=\"your_github_username\")` -> "
            f"`forge_agent(name=\"{first_artifact}\", description=\"TianGong 72h launch artifact\")` |"
        ),
        (
            "| 第 6-24 小时 | 把外部注意力导回 MCP | "
            f"`record_growth_referral(route=\"growth\", source_url=\"{growth_issue_proof_url}\", actor=\"your_github_username\")` |"
        ),
        (
            "| 第 24-48 小时 | 公开证明贡献已传播 | "
            "`record_share_attribution(contribution=\"forge\", "
            "share_url=\"https://github.com/owner/repo/issues/2\", "
            f"artifact_name=\"{first_artifact}\", source_url=\"{growth_issue_proof_url}\", actor=\"your_github_username\")` |"
        ),
        (
            "| 第 48-72 小时 | 排名、复盘、追赶 | "
            "`leaderboard(type=\"share\")` -> `share_attribution_report()` -> `growth_flywheel()` |"
        ),
        "",
        "## 公开回流入口",
        "",
        f"- Growth Issue: {growth_issue_url}",
        f"- Created Growth Issue proof URL: {growth_issue_proof_url}",
        "- Open the Growth Issue first, then record the created Issue URL as proof.",
        f"- Share Proof Issue: {share_issue_url}",
        "- 复查战役卡: `growth_campaign()`",
        "- 复查飞轮: `growth_flywheel()`",
        "- 复查激活: `activation_funnel()`",
        "- 验证公开牵引力: `public_growth_report()`",
        "- 生成首个公开证明包: `public_proof_pack()`",
        "- 查看分享证明天榜: `leaderboard(type=\"share\")`",
        "",
        "## 复制公开招募帖",
        "",
        "```text",
        (
            f"{campaign}: TianGong 正在发起 72 小时公开修炼战役。"
            f"当前真实瓶颈是 {bottleneck.label}，目标招募 {target} 位贡献者完成开炉、回流、分享证明。"
        ),
        "不伪造下载量、留存、转发数、转介绍或灵力奖励。",
        "加入修炼: pip install tiangong-mcp",
        "第一步: start_cultivation(username=\"your_github_username\")",
        f"增长 Issue: {growth_issue_url}",
        f"分享证明 Issue: {share_issue_url}",
        "复查战役: growth_campaign()",
        "验证公开证明: public_growth_report()",
        "首个公开证明包: public_proof_pack()",
        "```",
        "",
        "## 复制 Discussion/PR 战役帖",
        "",
        "```markdown",
        f"## {campaign}",
        "",
        f"- 72 小时目标: {target} 位真实贡献者",
        f"- 当前真实快照: {len(profiles)} 位修仙者 / {len(artifacts)} 件法宝 / {active_sects} 个活跃宗门",
        f"- 当前瓶颈: {bottleneck.label} ({_format_percent(bottleneck.rate)})",
        "- 数据原则: 不伪造下载量、留存、转发数、转介绍或灵力奖励",
        "- 第一手行动: `start_cultivation(username=\"your_github_username\")`",
        f"- Growth Issue: {growth_issue_url}",
        f"- Created Growth Issue proof URL for ledger commands: `{growth_issue_proof_url}`",
        f"- Share Proof Issue: {share_issue_url}",
        "- 复查命令: `growth_campaign()` / `growth_flywheel()` / `leaderboard(type=\"share\")`",
        "- 公开证明命令: `public_growth_report()`",
        "```",
    ]

    if not profiles:
        lines.extend(
            [
                "",
                "## 冷启动第一炉",
                "",
                '- 首件法宝: `forge_agent(name="first-growth-artifact", description="A TianGong artifact opening the first 72h launch campaign")`',
                '- 首条悬赏: `quest(action="post", artifact_name="first-growth-bounty", description="招募第一位修仙者完成 TianGong 72 小时爆发战役")`',
            ]
        )

    return "\n".join(lines)


def format_growth_flywheel(
    profiles: Sequence[CultivatorProfile],
    artifacts: Sequence[AgentSpec],
    sects: Sequence[SectProfile],
    activation_events: Sequence[ActivationEvent] | None = None,
) -> str:
    """Format the current TianGong growth flywheel without fabricated history."""
    stages = _build_growth_stages(profiles, artifacts, activation_events=activation_events)
    bottleneck = _select_bottleneck(stages)
    active_sects = _count_active_sects(sects)
    campaign_hook = f"补齐 TianGong 增长飞轮的最薄弱环节: {bottleneck.label}"
    real_data_context = (
        f"当前真实快照: {len(profiles)} 位修仙者 / {len(artifacts)} 件法宝 / "
        f"{active_sects} 个活跃宗门 / {bottleneck.label} {_format_percent(bottleneck.rate)}"
    )
    growth_issue_url = build_growth_issue_url(
        bottleneck_label=bottleneck.label,
        campaign_hook=campaign_hook,
        real_data_context=real_data_context,
    )

    lines = [
        "# TianGong 增长飞轮",
        "",
        (
            f"> 当前真实快照: {len(profiles)} 位修仙者、{len(artifacts)} 件公开法宝、"
            f"{active_sects}/{len(sects)} 个活跃宗门。"
        ),
        "> 不伪造历史事件、下载量、留存曲线或外部传播数据；这里只评估当前 registry 已经能证明的闭环。",
        "",
        "## 飞轮转化表",
        "",
        "| 环节 | 真实数据 | 转化率 | 下一动作 |",
        "|---|---:|---:|---|",
    ]

    for stage in stages:
        lines.append(f"| {stage.label} | {stage.value} | {_format_percent(stage.rate)} | {stage.next_action} |")

    lines.extend(
        [
            "",
            "## 当前瓶颈",
            "",
            f"- 最薄弱环节: {bottleneck.label}",
            f"- 真实转化率: {_format_percent(bottleneck.rate)}",
            f"- 第一手行动: {bottleneck.next_action}",
            "",
            "## 闭环判断",
            "",
            "- 已形成可执行闭环: 开炉 -> 发布/发现 -> 鉴定 -> 淬炼 -> 悬赏 -> 宗门/赛季 -> 渡劫证据 -> 再传播。",
            "- 还未形成自增长闭环: 缺少对每一环的统一体检入口时，用户不知道下一步该补哪一环。",
            "- 现在的增长飞轮入口会把瓶颈直接转成可复制命令，避免只靠叙事热度消耗用户注意力。",
            "",
            "## 可复制命令",
            "",
            "- 复查真实激活漏斗: `activation_funnel()`",
            "- 复查飞轮: `growth_flywheel()`",
            "- 发起 72 小时爆发战役: `growth_campaign()`",
            "- 验证公开牵引力: `public_growth_report()`",
            "- 生成首个公开证明包: `public_proof_pack()`",
            "- 继续淬炼: `refine_agent(agent_id=\"artifact-id\", changes=\"...\")`",
            "- 发布悬赏: `quest(action=\"post\", artifact_name=\"growth-bounty\", description=\"补齐 TianGong 增长飞轮的下一环\")`",
            "- 查看赛季追赶: `leaderboard(type=\"season\")`",
            "- 查看宗门战: `leaderboard(type=\"sect\")`",
            "- 查看公开分享证明: `leaderboard(type=\"share\")`",
            "- 复查公开分享归因: `share_attribution_report()`",
            f"- 打开外部招募 Issue: {growth_issue_url}",
            "",
            "## 外部回流入口",
            "",
            f"- GitHub Growth Issue: {growth_issue_url}",
            f"- Issue Form 模板: `{GROWTH_ISSUE_TEMPLATE}`",
            "- 作用: 把社交传播导回 `tiangong:growth`，由 IssueOps 安全回帖真实命令卡。",
            "",
            "## 复制增长战报",
            "",
            "```text",
            (
                f"TianGong 当前增长飞轮快照: {len(profiles)} 位修仙者、{len(artifacts)} 件法宝、"
                f"最薄弱环节是{bottleneck.label}。不伪造历史事件，只用真实 registry 快照补齐下一步。"
            ),
            "加入修炼: pip install tiangong-mcp",
            "复查激活: activation_funnel()",
            "复查飞轮: growth_flywheel()",
            "发起战役: growth_campaign()",
            "验证公开证明: public_growth_report()",
            "首个公开证明包: public_proof_pack()",
            f"打开增长复盘: {growth_issue_url}",
            "```",
            "",
            "## 复制 Discussion/PR 飞轮复盘",
            "",
            "```markdown",
            "## TianGong 增长飞轮复盘",
            "",
            f"- 当前真实快照: {len(profiles)} 位修仙者 / {len(artifacts)} 件法宝 / {active_sects} 个活跃宗门",
            "- 数据原则: 不伪造历史事件、下载量、留存曲线或外部传播数据",
            "- 分享证明原则: 不伪造下载量、留存、转发数、转介绍或灵力奖励",
            f"- 最薄弱环节: {bottleneck.label} ({_format_percent(bottleneck.rate)})",
            f"- 第一手行动: {bottleneck.next_action}",
            "- 激活漏斗入口: `activation_funnel()`",
            "- 复查入口: `growth_flywheel()`",
            "- 爆发战役入口: `growth_campaign()`",
            "- 公开证明入口: `public_growth_report()`",
            "- 首个公开证明包: `public_proof_pack()`",
            f"- 外部回流 Issue: {growth_issue_url}",
            "- 安装: `pip install tiangong-mcp`",
            "```",
        ]
    )

    if not profiles:
        lines.extend(
            [
                "",
                "## 冷启动第一手行动",
                "",
                '- 第一手行动: `forge_agent(name="first-growth-artifact", description="A TianGong artifact opening the first growth flywheel")`',
                '- 同步招募悬赏: `quest(action="post", artifact_name="first-growth-bounty", description="招募第一位修仙者补齐 TianGong 增长飞轮")`',
            ]
        )

    return "\n".join(lines)
