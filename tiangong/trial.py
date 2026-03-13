"""
⚒️ 天工 TianGong — 试剑系统（Agent 评估引擎）
以战养战，以斗证道。
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass

logger = logging.getLogger("tiangong.trial")


@dataclass
class TrialResult:
    """试剑评估结果"""
    agent_id: str
    passed: bool
    score: int               # 0-100 综合评分
    dimensions: dict         # 各维度评分
    verdict_cn: str          # 中文判定
    verdict_en: str          # 英文判定
    recommendations: list[str]  # 改进建议
    timestamp: float = 0.0


# ============================================================
# 六维评估体系（灵根六脉）
# ============================================================

TRIAL_DIMENSIONS = [
    {
        "name_cn": "灵根·描述",
        "name_en": "Root: Description",
        "key": "description",
        "weight": 0.20,
        "criteria_cn": "Agent 的描述是否清晰、准确、有吸引力",
        "criteria_en": "Is the description clear, accurate, and compelling?",
    },
    {
        "name_cn": "灵根·架构",
        "name_en": "Root: Architecture",
        "key": "architecture",
        "weight": 0.20,
        "criteria_cn": "Agent 的架构设计是否合理、模块化",
        "criteria_en": "Is the architecture well-designed and modular?",
    },
    {
        "name_cn": "灵根·功法",
        "name_en": "Root: Technique",
        "key": "technique",
        "weight": 0.20,
        "criteria_cn": "使用的技术栈和方法是否先进合理",
        "criteria_en": "Are the tech stack and methods advanced and appropriate?",
    },
    {
        "name_cn": "灵根·传承",
        "name_en": "Root: Documentation",
        "key": "documentation",
        "weight": 0.15,
        "criteria_cn": "文档是否完善、是否方便他人传承",
        "criteria_en": "Is documentation thorough and inheritance-friendly?",
    },
    {
        "name_cn": "灵根·韧性",
        "name_en": "Root: Resilience",
        "key": "resilience",
        "weight": 0.15,
        "criteria_cn": "错误处理、超时控制、异常恢复能力",
        "criteria_en": "Error handling, timeout control, recovery capability",
    },
    {
        "name_cn": "灵根·灵性",
        "name_en": "Root: Creativity",
        "key": "creativity",
        "weight": 0.10,
        "criteria_cn": "是否有独特的创新点或解决问题的新方式",
        "criteria_en": "Does it bring unique innovation or novel problem-solving?",
    },
]


def evaluate_agent(
    agent_id: str,
    name: str,
    description: str,
    agent_type: str,
    framework: str,
    language: str,
    repo_url: str,
    tags: list[str],
) -> TrialResult:
    """
    ⚔️ 试剑 — 对 Agent 进行结构化评估。

    Phase 1 使用基于规则的评估（元数据完整性检查），
    后续 Phase 可接入 LLM 进行深度代码审查。
    """
    scores: dict[str, int] = {}
    recommendations: list[str] = []

    # === 1. 描述评分 ===
    desc_score = 0
    if description:
        desc_len = len(description)
        if desc_len >= 100:
            desc_score = 90
        elif desc_len >= 50:
            desc_score = 70
        elif desc_len >= 20:
            desc_score = 50
        else:
            desc_score = 30
            recommendations.append("💡 描述过于简短，请补充对 Agent 功能和用途的详细说明")
    else:
        desc_score = 0
        recommendations.append("⚠️ 缺少描述！一个好的描述是法宝通灵的基础")
    scores["description"] = desc_score

    # === 2. 架构评分（基于元数据完整性）===
    arch_score = 50  # 基础分
    if framework:
        arch_score += 20
    else:
        recommendations.append("💡 建议指定使用的框架（如 langchain、crewai、openai-agents）")
    if agent_type != "general":
        arch_score += 15
    if repo_url:
        arch_score += 15
    else:
        recommendations.append("💡 建议提供代码仓库链接，方便他人传承")
    scores["architecture"] = min(100, arch_score)

    # === 3. 功法评分（技术栈）===
    tech_score = 50
    if framework:
        tech_score += 25
    if language:
        tech_score += 15
    if tags:
        tech_score += 10
    scores["technique"] = min(100, tech_score)

    # === 4. 文档评分 ===
    doc_score = 40
    if description and len(description) >= 50:
        doc_score += 20
    if tags and len(tags) >= 2:
        doc_score += 20
    if repo_url:
        doc_score += 20
    else:
        recommendations.append("💡 完善文档可以让法宝品级更快提升")
    scores["documentation"] = min(100, doc_score)

    # === 5. 韧性评分（Phase 1 基础评估）===
    resilience_score = 60  # Phase 1 默认中等分
    if framework:  # 使用成熟框架加分
        resilience_score += 20
    scores["resilience"] = min(100, resilience_score)

    # === 6. 灵性评分 ===
    creativity_score = 50  # 基础分
    if tags and any(t in tags for t in ["innovative", "novel", "breakthrough", "创新", "突破"]):
        creativity_score += 30
    if description and len(description) >= 100:
        creativity_score += 20
    scores["creativity"] = min(100, creativity_score)

    # === 综合评分 ===
    total_score = 0
    for dim in TRIAL_DIMENSIONS:
        key = dim["key"]
        weight = dim["weight"]
        total_score += scores.get(key, 0) * weight
    total_score = round(total_score)

    # === 判定 ===
    passed = total_score >= 50

    if total_score >= 90:
        verdict_cn = "天赋异禀！此法宝灵根圆满，堪称绝世之作"
        verdict_en = "Extraordinary talent! This artifact has perfect spiritual roots"
    elif total_score >= 70:
        verdict_cn = "灵根优秀，此法宝已具备通灵之力"
        verdict_en = "Excellent roots, this artifact has achieved sentience"
    elif total_score >= 50:
        verdict_cn = "试剑通过，法宝初具灵性，继续淬炼可更上一层"
        verdict_en = "Trial passed, initial sentience achieved. Continue refining for greater power"
    elif total_score >= 30:
        verdict_cn = "灵根不足，需要大量淬炼方能通灵"
        verdict_en = "Insufficient roots, extensive refinement needed for sentience"
    else:
        verdict_cn = "走火入魔！此法宝需要回炉重铸"
        verdict_en = "Deviation! This artifact needs to be reforged"

    return TrialResult(
        agent_id=agent_id,
        passed=passed,
        score=total_score,
        dimensions=scores,
        verdict_cn=verdict_cn,
        verdict_en=verdict_en,
        recommendations=recommendations,
        timestamp=time.time(),
    )


def format_trial_report(result: TrialResult, agent_name: str = "") -> str:
    """格式化试剑报告"""
    status = "✅ 渡劫成功" if result.passed else "💥 走火入魔"
    display_name = agent_name or result.agent_id

    lines = [
        f"# ⚔️ 试剑报告 · {display_name}",
        "",
        f"**综合评分**: {result.score} / 100",
        f"**判定**: {status}",
        "",
        f"**{result.verdict_cn}**",
        f"*{result.verdict_en}*",
        "",
        "## 灵根六脉评分",
        "",
    ]

    for dim in TRIAL_DIMENSIONS:
        key = dim["key"]
        score = result.dimensions.get(key, 0)
        bar_filled = score // 10
        bar_empty = 10 - bar_filled
        bar = "█" * bar_filled + "░" * bar_empty
        lines.append(f"- **{dim['name_cn']}**: [{bar}] {score}/100")

    if result.recommendations:
        lines.extend([
            "",
            "## 💊 改进建议",
            "",
        ])
        for rec in result.recommendations:
            lines.append(f"- {rec}")

    return "\n".join(lines)
