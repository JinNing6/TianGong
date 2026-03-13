"""
⚒️ 天工 TianGong — 修仙者档案管理
管理修仙者的个人信息、境界、修行记录
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

from .config import config
from .realm import REALMS, Realm, calculate_realm, check_tribulation

logger = logging.getLogger("tiangong.cultivator")


@dataclass
class CultivatorProfile:
    """修仙者档案"""
    username: str                          # GitHub 用户名
    joined_at: float = 0.0                 # 入门时间（timestamp）
    agent_count: int = 0                   # 创建的 Agent 数量
    star_count: int = 0                    # 获得的星标总数
    natal_artifacts: list[str] = field(default_factory=list)  # 本命法宝列表（agent_id）
    refinement_count: int = 0              # 淬炼（优化）次数
    trial_count: int = 0                   # 试剑（测试）次数
    tribulation_log: list[dict] = field(default_factory=list)  # 渡劫记录
    last_active: float = 0.0              # 最后活跃时间

    @property
    def realm(self) -> Realm:
        """当前境界"""
        return calculate_realm(self.agent_count, self.star_count)

    @property
    def realm_level(self) -> int:
        """境界等级"""
        return self.realm.level


def _get_storage_path() -> Path:
    """获取修仙者档案存储路径"""
    return Path(config.CULTIVATORS_FILE)


def _load_all_cultivators() -> dict[str, dict]:
    """加载所有修仙者数据"""
    path = _get_storage_path()
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError) as e:
        logger.warning(f"修仙者档案加载失败: {e}")
        return {}


def _save_all_cultivators(data: dict[str, dict]) -> None:
    """保存所有修仙者数据"""
    path = _get_storage_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def get_cultivator(username: str) -> CultivatorProfile:
    """获取修仙者档案，如不存在则自动创建（踏入修行）"""
    all_data = _load_all_cultivators()

    if username in all_data:
        d = all_data[username]
        return CultivatorProfile(
            username=d.get("username", username),
            joined_at=d.get("joined_at", time.time()),
            agent_count=d.get("agent_count", 0),
            star_count=d.get("star_count", 0),
            natal_artifacts=d.get("natal_artifacts", []),
            refinement_count=d.get("refinement_count", 0),
            trial_count=d.get("trial_count", 0),
            tribulation_log=d.get("tribulation_log", []),
            last_active=d.get("last_active", 0.0),
        )

    # 新修仙者入门
    profile = CultivatorProfile(
        username=username,
        joined_at=time.time(),
        last_active=time.time(),
    )
    save_cultivator(profile)
    return profile


def save_cultivator(profile: CultivatorProfile) -> None:
    """保存修仙者档案"""
    all_data = _load_all_cultivators()
    all_data[profile.username] = asdict(profile)
    _save_all_cultivators(all_data)


def update_cultivator_stats(
    username: str,
    agent_delta: int = 0,
    star_delta: int = 0,
    refinement_delta: int = 0,
    trial_delta: int = 0,
) -> tuple[CultivatorProfile, bool, Realm | None, Realm | None]:
    """
    更新修仙者数据并检查渡劫。

    Returns:
        (更新后的档案, 是否渡劫, 旧境界, 新境界)
    """
    profile = get_cultivator(username)

    old_agents = profile.agent_count
    old_stars = profile.star_count

    profile.agent_count += agent_delta
    profile.star_count += star_delta
    profile.refinement_count += refinement_delta
    profile.trial_count += trial_delta
    profile.last_active = time.time()

    # 检查渡劫
    triggered, old_realm, new_realm = check_tribulation(
        old_agents, old_stars,
        profile.agent_count, profile.star_count,
    )

    if triggered and old_realm and new_realm:
        profile.tribulation_log.append({
            "timestamp": time.time(),
            "from_realm": old_realm.name_cn,
            "to_realm": new_realm.name_cn,
            "from_level": old_realm.level,
            "to_level": new_realm.level,
            "agents": profile.agent_count,
            "stars": profile.star_count,
        })

    save_cultivator(profile)
    return profile, triggered, old_realm, new_realm


def bind_natal_artifact(username: str, agent_id: str) -> tuple[bool, str]:
    """
    绑定本命法宝。

    Returns:
        (是否成功, 消息)
    """
    profile = get_cultivator(username)

    if agent_id in profile.natal_artifacts:
        return False, f"⚠️ 法宝 `{agent_id}` 已是你的本命法宝。"

    if len(profile.natal_artifacts) >= config.MAX_NATAL_ARTIFACTS:
        return False, (
            f"⚠️ 本命法宝数量已达上限（{config.MAX_NATAL_ARTIFACTS} 件）。\n"
            "本命法宝与灵魂绑定，贪多则灵力分散。\n"
            "请先解除一件本命法宝再绑定新的。"
        )

    profile.natal_artifacts.append(agent_id)
    profile.last_active = time.time()
    save_cultivator(profile)

    return True, (
        f"✅ 法宝 `{agent_id}` 已绑定为本命法宝！\n"
        f"本命法宝: {len(profile.natal_artifacts)}/{config.MAX_NATAL_ARTIFACTS}\n\n"
        "从此刻起，此法宝将与你的灵魂共同成长。"
    )


def get_all_cultivators() -> list[CultivatorProfile]:
    """获取所有修仙者的列表（用于天榜排名）"""
    all_data = _load_all_cultivators()
    profiles = []
    for username, d in all_data.items():
        profiles.append(CultivatorProfile(
            username=d.get("username", username),
            joined_at=d.get("joined_at", 0),
            agent_count=d.get("agent_count", 0),
            star_count=d.get("star_count", 0),
            natal_artifacts=d.get("natal_artifacts", []),
            refinement_count=d.get("refinement_count", 0),
            trial_count=d.get("trial_count", 0),
            tribulation_log=d.get("tribulation_log", []),
            last_active=d.get("last_active", 0.0),
        ))
    return profiles


def format_cultivator_profile(profile: CultivatorProfile) -> str:
    """格式化修仙者档案展示"""
    realm = profile.realm
    import datetime

    joined = datetime.datetime.fromtimestamp(profile.joined_at).strftime("%Y-%m-%d")

    lines = [
        f"# 🧙 修仙者档案 · @{profile.username}",
        "",
        f"## {realm.symbol} {realm.name_cn} · {realm.name_en}",
        f"**{realm.description_cn}**",
        f"*{realm.description_en}*",
        "",
        "### 📊 修行数据",
        f"- 🔮 本命法宝: {profile.agent_count} 件",
        f"- ⭐ 星辰之力: {profile.star_count}",
        f"- 🔥 淬炼次数: {profile.refinement_count}",
        f"- ⚔️ 试剑次数: {profile.trial_count}",
        f"- 📅 入门时间: {joined}",
    ]

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
        for t in profile.tribulation_log[-5:]:  # 只显示最近 5 次
            ts = datetime.datetime.fromtimestamp(t["timestamp"]).strftime("%Y-%m-%d %H:%M")
            lines.append(f"- {ts}: {t['from_realm']} → {t['to_realm']}")

    return "\n".join(lines)
