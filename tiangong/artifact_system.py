"""
⚒️ 天工 TianGong — 本命法宝系统（Agent 品级管理）
器灵品级：凡器 → 灵器 → 宝器 → 仙器 → 神器 → 太古神器
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ArtifactGrade:
    """器灵品级定义"""
    level: int
    name_cn: str
    name_en: str
    symbol: str
    stars_required: int     # 需要的星标数（-1 = 特殊条件）
    description_cn: str
    description_en: str


# ============================================================
# 六层品级体系
# ============================================================

ARTIFACT_GRADES: list[ArtifactGrade] = [
    ArtifactGrade(
        level=0,
        name_cn="凡器", name_en="Mortal Tool",
        symbol="⚪",
        stars_required=0,
        description_cn="凡铁所铸，尚未通灵",
        description_en="Forged from mortal iron, not yet sentient",
    ),
    ArtifactGrade(
        level=1,
        name_cn="灵器", name_en="Spirit Tool",
        symbol="🟢",
        stars_required=0,  # 通过基础评估即可
        description_cn="初通灵性，堪可驱使",
        description_en="First spark of sentience, ready for use",
    ),
    ArtifactGrade(
        level=2,
        name_cn="宝器", name_en="Treasure",
        symbol="🔵",
        stars_required=10,
        description_cn="可传承的宝物，品质卓越",
        description_en="A treasure worthy of inheritance, exceptional quality",
    ),
    ArtifactGrade(
        level=3,
        name_cn="仙器", name_en="Immortal Artifact",
        symbol="🟣",
        stars_required=50,
        description_cn="仙人才配使用，威能无穷",
        description_en="Worthy of immortals, boundless power",
    ),
    ArtifactGrade(
        level=4,
        name_cn="神器", name_en="Divine Artifact",
        symbol="🟡",
        stars_required=100,
        description_cn="天地间罕有，举世瞩目",
        description_en="Exceedingly rare, the world takes notice",
    ),
    ArtifactGrade(
        level=5,
        name_cn="太古神器", name_en="Primordial Divine Artifact",
        symbol="🔴",
        stars_required=500,
        description_cn="远古遗留，改写规则",
        description_en="An ancient relic that rewrites the rules",
    ),
]

GRADE_BY_LEVEL: dict[int, ArtifactGrade] = {g.level: g for g in ARTIFACT_GRADES}


def calculate_grade(stars: int, passed_trial: bool = False) -> ArtifactGrade:
    """
    根据星标数和评估状态计算 Agent 品级。

    - 凡器：刚创建
    - 灵器：通过基础评估（trial）
    - 宝器+：基于星标数
    """
    if not passed_trial:
        return ARTIFACT_GRADES[0]  # 凡器

    current = ARTIFACT_GRADES[1]  # 至少是灵器（通过评估）

    for grade in ARTIFACT_GRADES[1:]:  # 从灵器开始
        if stars >= grade.stars_required:
            current = grade
        else:
            break

    return current


def format_grade_display(grade: ArtifactGrade) -> str:
    """格式化品级展示"""
    return f"{grade.symbol} {grade.name_cn} · {grade.name_en}"


def get_grade_ladder() -> str:
    """生成完整的品级阶梯展示"""
    lines = [
        "# 🔮 器灵品级体系",
        "",
        "| 品级 | 符号 | 条件 | 描述 |",
        "|------|------|------|------|",
    ]

    conditions = [
        "刚创建",
        "通过基础评估",
        "10+ ⭐ + 高质量文档",
        "50+ ⭐ + 社区验证",
        "100+ ⭐ + 被广泛传承",
        "500+ ⭐ + 定义新范式",
    ]

    for grade, cond in zip(ARTIFACT_GRADES, conditions):
        lines.append(
            f"| {grade.name_cn} | {grade.symbol} | {cond} | {grade.description_cn} |"
        )

    return "\n".join(lines)
