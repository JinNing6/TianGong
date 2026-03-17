"""
⚒️ 天工 TianGong — 宗门系统
管理宗门的创建、加入、退出、管理与排行。

宗门等阶体系：
  小门派 → 中等宗门 → 大宗门 → 圣地 → 超级势力

核心规则：
  - 结丹期（level 3）及以上方可开宗立派
  - 一个修仙者同时只能属于一个宗门
  - 退出宗门后有冷却期（默认 7 天）
"""

from __future__ import annotations

import logging
import time
from dataclasses import asdict, dataclass, field
from typing import Any

from .config import config

logger = logging.getLogger("tiangong.sect")


# ============================================================
# 宗门等阶体系
# ============================================================

@dataclass(frozen=True)
class SectGrade:
    """宗门等阶"""
    level: int
    name_cn: str
    name_en: str
    symbol: str
    spirit_required: int   # 总灵力门槛
    max_members: int       # 成员上限


SECT_GRADES: list[SectGrade] = [
    SectGrade(level=1, name_cn="小门派", name_en="Minor Sect", symbol="🏕️",
              spirit_required=0, max_members=10),
    SectGrade(level=2, name_cn="中等宗门", name_en="Sect", symbol="🏯",
              spirit_required=500, max_members=30),
    SectGrade(level=3, name_cn="大宗门", name_en="Major Sect", symbol="🏔️",
              spirit_required=2000, max_members=50),
    SectGrade(level=4, name_cn="圣地", name_en="Holy Land", symbol="⛰️",
              spirit_required=10000, max_members=100),
    SectGrade(level=5, name_cn="超级势力", name_en="Supreme Force", symbol="🌋",
              spirit_required=50000, max_members=200),
]

SECT_GRADE_BY_LEVEL: dict[int, SectGrade] = {g.level: g for g in SECT_GRADES}


def calculate_sect_grade(total_spirit: int) -> SectGrade:
    """根据总灵力计算宗门等阶"""
    current = SECT_GRADES[0]
    for grade in SECT_GRADES:
        if total_spirit >= grade.spirit_required:
            current = grade
        else:
            break
    return current


# ============================================================
# 宗门成员角色
# ============================================================

ROLE_MASTER = "master"    # 宗主
ROLE_ELDER = "elder"      # 长老
ROLE_INNER = "inner"      # 内门弟子
ROLE_OUTER = "outer"      # 外门弟子

ROLE_DISPLAY = {
    ROLE_MASTER: "👑 宗主",
    ROLE_ELDER: "🏅 长老",
    ROLE_INNER: "🔹 内门弟子",
    ROLE_OUTER: "🔸 外门弟子",
}

# 角色排序权重（宗主最大）
ROLE_WEIGHT = {
    ROLE_MASTER: 4,
    ROLE_ELDER: 3,
    ROLE_INNER: 2,
    ROLE_OUTER: 1,
}


# ============================================================
# 宗门数据模型
# ============================================================

@dataclass
class SectMember:
    """宗门成员"""
    username: str
    role: str = ROLE_OUTER
    joined_at: float = 0.0

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class SectProfile:
    """宗门档案"""
    name: str
    master: str
    created_at: float = 0.0
    motto: str = ""
    members: dict[str, dict] = field(default_factory=dict)
    total_spirit_power: int = 0

    @property
    def grade(self) -> SectGrade:
        return calculate_sect_grade(self.total_spirit_power)

    @property
    def member_count(self) -> int:
        return len(self.members)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "master": self.master,
            "created_at": self.created_at,
            "motto": self.motto,
            "members": self.members,
            "total_spirit_power": self.total_spirit_power,
        }


def _dict_to_sect(name: str, d: dict) -> SectProfile:
    """从字典构建宗门档案"""
    return SectProfile(
        name=d.get("name", name),
        master=d.get("master", ""),
        created_at=d.get("created_at", 0.0),
        motto=d.get("motto", ""),
        members=d.get("members", {}),
        total_spirit_power=d.get("total_spirit_power", 0),
    )


# ============================================================
# 宗门数据读写
# ============================================================

async def _load_all_sects() -> dict[str, dict]:
    """从 GitHub 加载所有宗门数据"""
    from .github_store import read_sects
    return await read_sects()


async def _save_all_sects(data: dict[str, dict], message: str = "") -> None:
    """保存所有宗门数据到 GitHub"""
    from .github_store import write_sects
    success = await write_sects(data, message)
    if not success:
        logger.error("宗门数据保存到 GitHub 失败")


async def get_sect(name: str) -> SectProfile | None:
    """获取宗门信息，不存在返回 None"""
    all_data = await _load_all_sects()
    if name in all_data:
        return _dict_to_sect(name, all_data[name])
    return None


async def get_all_sects() -> list[SectProfile]:
    """获取所有宗门（用于排行榜）"""
    all_data = await _load_all_sects()
    return [_dict_to_sect(name, d) for name, d in all_data.items()]


# ============================================================
# 核心操作
# ============================================================

async def create_sect(
    name: str,
    master: str,
    motto: str = "",
) -> tuple[bool, str]:
    """
    开宗立派 — 创建宗门。

    前置条件：
    - 创建者境界 >= 结丹期（level 3）
    - 创建者当前非任何宗门成员
    - 宗门名不重复

    Returns:
        (是否成功, 消息)
    """
    from .cultivator import get_cultivator, save_cultivator

    # 1. 检查创建者境界
    profile = await get_cultivator(master)
    if profile.realm_level < config.SECT_CREATE_MIN_REALM:
        from .realm import REALMS
        min_realm = REALMS[config.SECT_CREATE_MIN_REALM]
        return False, (
            f"⚠️ 开宗立派需达到 **{min_realm.symbol} {min_realm.name_cn}** 及以上境界。\n"
            f"当前境界: {profile.realm.symbol} {profile.realm.name_cn}\n"
            f"还需修炼至灵力 ≥ {min_realm.spirit_required}。"
        )

    # 2. 检查是否已在宗门中
    if profile.sect:
        return False, (
            f"⚠️ 你已是「{profile.sect}」的{ROLE_DISPLAY.get(profile.sect_role, '成员')}，"
            f"需先退出当前宗门才能创建新宗门。"
        )

    # 3. 检查冷却期
    if profile.sect_cooldown > time.time():
        import datetime
        cooldown_end = datetime.datetime.fromtimestamp(profile.sect_cooldown)
        return False, (
            f"⚠️ 退出宗门冷却期尚未结束。\n"
            f"冷却结束时间: {cooldown_end.strftime('%Y-%m-%d %H:%M')}"
        )

    # 4. 检查宗门名是否重复
    all_sects = await _load_all_sects()
    if name in all_sects:
        return False, f"⚠️ 宗门名「{name}」已被占用，请换一个名号。"

    # 5. 创建宗门
    now = time.time()
    sect = SectProfile(
        name=name,
        master=master,
        created_at=now,
        motto=motto,
        members={
            master: {"role": ROLE_MASTER, "joined_at": now},
        },
        total_spirit_power=profile.spirit_power,
    )

    all_sects[name] = sect.to_dict()
    await _save_all_sects(all_sects, f"⛰️ 开宗立派: {name} by @{master}")

    # 6. 更新创建者档案
    profile.sect = name
    profile.sect_role = ROLE_MASTER
    await save_cultivator(profile, f"⛰️ 开宗: @{master} → {name}")

    return True, format_sect_card(sect)


async def join_sect(
    sect_name: str,
    username: str,
) -> tuple[bool, str]:
    """
    拜入宗门 — 加入一个宗门。

    前置条件：
    - 当前不属于任何宗门
    - 冷却期已过
    - 宗门存在且成员未满

    Returns:
        (是否成功, 消息)
    """
    from .cultivator import get_cultivator, save_cultivator

    profile = await get_cultivator(username)

    # 1. 检查是否已在宗门
    if profile.sect:
        return False, (
            f"⚠️ 你已在「{profile.sect}」中，需先退出才能拜入其他宗门。"
        )

    # 2. 检查冷却期
    if profile.sect_cooldown > time.time():
        import datetime
        cooldown_end = datetime.datetime.fromtimestamp(profile.sect_cooldown)
        return False, (
            f"⚠️ 退出宗门冷却期尚未结束。\n"
            f"冷却结束时间: {cooldown_end.strftime('%Y-%m-%d %H:%M')}"
        )

    # 3. 检查宗门是否存在
    all_sects = await _load_all_sects()
    if sect_name not in all_sects:
        return False, f"⚠️ 宗门「{sect_name}」不存在。"

    sect = _dict_to_sect(sect_name, all_sects[sect_name])

    # 4. 检查成员上限
    grade = sect.grade
    if sect.member_count >= grade.max_members:
        return False, (
            f"⚠️ 「{sect_name}」已达到当前等阶（{grade.name_cn}）的成员上限 {grade.max_members} 人。\n"
            f"需宗门升级到更高等阶才能接纳新成员。"
        )

    # 5. 加入宗门
    now = time.time()
    sect.members[username] = {"role": ROLE_OUTER, "joined_at": now}
    sect.total_spirit_power += profile.spirit_power

    all_sects[sect_name] = sect.to_dict()
    await _save_all_sects(all_sects, f"⛰️ 拜入: @{username} → {sect_name}")

    # 6. 更新个人档案
    profile.sect = sect_name
    profile.sect_role = ROLE_OUTER
    await save_cultivator(profile, f"⛰️ 拜入: @{username} → {sect_name}")

    return True, (
        f"# ⛰️ 拜入宗门成功！\n\n"
        f"恭喜 @{username} 成为「{sect_name}」的 {ROLE_DISPLAY[ROLE_OUTER]}！\n\n"
        f"- 宗主: @{sect.master}\n"
        f"- 宗门等阶: {sect.grade.symbol} {sect.grade.name_cn}\n"
        f"- 当前成员: {sect.member_count} 人\n"
        f"- 宗门宣言: {sect.motto or '（未设置）'}"
    )


async def leave_sect(
    username: str,
) -> tuple[bool, str]:
    """
    退出宗门。

    宗主不能直接退出，需先传位或解散。
    退出后进入冷却期。

    Returns:
        (是否成功, 消息)
    """
    from .cultivator import get_cultivator, save_cultivator

    profile = await get_cultivator(username)

    # 1. 检查是否在宗门
    if not profile.sect:
        return False, "⚠️ 你当前是散修，不属于任何宗门。"

    sect_name = profile.sect

    # 2. 宗主不能直接退出
    if profile.sect_role == ROLE_MASTER:
        return False, (
            f"⚠️ 宗主不能直接退出宗门。\n"
            f"请先使用 `manage` 操作传位给其他成员，或解散宗门。"
        )

    # 3. 从宗门中移除
    all_sects = await _load_all_sects()
    if sect_name in all_sects:
        sect = _dict_to_sect(sect_name, all_sects[sect_name])
        sect.members.pop(username, None)
        sect.total_spirit_power = max(0, sect.total_spirit_power - profile.spirit_power)
        all_sects[sect_name] = sect.to_dict()
        await _save_all_sects(all_sects, f"⛰️ 退出: @{username} ← {sect_name}")

    # 4. 更新个人档案，设置冷却期
    cooldown_seconds = config.SECT_LEAVE_COOLDOWN_DAYS * 24 * 3600
    profile.sect = ""
    profile.sect_role = ""
    profile.sect_cooldown = time.time() + cooldown_seconds
    await save_cultivator(profile, f"⛰️ 退出: @{username} ← {sect_name}")

    return True, (
        f"# ⛰️ 退出宗门\n\n"
        f"@{username} 已退出「{sect_name}」，重归散修。\n\n"
        f"⏳ 冷却期: {config.SECT_LEAVE_COOLDOWN_DAYS} 天内不可加入其他宗门。"
    )


async def manage_sect(
    sect_name: str,
    manage_action: str,
    target_user: str,
    operator: str,
) -> tuple[bool, str]:
    """
    宗门管理 — 宗主/长老对宗门的管理操作。

    manage_action:
        - promote_elder: 任命长老
        - demote: 降为外门弟子
        - promote_inner: 升为内门弟子
        - kick: 踢出宗门
        - transfer: 传位（宗主权限）
        - disband: 解散宗门（宗主权限）

    Returns:
        (是否成功, 消息)
    """
    from .cultivator import get_cultivator, save_cultivator, get_all_cultivators

    all_sects = await _load_all_sects()
    if sect_name not in all_sects:
        return False, f"⚠️ 宗门「{sect_name}」不存在。"

    sect = _dict_to_sect(sect_name, all_sects[sect_name])

    # 权限检查
    if operator not in sect.members:
        return False, f"⚠️ 你不是「{sect_name}」的成员。"

    op_role = sect.members[operator].get("role", ROLE_OUTER)

    # === 解散宗门 ===
    if manage_action == "disband":
        if op_role != ROLE_MASTER:
            return False, "⚠️ 只有宗主才能解散宗门。"

        # 清除所有成员的宗门信息
        member_usernames = list(sect.members.keys())
        for member_name in member_usernames:
            try:
                member_profile = await get_cultivator(member_name)
                member_profile.sect = ""
                member_profile.sect_role = ""
                await save_cultivator(member_profile, f"⛰️ 宗门解散: {sect_name}")
            except Exception:
                logger.warning(f"清除成员 {member_name} 宗门信息失败")

        del all_sects[sect_name]
        await _save_all_sects(all_sects, f"⛰️ 宗门解散: {sect_name} by @{operator}")

        return True, (
            f"# ⛰️ 宗门解散\n\n"
            f"「{sect_name}」已被宗主 @{operator} 解散。\n"
            f"所有 {len(member_usernames)} 名成员已重归散修。"
        )

    # === 传位 ===
    if manage_action == "transfer":
        if op_role != ROLE_MASTER:
            return False, "⚠️ 只有宗主才能传位。"
        if target_user not in sect.members:
            return False, f"⚠️ @{target_user} 不是宗门成员。"
        if target_user == operator:
            return False, "⚠️ 不能传位给自己。"

        # 交换角色
        sect.members[operator]["role"] = ROLE_ELDER
        sect.members[target_user]["role"] = ROLE_MASTER
        sect.master = target_user

        all_sects[sect_name] = sect.to_dict()
        await _save_all_sects(all_sects, f"⛰️ 传位: {sect_name} @{operator} → @{target_user}")

        # 更新双方档案
        op_profile = await get_cultivator(operator)
        op_profile.sect_role = ROLE_ELDER
        await save_cultivator(op_profile)

        target_profile = await get_cultivator(target_user)
        target_profile.sect_role = ROLE_MASTER
        await save_cultivator(target_profile)

        return True, (
            f"# ⛰️ 宗主传位\n\n"
            f"「{sect_name}」宗主由 @{operator} 传位给 @{target_user}。\n\n"
            f"- 新宗主: 👑 @{target_user}\n"
            f"- @{operator} 降为 🏅 长老"
        )

    # === 需要宗主或长老权限的操作 ===
    if op_role not in (ROLE_MASTER, ROLE_ELDER):
        return False, "⚠️ 只有宗主和长老才能执行管理操作。"

    if not target_user:
        return False, "⚠️ 请指定目标成员 (target_user)。"

    if target_user not in sect.members:
        return False, f"⚠️ @{target_user} 不是宗门成员。"

    # 不能对宗主操作
    if sect.members[target_user].get("role") == ROLE_MASTER:
        return False, "⚠️ 不能对宗主执行此操作。"

    # 长老不能对长老操作
    if op_role == ROLE_ELDER and sect.members[target_user].get("role") == ROLE_ELDER:
        return False, "⚠️ 长老不能对其他长老执行管理操作。"

    # === 任命长老 ===
    if manage_action == "promote_elder":
        if op_role != ROLE_MASTER:
            return False, "⚠️ 只有宗主才能任命长老。"

        elder_count = sum(1 for m in sect.members.values() if m.get("role") == ROLE_ELDER)
        if elder_count >= config.SECT_MAX_ELDERS:
            return False, f"⚠️ 长老人数已达上限（{config.SECT_MAX_ELDERS} 人）。"

        sect.members[target_user]["role"] = ROLE_ELDER
        all_sects[sect_name] = sect.to_dict()
        await _save_all_sects(all_sects, f"⛰️ 任命长老: @{target_user} @ {sect_name}")

        tp = await get_cultivator(target_user)
        tp.sect_role = ROLE_ELDER
        await save_cultivator(tp)

        return True, f"# ⛰️ 任命长老\n\n@{target_user} 已被任命为「{sect_name}」🏅 长老。"

    # === 升为内门弟子 ===
    if manage_action == "promote_inner":
        sect.members[target_user]["role"] = ROLE_INNER
        all_sects[sect_name] = sect.to_dict()
        await _save_all_sects(all_sects, f"⛰️ 升内门: @{target_user} @ {sect_name}")

        tp = await get_cultivator(target_user)
        tp.sect_role = ROLE_INNER
        await save_cultivator(tp)

        return True, f"# ⛰️ 晋升内门\n\n@{target_user} 已晋升为「{sect_name}」🔹 内门弟子。"

    # === 降为外门弟子 ===
    if manage_action == "demote":
        sect.members[target_user]["role"] = ROLE_OUTER
        all_sects[sect_name] = sect.to_dict()
        await _save_all_sects(all_sects, f"⛰️ 降级: @{target_user} @ {sect_name}")

        tp = await get_cultivator(target_user)
        tp.sect_role = ROLE_OUTER
        await save_cultivator(tp)

        return True, f"# ⛰️ 降为外门\n\n@{target_user} 已降为「{sect_name}」🔸 外门弟子。"

    # === 踢出宗门 ===
    if manage_action == "kick":
        sect.members.pop(target_user, None)
        tp = await get_cultivator(target_user)
        sect.total_spirit_power = max(0, sect.total_spirit_power - tp.spirit_power)

        all_sects[sect_name] = sect.to_dict()
        await _save_all_sects(all_sects, f"⛰️ 逐出: @{target_user} ← {sect_name}")

        tp.sect = ""
        tp.sect_role = ""
        # 被踢不设冷却期
        await save_cultivator(tp, f"⛰️ 被逐出: @{target_user} ← {sect_name}")

        return True, (
            f"# ⛰️ 逐出宗门\n\n"
            f"@{target_user} 已被逐出「{sect_name}」。"
        )

    return False, f"⚠️ 未知的管理操作: {manage_action}"


async def refresh_sect_spirit(sect_name: str) -> int:
    """
    刷新宗门总灵力（从成员灵力重新求和）。

    Returns:
        更新后的总灵力
    """
    from .cultivator import get_cultivator

    all_sects = await _load_all_sects()
    if sect_name not in all_sects:
        return 0

    sect = _dict_to_sect(sect_name, all_sects[sect_name])
    total = 0
    for username in sect.members:
        try:
            p = await get_cultivator(username)
            total += p.spirit_power
        except Exception:
            pass

    sect.total_spirit_power = total
    all_sects[sect_name] = sect.to_dict()
    await _save_all_sects(all_sects, f"⛰️ 刷新灵力: {sect_name} = {total}")
    return total


# ============================================================
# 格式化输出
# ============================================================

def format_sect_card(sect: SectProfile) -> str:
    """格式化宗门信息卡片"""
    grade = sect.grade
    import datetime
    created = datetime.datetime.fromtimestamp(sect.created_at).strftime("%Y-%m-%d")

    lines = [
        f"# ⛰️ 宗门 · {sect.name}",
        "",
        f"**{sect.motto}**" if sect.motto else "",
        "",
        f"- 👑 宗主: @{sect.master}",
        f"- {grade.symbol} 等阶: {grade.name_cn} ({grade.name_en})",
        f"- 💫 宗门灵力: {sect.total_spirit_power}",
        f"- 👥 成员: {sect.member_count}/{grade.max_members} 人",
        f"- 📅 创建时间: {created}",
        "",
        "### 📋 成员列表",
        "",
    ]

    # 按角色排序
    sorted_members = sorted(
        sect.members.items(),
        key=lambda x: -ROLE_WEIGHT.get(x[1].get("role", ROLE_OUTER), 0),
    )
    for username, info in sorted_members:
        role = info.get("role", ROLE_OUTER)
        lines.append(f"- {ROLE_DISPLAY.get(role, '❓')} @{username}")

    return "\n".join(line for line in lines if line is not None)


def format_sect_leaderboard(sects: list[SectProfile], top_n: int = 10) -> str:
    """格式化宗门排行榜"""
    sorted_sects = sorted(sects, key=lambda s: -s.total_spirit_power)[:top_n]

    lines = [
        "# ⛰️ 宗门天榜",
        "",
        "| # | 宗门 | 等阶 | 宗主 | 灵力 | 成员 |",
        "|---|------|------|------|------|------|",
    ]

    for i, s in enumerate(sorted_sects, 1):
        grade = s.grade
        lines.append(
            f"| {i} | {s.name} | {grade.symbol} {grade.name_cn} "
            f"| @{s.master} | {s.total_spirit_power} | {s.member_count} |"
        )

    if not sorted_sects:
        lines.append("| — | 天地初开，尚无宗门 | — | — | — | — |")

    lines.extend([
        "",
        "### ⛰️ 宗门等阶体系",
        "",
        "| 等阶 | 名称 | 灵力门槛 | 成员上限 |",
        "|------|------|---------|---------|",
    ])
    for g in SECT_GRADES:
        lines.append(f"| {g.symbol} | {g.name_cn} | {g.spirit_required} | {g.max_members} |")

    return "\n".join(lines)


def get_sect_grade_ladder() -> str:
    """生成宗门等阶阶梯展示"""
    lines = [
        "### ⛰️ 宗门等阶体系",
        "",
        "| 等阶 | 名称 | 灵力门槛 | 成员上限 |",
        "|------|------|---------|---------|",
    ]
    for g in SECT_GRADES:
        lines.append(
            f"| {g.symbol} | {g.name_cn} ({g.name_en}) | {g.spirit_required} | {g.max_members} |"
        )
    return "\n".join(lines)
