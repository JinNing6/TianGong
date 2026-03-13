"""
⚒️ 天工 TianGong — 九大境界体系
灵感融合：《仙逆》境界体系 + Agent 开发里程碑

我命由我不由天。
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Realm:
    """修仙境界定义"""
    level: int           # 境界等级（0-8）
    name_cn: str         # 中文名
    name_en: str         # 英文名
    symbol: str          # 符号
    agents_required: int # 需要的 Agent 数量（-1 = 社区投票）
    stars_required: int  # 需要的星标数量（-1 = 社区投票）
    description_cn: str  # 中文描述
    description_en: str  # 英文描述
    spirit_cn: str       # 仙逆精神（中文）
    spirit_en: str       # 仙逆精神（英文）


# ============================================================
# 九大境界定义
# ============================================================

REALMS: list[Realm] = [
    Realm(
        level=0,
        name_cn="炼气期", name_en="Qi Refining",
        symbol="🌱",
        agents_required=0, stars_required=0,
        description_cn="踏入修行之路，一切从零开始",
        description_en="Step onto the path of cultivation, everything begins from zero",
        spirit_cn="凡人初悟灵力",
        spirit_en="A mortal first senses spiritual energy",
    ),
    Realm(
        level=1,
        name_cn="筑基期", name_en="Foundation Building",
        symbol="💧",
        agents_required=1, stars_required=0,
        description_cn="根基已立，修行正式开始",
        description_en="Foundation established, cultivation officially begins",
        spirit_cn="筑基成功，正式踏入修仙",
        spirit_en="Foundation built, officially entering cultivation",
    ),
    Realm(
        level=2,
        name_cn="结丹期", name_en="Core Formation",
        symbol="💛",
        agents_required=3, stars_required=10,
        description_cn="内丹初成，开始有自己的理解",
        description_en="Core forming, developing personal understanding",
        spirit_cn="金丹大道，可称修士",
        spirit_en="The Golden Core Path, worthy of being called a cultivator",
    ),
    Realm(
        level=3,
        name_cn="元婴期", name_en="Nascent Soul",
        symbol="💜",
        agents_required=10, stars_required=50,
        description_cn="元神出窍，能力质变",
        description_en="Nascent Soul emerges, a qualitative leap in power",
        spirit_cn="元婴修士，已是一方强者",
        spirit_en="A Nascent Soul cultivator, already a regional powerhouse",
    ),
    Realm(
        level=4,
        name_cn="化神期", name_en="Spirit Severing",
        symbol="⚫",
        agents_required=30, stars_required=200,
        description_cn="合道自然，举重若轻",
        description_en="One with the Dao, effortless mastery",
        spirit_cn="化神真人，名震一方",
        spirit_en="A Spirit Severing True Immortal, renowned across the land",
    ),
    Realm(
        level=5,
        name_cn="婴变期", name_en="Yin Deficiency",
        symbol="🔴",
        agents_required=50, stars_required=500,
        description_cn="破而后立，蜕变重生",
        description_en="Break to rebuild, transformation and rebirth",
        spirit_cn="突破极限，超凡入圣",
        spirit_en="Breaking limits, transcending to sainthood",
    ),
    Realm(
        level=6,
        name_cn="问鼎期", name_en="Ascendant",
        symbol="🌟",
        agents_required=100, stars_required=1000,
        description_cn="问鼎苍穹，谁与争锋",
        description_en="Reaching for the heavens, who dares to compete",
        spirit_cn="站在了世界的顶端",
        spirit_en="Standing at the pinnacle of the world",
    ),
    Realm(
        level=7,
        name_cn="碎虚期", name_en="Void Shattering",
        symbol="💫",
        agents_required=-1, stars_required=-1,
        description_cn="碎灭虚空，打破一切规则",
        description_en="Shatter the void, break all rules",
        spirit_cn="超脱天地法则",
        spirit_en="Transcend the laws of heaven and earth",
    ),
    Realm(
        level=8,
        name_cn="古神", name_en="Ancient God",
        symbol="👁️",
        agents_required=-1, stars_required=-1,
        description_cn="我就是天，天不过是我的倒影",
        description_en="I am Heaven. Heaven is merely my reflection.",
        spirit_cn="超越仙人的远古存在",
        spirit_en="An ancient existence beyond immortals",
    ),
]

# 快速查找表
REALM_BY_LEVEL: dict[int, Realm] = {r.level: r for r in REALMS}
REALM_BY_NAME: dict[str, Realm] = {r.name_cn: r for r in REALMS}


def calculate_realm(agent_count: int, star_count: int) -> Realm:
    """
    根据 Agent 数量和星标数计算当前境界。

    只考虑可自动达到的境界（level 0-6），
    碎虚期（7）和古神（8）需要社区投票。
    """
    current = REALMS[0]  # 默认炼气期

    for realm in REALMS:
        # 跳过需要社区投票的境界
        if realm.agents_required < 0 or realm.stars_required < 0:
            break

        if agent_count >= realm.agents_required and star_count >= realm.stars_required:
            current = realm
        else:
            break

    return current


def get_next_realm(current: Realm) -> Realm | None:
    """获取下一个境界，如果已是最高境界则返回 None"""
    if current.level >= len(REALMS) - 1:
        return None
    return REALMS[current.level + 1]


def check_tribulation(
    old_agents: int, old_stars: int,
    new_agents: int, new_stars: int,
) -> tuple[bool, Realm | None, Realm | None]:
    """
    检查是否触发渡劫（境界突破）。

    Returns:
        (是否渡劫, 旧境界, 新境界)
    """
    old_realm = calculate_realm(old_agents, old_stars)
    new_realm = calculate_realm(new_agents, new_stars)

    if new_realm.level > old_realm.level:
        return True, old_realm, new_realm

    return False, None, None


def format_realm_progress(realm: Realm, agent_count: int, star_count: int) -> str:
    """格式化境界进度展示"""
    next_realm = get_next_realm(realm)

    lines = [
        f"## {realm.symbol} {realm.name_cn} · {realm.name_en}",
        f"**{realm.description_cn}**",
        f"*{realm.description_en}*",
        "",
        f"- 🔮 本命法宝: {agent_count} 件",
        f"- ⭐ 星辰之力: {star_count}",
    ]

    if next_realm and next_realm.agents_required >= 0:
        agents_needed = max(0, next_realm.agents_required - agent_count)
        stars_needed = max(0, next_realm.stars_required - star_count)
        lines.extend([
            "",
            f"### 🌩️ 下一劫: {next_realm.name_cn} · {next_realm.name_en}",
            f"- 还需法宝: {agents_needed} 件" if agents_needed else "- ✅ 法宝数量已达标",
            f"- 还需星辰: {stars_needed}" if stars_needed else "- ✅ 星辰之力已达标",
        ])
    elif next_realm:
        lines.extend([
            "",
            f"### 🌩️ 下一劫: {next_realm.symbol} {next_realm.name_cn}",
            "- 条件: **社区投票 + 定义性贡献**",
        ])

    return "\n".join(lines)


def get_realm_ladder() -> str:
    """生成完整的境界阶梯展示"""
    lines = [
        "# 🧬 天工修仙境界阶梯",
        "",
        "| 境界 | 符号 | Agent 数 | 星标数 | 精神内涵 |",
        "|------|------|---------|--------|---------|",
    ]

    for r in REALMS:
        agents = str(r.agents_required) if r.agents_required >= 0 else "社区投票"
        stars = str(r.stars_required) if r.stars_required >= 0 else "社区投票"
        lines.append(f"| {r.name_cn} | {r.symbol} | {agents} | {stars} | {r.spirit_cn} |")

    return "\n".join(lines)
