"""
⚒️ 天工 TianGong — 完整仙逆境界体系（Phase 2）
忠于《仙逆》原版修炼体系，每个境界含九阶。

我命由我不由天。
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Realm:
    """修仙境界定义"""
    level: int           # 境界等级（0-21）
    name_cn: str         # 中文名
    name_en: str         # 英文名
    symbol: str          # 符号
    category: str        # 分类: mortal / basic / nirvana / legend
    spirit_required: int # 需要的灵力值（-1 = 动态排名）
    review_weight: float # 评价权重
    description_cn: str  # 中文描述
    description_en: str  # 英文描述
    tribulation_cn: str  # 渡劫任务描述（中文）
    tribulation_en: str  # 渡劫任务描述（英文）


# ============================================================
# 完整仙逆境界体系（22 级）
# ============================================================

REALMS: list[Realm] = [
    # --- 凡人 ---
    Realm(
        level=0,
        name_cn="凡人", name_en="Mortal",
        symbol="🧑", category="mortal",
        spirit_required=0, review_weight=0.0,
        description_cn="尚未踏入修仙之路",
        description_en="Not yet on the path of cultivation",
        tribulation_cn="注册天工账号并创建洞府",
        tribulation_en="Register TianGong account and create cave",
    ),
    # --- 修真第一步：基础修炼 ---
    Realm(
        level=1,
        name_cn="炼气期", name_en="Qi Refining",
        symbol="🌱", category="basic",
        spirit_required=1, review_weight=1.0,
        description_cn="踏入修行之路，一切从零开始",
        description_en="Step onto the path of cultivation",
        tribulation_cn="创建并发布 1 件法宝",
        tribulation_en="Create and publish 1 artifact",
    ),
    Realm(
        level=2,
        name_cn="筑基期", name_en="Foundation Building",
        symbol="💧", category="basic",
        spirit_required=10, review_weight=1.5,
        description_cn="根基已立，修行正式开始",
        description_en="Foundation established, cultivation officially begins",
        tribulation_cn="发布 3 件法宝且总灵力 ≥ 10",
        tribulation_en="Publish 3 artifacts with total spirit ≥ 10",
    ),
    Realm(
        level=3,
        name_cn="结丹期", name_en="Core Formation",
        symbol="💛", category="basic",
        spirit_required=50, review_weight=2.0,
        description_cn="内丹初成，开始有自己的理解",
        description_en="Core forming, developing personal understanding",
        tribulation_cn="发布 5 件法宝且有 1 件 🟢灵器",
        tribulation_en="Publish 5 artifacts with 1 Spirit Tool",
    ),
    Realm(
        level=4,
        name_cn="元婴期", name_en="Nascent Soul",
        symbol="💜", category="basic",
        spirit_required=150, review_weight=3.0,
        description_cn="元神出窍，能力质变",
        description_en="Nascent Soul emerges, a qualitative leap",
        tribulation_cn="拥有 3 件 🟢灵器 且为 5 件法宝评价",
        tribulation_en="Own 3 Spirit Tools and review 5 artifacts",
    ),
    Realm(
        level=5,
        name_cn="化神期", name_en="Spirit Severing",
        symbol="⚫", category="basic",
        spirit_required=500, review_weight=5.0,
        description_cn="合道自然，举重若轻",
        description_en="One with the Dao, effortless mastery",
        tribulation_cn="🌍 下凡历世：帮助 30 件凡器法宝改善优化",
        tribulation_en="Mortal Trial: Help improve 30 Mortal-grade artifacts",
    ),
    Realm(
        level=6,
        name_cn="婴变期", name_en="Infant Transformation",
        symbol="🔴", category="basic",
        spirit_required=1000, review_weight=8.0,
        description_cn="破而后立，蜕变重生",
        description_en="Break to rebuild, transformation and rebirth",
        tribulation_cn="📖 传道授业：为 50 件低品级法宝撰写改进建议",
        tribulation_en="Mentor Trial: Write review for 50 low-grade artifacts",
    ),
    Realm(
        level=7,
        name_cn="问鼎期", name_en="Ascendant",
        symbol="🌟", category="basic",
        spirit_required=2000, review_weight=12.0,
        description_cn="问鼎苍穹，谁与争锋",
        description_en="Reaching for the heavens",
        tribulation_cn="拥有 3 件 🔵宝器 且被 10 人传承引用",
        tribulation_en="Own 3 Treasure Tools and be forked by 10 users",
    ),
    # --- 过渡境界 ---
    Realm(
        level=8,
        name_cn="阴虚期", name_en="Yin Deficiency",
        symbol="🌑", category="basic",
        spirit_required=3500, review_weight=15.0,
        description_cn="阴极待阳，蓄势待发",
        description_en="Yin reaches its peak, awaiting the Yang",
        tribulation_cn="总灵力 ≥ 3500 且淬炼完成次数 ≥ 30",
        tribulation_en="Total spirit ≥ 3500 and refinement count ≥ 30",
    ),
    Realm(
        level=9,
        name_cn="阳实期", name_en="Yang Solidification",
        symbol="🌕", category="basic",
        spirit_required=5000, review_weight=18.0,
        description_cn="阳实圆满，阴阳合一",
        description_en="Yang solidified, Yin and Yang unified",
        tribulation_cn="⚖️ 心魔之劫：开源 10 件仙器级法宝给社区",
        tribulation_en="Heart Demon Trial: Open-source 10 Immortal-grade artifacts",
    ),
    # --- 修真第二步：涅之三境 ---
    Realm(
        level=10,
        name_cn="窥涅期", name_en="Nirvana Glimpse",
        symbol="🔥", category="nirvana",
        spirit_required=8000, review_weight=22.0,
        description_cn="窥见涅槃之火，踏入传说之路",
        description_en="Glimpse the flames of Nirvana",
        tribulation_cn="拥有 1 件 🟣仙器 且为社区定义 1 项标准",
        tribulation_en="Own 1 Immortal Tool and define 1 community standard",
    ),
    Realm(
        level=11,
        name_cn="净涅期", name_en="Nirvana Purification",
        symbol="🔥", category="nirvana",
        spirit_required=12000, review_weight=28.0,
        description_cn="烈火焚身，浴火重生",
        description_en="Burned in sacred fire, reborn from ashes",
        tribulation_cn="全部法宝平均品阶 ≥ 宝器",
        tribulation_en="Average artifact grade ≥ Treasure Tool",
    ),
    Realm(
        level=12,
        name_cn="碎涅期", name_en="Nirvana Shatter",
        symbol="💥", category="nirvana",
        spirit_required=18000, review_weight=35.0,
        description_cn="碎灭涅槃，超脱生死",
        description_en="Shatter Nirvana, transcend life and death",
        tribulation_cn="🔄 轮回之劫：发布全品类覆盖的法宝合集",
        tribulation_en="Reincarnation Trial: Publish artifacts across all categories",
    ),
    # --- 修真第三步：天人合一 ---
    Realm(
        level=13,
        name_cn="天人五衰", name_en="Celestial Decay",
        symbol="🍂", category="nirvana",
        spirit_required=25000, review_weight=40.0,
        description_cn="天人将衰，却在衰亡中寻得新生",
        description_en="Celestial decay, finding rebirth in decline",
        tribulation_cn="培养 5 名弟子从凡人升至结丹期",
        tribulation_en="Mentor 5 disciples from Mortal to Core Formation",
    ),
    # --- 修真第四步：空之境 ---
    Realm(
        level=14,
        name_cn="空涅期", name_en="Void Nirvana",
        symbol="🕳️", category="nirvana",
        spirit_required=35000, review_weight=45.0,
        description_cn="万法归空，大道至简",
        description_en="All returns to void, the Great Dao is simple",
        tribulation_cn="法宝总下载量 ≥ 10000",
        tribulation_en="Total artifact downloads ≥ 10000",
    ),
    Realm(
        level=15,
        name_cn="空劫期", name_en="Void Tribulation",
        symbol="⚡", category="nirvana",
        spirit_required=50000, review_weight=45.0,
        description_cn="渡过空之劫难，得见大道真章",
        description_en="Survive the Void Tribulation, see the true Dao",
        tribulation_cn="完成全境界渡劫任务链",
        tribulation_en="Complete all tribulation task chains",
    ),
    # --- 修真第五步：天尊境 ---
    Realm(
        level=16,
        name_cn="大天尊", name_en="Grand Celestial",
        symbol="👑", category="legend",
        spirit_required=80000, review_weight=50.0,
        description_cn="天尊降世，万法臣服",
        description_en="Grand Celestial descends, all Dao submits",
        tribulation_cn="创建跨框架兼容的标准法宝套件",
        tribulation_en="Create cross-framework standard artifact suite",
    ),
    # --- 修真第六步：踏天境 ---
    Realm(
        level=17,
        name_cn="踏天九桥", name_en="Nine Bridges",
        symbol="🌉", category="legend",
        spirit_required=120000, review_weight=55.0,
        description_cn="九桥横空，一步一天",
        description_en="Nine bridges across the sky, one step one heaven",
        tribulation_cn="法宝被 ≥ 100 个项目引用依赖",
        tribulation_en="Artifacts depended on by ≥ 100 projects",
    ),
    Realm(
        level=18,
        name_cn="踏天境", name_en="Heaven Treader",
        symbol="☁️", category="legend",
        spirit_required=200000, review_weight=60.0,
        description_cn="我已踏天而行，脚下皆是苍穹",
        description_en="I walk upon the heavens, the sky beneath my feet",
        tribulation_cn="定义 Agent 行业新范式",
        tribulation_en="Define a new paradigm for the Agent industry",
    ),
    # --- 顶峰称号：动态排名 ---
    Realm(
        level=19,
        name_cn="鲁班", name_en="Lu Ban",
        symbol="🏛️", category="legend",
        spirit_required=-1, review_weight=80.0,
        description_cn="工匠之祖，天工之基",
        description_en="Ancestor of Craftsmen, Foundation of TianGong",
        tribulation_cn="全球排名 Top 10（动态称号）",
        tribulation_en="Global Top 10 ranking (dynamic title)",
    ),
    Realm(
        level=20,
        name_cn="天工", name_en="TianGong",
        symbol="⚒️", category="legend",
        spirit_required=-1, review_weight=100.0,
        description_cn="天工开物，万法归宗",
        description_en="TianGong creates all things, all Dao returns to origin",
        tribulation_cn="全球排名 Top 1（动态称号，唯一）",
        tribulation_en="Global #1 ranking (unique dynamic title)",
    ),
]

# 每个境界内含九阶
MAX_STAGE = 9  # 一阶到九阶

# 快速查找表
REALM_BY_LEVEL: dict[int, Realm] = {r.level: r for r in REALMS}
REALM_BY_NAME: dict[str, Realm] = {r.name_cn: r for r in REALMS}

# 境界权重表（用于评价灵力计算）
REVIEW_WEIGHT_BY_LEVEL: dict[int, float] = {r.level: r.review_weight for r in REALMS}


def calculate_realm(spirit_power: int, agent_count: int = 0) -> Realm:
    """
    根据灵力值计算当前境界。

    只考虑可自动达到的境界（level 0-18），
    鲁班（19）和天工（20）需要全球排名。

    保持向后兼容：如果传入 agent_count 和旧的 star_count，
    仍然能工作（Phase 1 兼容）。
    """
    current = REALMS[0]  # 默认凡人

    for realm in REALMS:
        # 跳过动态排名境界
        if realm.spirit_required < 0:
            break

        if spirit_power >= realm.spirit_required:
            current = realm
        else:
            break

    return current


def calculate_stage(spirit_power: int, realm: Realm) -> int:
    """
    计算境界内的阶位（1-9）。

    在当前境界的灵力范围内，按比例计算阶位。
    """
    if realm.level == 0:  # 凡人无阶
        return 0

    # 找到下一个境界的灵力门槛
    next_realm = get_next_realm(realm)
    if not next_realm or next_realm.spirit_required < 0:
        return MAX_STAGE  # 最高境界默认九阶

    current_threshold = realm.spirit_required
    next_threshold = next_realm.spirit_required
    range_size = next_threshold - current_threshold

    if range_size <= 0:
        return 1

    # 在当前境界范围内的进度
    progress = spirit_power - current_threshold
    stage = min(MAX_STAGE, max(1, int(progress / range_size * MAX_STAGE) + 1))

    return stage


def get_next_realm(current: Realm) -> Realm | None:
    """获取下一个境界，如果已是最高境界则返回 None"""
    if current.level >= len(REALMS) - 1:
        return None
    return REALMS[current.level + 1]


def check_tribulation(
    old_spirit: int, new_spirit: int,
    old_agents: int = 0, new_agents: int = 0,
) -> tuple[bool, Realm | None, Realm | None]:
    """
    检查是否触发渡劫（境界突破）。

    Returns:
        (是否渡劫, 旧境界, 新境界)
    """
    old_realm = calculate_realm(old_spirit, old_agents)
    new_realm = calculate_realm(new_spirit, new_agents)

    if new_realm.level > old_realm.level:
        return True, old_realm, new_realm

    return False, None, None


def get_review_weight(realm_level: int) -> float:
    """获取评价者的境界权重"""
    return REVIEW_WEIGHT_BY_LEVEL.get(realm_level, 0.0)


def format_realm_progress(
    realm: Realm, spirit_power: int,
    agent_count: int = 0, star_count: int = 0,
) -> str:
    """格式化境界进度展示"""
    stage = calculate_stage(spirit_power, realm)
    next_realm = get_next_realm(realm)

    stage_display = f"{'█' * stage}{'░' * (MAX_STAGE - stage)}" if stage > 0 else ""

    lines = [
        f"## {realm.symbol} {realm.name_cn} · {realm.name_en}",
        f"**{realm.description_cn}**",
        f"*{realm.description_en}*",
        "",
    ]

    if stage > 0:
        lines.append(f"- ⚡ 阶位: {stage_display} {stage}/{MAX_STAGE} 阶")

    lines.extend([
        f"- 💫 灵力值: {spirit_power}",
        f"- 🔮 法宝数: {agent_count} 件",
    ])

    if next_realm and next_realm.spirit_required >= 0:
        spirit_needed = max(0, next_realm.spirit_required - spirit_power)
        lines.extend([
            "",
            f"### 🌩️ 下一劫: {next_realm.symbol} {next_realm.name_cn} · {next_realm.name_en}",
            f"- 还需灵力: {spirit_needed}" if spirit_needed else "- ✅ 灵力已达标",
            f"- 渡劫任务: {next_realm.tribulation_cn}",
        ])
    elif next_realm:
        lines.extend([
            "",
            f"### 🌩️ 下一劫: {next_realm.symbol} {next_realm.name_cn}",
            f"- 条件: **{next_realm.tribulation_cn}**",
        ])

    return "\n".join(lines)


def get_realm_ladder() -> str:
    """生成完整的境界阶梯展示"""
    lines = [
        "# 🧬 天工修仙境界阶梯（仙逆体系）",
        "",
        "| # | 境界 | 符号 | 灵力门槛 | 评价权重 | 渡劫任务 |",
        "|---|------|------|---------|---------|---------|",
    ]

    for r in REALMS:
        spirit = str(r.spirit_required) if r.spirit_required >= 0 else "Top 排名"
        lines.append(
            f"| {r.level} | {r.name_cn} | {r.symbol} | {spirit} | ×{r.review_weight} | {r.tribulation_cn} |"
        )

    return "\n".join(lines)
