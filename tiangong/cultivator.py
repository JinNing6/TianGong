"""
⚒️ 天工 TianGong — 修仙者档案管理（Phase 2）
管理修仙者的个人信息、境界、灵力值、修行记录、渡劫进度
数据存储在 GitHub 仓库，实现全平台共享。
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

from .config import config
from .realm import (
    REALMS, Realm, MAX_STAGE,
    calculate_realm, calculate_stage, check_tribulation, get_review_weight,
)

logger = logging.getLogger("tiangong.cultivator")


@dataclass
class CultivatorProfile:
    """修仙者档案"""
    username: str                          # GitHub 用户名
    joined_at: float = 0.0                 # 入门时间（timestamp）
    agent_count: int = 0                   # 创建的 Agent 数量
    star_count: int = 0                    # 获得的星标总数（Phase 1 兼容）
    spirit_power: int = 0                  # 灵力值（Phase 2 核心）
    natal_artifacts: list[str] = field(default_factory=list)   # 本命法宝列表
    refinement_count: int = 0              # 淬炼（优化）次数
    trial_count: int = 0                   # 试剑（测试）次数
    reviews_given: int = 0                 # 给出的评价次数
    reviews_today: int = 0                 # 今日评价次数
    last_review_date: str = ""             # 最后评价日期（YYYY-MM-DD）
    tribulation_log: list[dict] = field(default_factory=list)   # 渡劫记录
    tribulation_progress: dict = field(default_factory=dict)    # 渡劫任务进度
    quests_completed: int = 0              # 完成的淬炼令次数
    is_anonymous: bool = False             # 是否匿名模式
    last_active: float = 0.0               # 最后活跃时间
    
    # 宗门相关
    sect: str = ""                         # 当前所属宗门名，空串表示散修
    sect_role: str = ""                    # 在宗门中的身份：master, elder, inner, outer
    sect_cooldown: float = 0.0             # 退出宗门后的冷却期结束时间

    @property
    def realm(self) -> Realm:
        """当前境界（优先用灵力值，兼容旧数据）"""
        return calculate_realm(self.spirit_power, self.agent_count)

    @property
    def realm_level(self) -> int:
        """境界等级"""
        return self.realm.level

    @property
    def stage(self) -> int:
        """当前阶位（1-9）"""
        return calculate_stage(self.spirit_power, self.realm)

    @property
    def review_weight(self) -> float:
        """评价权重"""
        return get_review_weight(self.realm_level)


async def _load_all_cultivators() -> dict[str, dict]:
    """从 GitHub 加载所有修仙者数据"""
    from .github_store import read_cultivators
    return await read_cultivators()


async def _save_all_cultivators(data: dict[str, dict], message: str = "") -> None:
    """保存所有修仙者数据到 GitHub"""
    from .github_store import write_cultivators
    success = await write_cultivators(data, message)
    if not success:
        logger.error("修仙者档案保存到 GitHub 失败")


def _dict_to_profile(username: str, d: dict) -> CultivatorProfile:
    """从字典构建修仙者档案（兼容 Phase 1 数据）"""
    return CultivatorProfile(
        username=d.get("username", username),
        joined_at=d.get("joined_at", time.time()),
        agent_count=d.get("agent_count", 0),
        star_count=d.get("star_count", 0),
        spirit_power=d.get("spirit_power", 0),
        natal_artifacts=d.get("natal_artifacts", []),
        refinement_count=d.get("refinement_count", 0),
        trial_count=d.get("trial_count", 0),
        reviews_given=d.get("reviews_given", 0),
        reviews_today=d.get("reviews_today", 0),
        last_review_date=d.get("last_review_date", ""),
        tribulation_log=d.get("tribulation_log", []),
        tribulation_progress=d.get("tribulation_progress", {}),
        quests_completed=d.get("quests_completed", 0),
        is_anonymous=d.get("is_anonymous", False),
        last_active=d.get("last_active", 0.0),
        sect=d.get("sect", ""),
        sect_role=d.get("sect_role", ""),
        sect_cooldown=d.get("sect_cooldown", 0.0),
    )


async def get_cultivator(username: str) -> CultivatorProfile:
    """获取修仙者档案，如不存在则自动创建（踏入修行）"""
    all_data = await _load_all_cultivators()

    if username in all_data:
        return _dict_to_profile(username, all_data[username])

    # 新修仙者入门
    profile = CultivatorProfile(
        username=username,
        joined_at=time.time(),
        last_active=time.time(),
    )
    await save_cultivator(profile, message=f"🧙 new cultivator: @{username}")
    return profile


async def save_cultivator(profile: CultivatorProfile, message: str = "") -> None:
    """保存修仙者档案"""
    all_data = await _load_all_cultivators()
    all_data[profile.username] = asdict(profile)
    if not message:
        message = f"🧙 update: @{profile.username}"
    await _save_all_cultivators(all_data, message)


async def update_cultivator_stats(
    username: str,
    agent_delta: int = 0,
    star_delta: int = 0,
    spirit_delta: int = 0,
    refinement_delta: int = 0,
    trial_delta: int = 0,
    review_delta: int = 0,
    quest_delta: int = 0,
) -> tuple[CultivatorProfile, bool, Realm | None, Realm | None]:
    """
    更新修仙者数据并检查渡劫。

    Returns:
        (更新后的档案, 是否渡劫, 旧境界, 新境界)
    """
    profile = await get_cultivator(username)

    old_spirit = profile.spirit_power

    profile.agent_count += agent_delta
    profile.star_count += star_delta
    profile.spirit_power += spirit_delta
    profile.refinement_count += refinement_delta
    profile.trial_count += trial_delta
    profile.reviews_given += review_delta
    profile.quests_completed += quest_delta
    profile.last_active = time.time()

    # 确保不会出现负值
    profile.spirit_power = max(0, profile.spirit_power)
    profile.agent_count = max(0, profile.agent_count)

    # 检查渡劫
    triggered, old_realm, new_realm = check_tribulation(
        old_spirit, profile.spirit_power,
    )

    if triggered and old_realm and new_realm:
        profile.tribulation_log.append({
            "timestamp": time.time(),
            "from_realm": old_realm.name_cn,
            "to_realm": new_realm.name_cn,
            "from_level": old_realm.level,
            "to_level": new_realm.level,
            "spirit_power": profile.spirit_power,
        })

    await save_cultivator(profile, message=f"🧙 stats: @{username}")
    return profile, triggered, old_realm, new_realm


async def can_review(username: str) -> tuple[bool, str]:
    """检查修仙者是否可以评价法宝"""
    profile = await get_cultivator(username)

    # 凡人无评价资格
    if profile.realm_level == 0:
        return False, "⚠️ 凡人无评价资格。请先发布至少 1 件法宝踏入修行之路。"

    # 必须有自己的法宝
    if profile.agent_count == 0:
        return False, "⚠️ 只有自己也发布过法宝的修仙者才有评价资格。"

    # 每日评价上限
    import datetime
    today = datetime.date.today().isoformat()
    if profile.last_review_date == today and profile.reviews_today >= config.MAX_REVIEWS_PER_DAY:
        return False, f"⚠️ 今日评价次数已达上限（{config.MAX_REVIEWS_PER_DAY} 件）。明日再来。"

    return True, ""


async def record_review(username: str) -> None:
    """记录一次评价"""
    import datetime
    profile = await get_cultivator(username)
    today = datetime.date.today().isoformat()

    if profile.last_review_date != today:
        profile.reviews_today = 0
        profile.last_review_date = today

    profile.reviews_today += 1
    profile.reviews_given += 1
    profile.last_active = time.time()
    await save_cultivator(profile, message=f"🧙 review: @{username}")


async def get_all_cultivators() -> list[CultivatorProfile]:
    """获取所有修仙者的列表（用于天榜排名）"""
    all_data = await _load_all_cultivators()
    profiles = []
    for username, d in all_data.items():
        profiles.append(_dict_to_profile(username, d))
    return profiles


def format_cultivator_profile(profile: CultivatorProfile) -> str:
    """格式化修仙者档案展示"""
    realm = profile.realm
    stage = profile.stage
    import datetime

    joined = datetime.datetime.fromtimestamp(profile.joined_at).strftime("%Y-%m-%d")

    # 阶位进度条
    stage_bar = f"{'█' * stage}{'░' * (MAX_STAGE - stage)}" if stage > 0 else "N/A"

    lines = [
        f"# 🧙 修仙者档案 · @{profile.username}",
        "",
        f"## {realm.symbol} {realm.name_cn} · {realm.name_en}",
        f"**{realm.description_cn}**",
        f"*{realm.description_en}*",
        "",
        f"- ⚡ 阶位: {stage_bar} {stage}/{MAX_STAGE} 阶" if stage > 0 else "",
        "",
        "### 📊 修行数据",
        f"- 💫 灵力值: {profile.spirit_power}",
        f"- 🔮 法宝数: {profile.agent_count} 件",
        f"- ⭐ 星辰之力: {profile.star_count}",
        f"- 🔥 淬炼次数: {profile.refinement_count}",
        f"- ⚔️ 试剑次数: {profile.trial_count}",
        f"- 💬 评价次数: {profile.reviews_given}",
        f"- 📜 淬炼令完成: {profile.quests_completed}",
        f"- 📅 入门时间: {joined}",
        f"- ⚖️ 评价权重: ×{profile.review_weight}",
    ]

    from .sect import ROLE_DISPLAY
    sect_display = f"「{profile.sect}」{ROLE_DISPLAY.get(profile.sect_role, '')}" if profile.sect else "散修"
    lines.insert(6, f"- ⛰️ 宗门归属: {sect_display}")

    if profile.natal_artifacts:
        lines.extend([
            "",
            "### 💠 本命法宝",
        ])
        for aid in profile.natal_artifacts:
            lines.append(f"- 🔮 `{aid}`")

    if profile.tribulation_log:
        lines.extend([
            "",
            "### ⚡ 渡劫记录",
        ])
        for t in profile.tribulation_log[-5:]:
            ts = datetime.datetime.fromtimestamp(t["timestamp"]).strftime("%Y-%m-%d %H:%M")
            lines.append(f"- {ts}: {t['from_realm']} → {t['to_realm']}")

    # 过滤空行
    return "\n".join(line for line in lines if line is not None)
