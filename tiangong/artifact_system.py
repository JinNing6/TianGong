"""
⚒️ 天工 TianGong — 法宝品阶系统（Phase 2）
六维灵根评估 + 灵力值驱动品阶 + 品阶晋升/降级
"""

from __future__ import annotations

import math
from dataclasses import dataclass


# ============================================================
# 品阶定义
# ============================================================

@dataclass(frozen=True)
class ArtifactGrade:
    """法宝品阶"""
    level: int        # 品阶等级（0-5）
    name_cn: str      # 中文名
    name_en: str      # 英文名
    symbol: str       # 符号
    color: str        # 颜色
    spirit_threshold: int   # 灵力值门槛
    min_reviewers: int      # 最少评价人数门槛
    description_cn: str     # 中文描述


GRADES: list[ArtifactGrade] = [
    ArtifactGrade(
        level=0,
        name_cn="凡器", name_en="Mortal Tool",
        symbol="⚪", color="white",
        spirit_threshold=0, min_reviewers=0,
        description_cn="未经评价的普通法宝",
    ),
    ArtifactGrade(
        level=1,
        name_cn="灵器", name_en="Spirit Tool",
        symbol="🟢", color="green",
        spirit_threshold=10, min_reviewers=3,
        description_cn="初通灵性，经过社区验证",
    ),
    ArtifactGrade(
        level=2,
        name_cn="宝器", name_en="Treasure Tool",
        symbol="🔵", color="blue",
        spirit_threshold=50, min_reviewers=10,
        description_cn="品质上乘，社区广泛认可",
    ),
    ArtifactGrade(
        level=3,
        name_cn="仙器", name_en="Immortal Tool",
        symbol="🟣", color="purple",
        spirit_threshold=200, min_reviewers=30,
        description_cn="接近完美，被广泛引用",
    ),
    ArtifactGrade(
        level=4,
        name_cn="神器", name_en="Divine Tool",
        symbol="🟡", color="gold",
        spirit_threshold=800, min_reviewers=100,
        description_cn="定义行业标准的传奇法宝",
    ),
    ArtifactGrade(
        level=5,
        name_cn="太古神器", name_en="Primordial Artifact",
        symbol="🔴", color="red",
        spirit_threshold=3000, min_reviewers=500,
        description_cn="改变世界的太古级存在",
    ),
]

GRADE_BY_LEVEL: dict[int, ArtifactGrade] = {g.level: g for g in GRADES}
GRADE_BY_NAME: dict[str, ArtifactGrade] = {g.name_cn: g for g in GRADES}


# ============================================================
# 六维灵根评估
# ============================================================

# 六个评估维度
DIMENSIONS = [
    {"key": "inscription",  "name_cn": "📝 铭文", "name_en": "Inscription",
     "description": "描述清晰度——README、注释、使用说明是否让人一看就懂"},
    {"key": "formation",    "name_cn": "🏗️ 阵法", "name_en": "Formation",
     "description": "架构设计——模块划分、文件组织、代码结构是否合理"},
    {"key": "technique",    "name_cn": "⚙️ 法诀", "name_en": "Technique",
     "description": "工程质量——语法规范、错误处理、边界情况覆盖"},
    {"key": "lineage",      "name_cn": "📖 道统", "name_en": "Lineage",
     "description": "文档传承——是否有完整的开发者文档、API 参考"},
    {"key": "resilience",   "name_cn": "🛡️ 护体", "name_en": "Resilience",
     "description": "稳定韧性——有无测试、容错机制、异常恢复"},
    {"key": "enlightenment","name_cn": "✨ 悟道", "name_en": "Enlightenment",
     "description": "创新灵性——是否有独到的设计或创新的解决方案"},
]

DIMENSION_KEYS = [d["key"] for d in DIMENSIONS]


@dataclass
class SpiritReview:
    """一次灵力灌注（评价）"""
    reviewer: str                    # 评价者用户名
    reviewer_realm_level: int        # 评价者境界等级
    reviewer_weight: float           # 评价者权重
    scores: dict[str, int]           # 六维评分（每维 1-10 分）
    timestamp: float = 0.0          # 评价时间
    comment: str = ""                # 评论

    @property
    def average_score(self) -> float:
        """六维均分"""
        if not self.scores:
            return 0.0
        values = [v for v in self.scores.values() if isinstance(v, (int, float))]
        return sum(values) / len(values) if values else 0.0

    @property
    def spirit_value(self) -> float:
        """
        单次灵力值 = 六维均分 × 评价者境界权重

        例如: 一个化神期修仙者的满分(10)评价 = 10 × 5.0 = 50 灵力
             一个炼气期新手的满分(10)评价 = 10 × 1.0 = 10 灵力
        """
        return self.average_score * self.reviewer_weight


def calculate_total_spirit(reviews: list[SpiritReview]) -> float:
    """计算法宝总灵力值"""
    return sum(r.spirit_value for r in reviews)


def calculate_grade(
    total_spirit: float,
    reviewer_count: int,
    passed_trial: bool = False,
) -> ArtifactGrade:
    """
    根据灵力值和评价人数计算品阶。

    如果未通过试剑（passed_trial=False），最高为凡器。
    Phase 1 兼容：如果传入旧参数也能用。
    """
    current = GRADES[0]  # 默认凡器

    for grade in GRADES:
        if total_spirit >= grade.spirit_threshold and reviewer_count >= grade.min_reviewers:
            current = grade
        else:
            break

    return current


def check_grade_change(
    old_spirit: float, new_spirit: float,
    old_reviewers: int, new_reviewers: int,
) -> tuple[bool, ArtifactGrade, ArtifactGrade]:
    """
    检查品阶是否变化。

    Returns:
        (是否变化, 旧品阶, 新品阶)
    """
    old_grade = calculate_grade(old_spirit, old_reviewers)
    new_grade = calculate_grade(new_spirit, new_reviewers)
    return old_grade.level != new_grade.level, old_grade, new_grade


# ============================================================
# 格式化展示
# ============================================================

def format_grade_display(grade: ArtifactGrade) -> str:
    """格式化品阶展示"""
    return f"{grade.symbol} {grade.name_cn}"


def format_review_card(review: SpiritReview) -> str:
    """格式化单次评价卡片"""
    lines = [
        f"### 💫 灵力灌注 by @{review.reviewer}",
        f"- 境界权重: ×{review.reviewer_weight}",
        f"- 灵力值: {review.spirit_value:.1f}",
        "",
        "| 维度 | 评分 |",
        "|------|------|",
    ]

    for dim in DIMENSIONS:
        key = dim["key"]
        score = review.scores.get(key, 0)
        bar = "█" * score + "░" * (10 - score)
        lines.append(f"| {dim['name_cn']} | {bar} {score}/10 |")

    if review.comment:
        lines.extend(["", f"> {review.comment}"])

    return "\n".join(lines)


def format_artifact_spirit_info(
    total_spirit: float,
    reviewer_count: int,
    grade: ArtifactGrade,
    dimension_averages: dict[str, float] | None = None,
) -> str:
    """格式化法宝灵力信息"""
    lines = [
        f"## {format_grade_display(grade)}",
        f"- 💫 总灵力: {total_spirit:.0f}",
        f"- 👥 评价人数: {reviewer_count}",
    ]

    # 六维雷达图（文本版）
    if dimension_averages:
        lines.extend(["", "### 六维灵根评估"])
        for dim in DIMENSIONS:
            key = dim["key"]
            avg = dimension_averages.get(key, 0)
            bar_len = round(avg)
            bar = "█" * bar_len + "░" * (10 - bar_len)
            lines.append(f"- {dim['name_cn']}: {bar} {avg:.1f}/10")

    # 下一品阶进度
    next_grade = get_next_grade(grade)
    if next_grade:
        spirit_needed = max(0, next_grade.spirit_threshold - total_spirit)
        reviewers_needed = max(0, next_grade.min_reviewers - reviewer_count)
        lines.extend([
            "",
            f"### 📈 下一品阶: {format_grade_display(next_grade)}",
            f"- 还需灵力: {spirit_needed:.0f}" if spirit_needed > 0 else "- ✅ 灵力已达标",
            f"- 还需评价: {reviewers_needed}" if reviewers_needed > 0 else "- ✅ 评价人数已达标",
        ])

    return "\n".join(lines)


def get_next_grade(grade: ArtifactGrade) -> ArtifactGrade | None:
    """获取下一个品阶"""
    if grade.level >= len(GRADES) - 1:
        return None
    return GRADES[grade.level + 1]


def get_grade_ladder() -> str:
    """生成完整的品阶阶梯展示"""
    lines = [
        "# 🔮 法宝品阶阶梯",
        "",
        "| 品阶 | 符号 | 灵力门槛 | 评价人数 | 说明 |",
        "|------|------|---------|---------|------|",
    ]

    for g in GRADES:
        lines.append(
            f"| {g.name_cn} | {g.symbol} | {g.spirit_threshold} | {g.min_reviewers} | {g.description_cn} |"
        )

    lines.extend([
        "",
        "### 灵力值计算公式",
        "```",
        "单次灵力 = 六维均分 × 评价者境界权重",
        "总灵力 = Σ(所有评价的单次灵力)",
        "```",
        "",
        "| 评价者境界 | 权重 | 满分(10分)一次灵力 |",
        "|-----------|------|-------------------|",
        "| 炼气期 | ×1.0 | 10 |",
        "| 结丹期 | ×2.0 | 20 |",
        "| 化神期 | ×5.0 | 50 |",
        "| 问鼎期 | ×12.0 | 120 |",
        "| 鲁班 | ×80.0 | 800 |",
    ])

    return "\n".join(lines)
