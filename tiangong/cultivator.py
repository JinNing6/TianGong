"""
⚒️ 天工 TianGong — 修仙者档案管理（Phase 2）
管理修仙者的个人信息、境界、灵力值、修行记录、渡劫进度
数据存储在 GitHub 仓库，实现全平台共享。
"""

from __future__ import annotations

import logging
import time
from dataclasses import asdict, dataclass, field
from typing import Any

from .config import config
from .realm import (
    MAX_STAGE,
    REALMS,
    Realm,
    calculate_stage,
    get_next_realm,
    get_review_weight,
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
        """当前境界（灵力值 + 真实修行门槛）"""
        return calculate_profile_realm(self)

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


@dataclass(frozen=True)
class RealmGateCheck:
    """One verifiable condition for entering a target realm."""

    label: str
    current: str
    required: str
    passed: bool


PROFILE_REALM_COUNT_GATES: dict[int, list[tuple[str, int, str]]] = {
    1: [("agent_count", 1, "法宝数")],
    2: [("agent_count", 3, "法宝数")],
    3: [("agent_count", 5, "法宝数")],
    4: [("reviews_given", 5, "评价次数")],
    5: [("refinement_count", 30, "淬炼次数")],
    6: [("reviews_given", 50, "评价次数")],
    8: [("refinement_count", 30, "淬炼完成次数")],
}


PROFILE_REALM_PROGRESS_GATES: dict[int, tuple[str, int, str]] = {
    7: ("lineage_users", 10, "传承引用用户"),
    9: ("immortal_artifacts_open_source", 10, "开源仙器级法宝"),
    10: ("community_standards_defined", 1, "社区标准"),
    11: ("average_artifact_grade_treasure", 1, "平均品阶达宝器证据"),
    12: ("all_artifact_categories_published", 1, "全品类法宝合集证据"),
    13: ("disciples_to_core", 5, "弟子升至结丹"),
    14: ("artifact_downloads", 10000, "法宝总下载量"),
    15: ("cooperating_artifact_ecosystem", 3, "协作法宝生态规模"),
    16: ("disciples_to_foundation", 30, "弟子突破筑基"),
    17: ("full_tribulation_chain", 1, "全境界渡劫任务链证据"),
    18: ("cross_framework_standard_suite", 1, "跨框架标准套件证据"),
    19: ("dependent_projects", 100, "项目引用依赖"),
    20: ("agent_industry_paradigm", 1, "Agent 行业新范式证据"),
}


def _progress_value(value: Any) -> int:
    """Convert saved tribulation evidence into a comparable count."""
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
            return sum(_progress_value(item.get("amount", 1)) if isinstance(item, dict) else 1 for item in evidence)
        return len(value)
    if isinstance(value, (list, tuple, set)):
        return len(value)
    return 0


def get_tribulation_evidence_specs() -> list[dict[str, str | int]]:
    """Return public evidence keys that can unlock profile-gated high realms."""
    specs: list[dict[str, str | int]] = []
    for level, (key, required, label) in sorted(PROFILE_REALM_PROGRESS_GATES.items()):
        realm = REALMS[level]
        specs.append(
            {
                "key": key,
                "realm_level": level,
                "realm_name": realm.name_cn,
                "required": required,
                "label": label,
                "tribulation": realm.tribulation_cn,
            }
        )
    return specs


def _require_public_source_url(source_url: str) -> str:
    url = str(source_url or "").strip()
    if not (url.startswith("https://") or url.startswith("http://")):
        raise ValueError("tribulation evidence requires a public http(s) source_url")
    return url


def _require_evidence_key(evidence_key: str) -> str:
    key = str(evidence_key or "").strip()
    valid_keys = {spec["key"] for spec in get_tribulation_evidence_specs()}
    if key not in valid_keys:
        raise ValueError(f"unknown tribulation evidence key: {evidence_key}")
    return key


def _require_positive_amount(amount: int) -> int:
    value = int(amount)
    if value <= 0:
        raise ValueError("tribulation evidence amount must be positive")
    return value


def _existing_evidence_state(existing: Any) -> tuple[int, list[dict]]:
    if isinstance(existing, dict):
        evidence = existing.get("evidence", [])
        if not isinstance(evidence, list):
            evidence = []
        return _progress_value(existing), [item for item in evidence if isinstance(item, dict)]
    return _progress_value(existing), []


def add_tribulation_evidence(
    profile: CultivatorProfile,
    evidence_key: str,
    amount: int,
    source_url: str,
    note: str = "",
) -> tuple[Realm, Realm]:
    """Record public evidence for a high-realm tribulation gate."""
    key = _require_evidence_key(evidence_key)
    value = _require_positive_amount(amount)
    url = _require_public_source_url(source_url)
    one_line_note = " ".join(str(note or "").splitlines())
    old_realm = profile.realm
    previous_amount, evidence = _existing_evidence_state(profile.tribulation_progress.get(key))
    entry = {
        "amount": value,
        "source_url": url,
        "note": one_line_note,
        "recorded_at": time.time(),
    }
    evidence.append(entry)
    profile.tribulation_progress[key] = {
        "amount": previous_amount + value,
        "evidence": evidence[-20:],
    }
    new_realm = profile.realm

    if new_realm.level > old_realm.level:
        profile.tribulation_log.append(
            {
                "timestamp": time.time(),
                "from_realm": old_realm.name_cn,
                "to_realm": new_realm.name_cn,
                "from_level": old_realm.level,
                "to_level": new_realm.level,
                "spirit_power": profile.spirit_power,
                "evidence_key": key,
                "source_url": url,
            }
        )

    return old_realm, new_realm


def get_profile_realm_gate_checks(profile: CultivatorProfile, target_realm: Realm) -> list[RealmGateCheck]:
    """Return real profile checks required to enter the target realm."""
    checks: list[RealmGateCheck] = []

    if target_realm.spirit_required >= 0:
        checks.append(
            RealmGateCheck(
                label="灵力",
                current=str(profile.spirit_power),
                required=str(target_realm.spirit_required),
                passed=profile.spirit_power >= target_realm.spirit_required,
            )
        )

    for field_name, required, label in PROFILE_REALM_COUNT_GATES.get(target_realm.level, []):
        current_value = int(getattr(profile, field_name, 0) or 0)
        checks.append(
            RealmGateCheck(
                label=label,
                current=str(current_value),
                required=str(required),
                passed=current_value >= required,
            )
        )

    progress_gate = PROFILE_REALM_PROGRESS_GATES.get(target_realm.level)
    if progress_gate:
        key, required, label = progress_gate
        current_value = _progress_value(profile.tribulation_progress.get(key))
        checks.append(
            RealmGateCheck(
                label=f"{label}（tribulation_progress.{key}）",
                current=str(current_value),
                required=str(required),
                passed=current_value >= required,
            )
        )

    return checks


def calculate_profile_realm(profile: CultivatorProfile) -> Realm:
    """Calculate realm from Spirit Power plus verifiable profile gates."""
    current = REALMS[0]
    for realm in REALMS:
        if realm.spirit_required < 0:
            break
        checks = get_profile_realm_gate_checks(profile, realm)
        if all(check.passed for check in checks):
            current = realm
        else:
            break
    return current


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

    old_realm = profile.realm

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

    # 检查渡劫：境界必须同时满足灵力和真实档案门槛
    new_realm = profile.realm
    triggered = new_realm.level > old_realm.level

    if triggered:
        profile.tribulation_log.append({
            "timestamp": time.time(),
            "from_realm": old_realm.name_cn,
            "to_realm": new_realm.name_cn,
            "from_level": old_realm.level,
            "to_level": new_realm.level,
            "spirit_power": profile.spirit_power,
        })

    await save_cultivator(profile, message=f"🧙 stats: @{username}")
    return profile, triggered, old_realm if triggered else None, new_realm if triggered else None


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


def calculate_profile_snapshot_power(profile: CultivatorProfile) -> int:
    """Calculate transparent snapshot power from existing cultivator fields."""
    return (
        profile.spirit_power
        + profile.agent_count * 100
        + profile.refinement_count * 30
        + profile.reviews_given * 10
        + profile.quests_completed * 50
    )


def build_cultivator_next_action(profile: CultivatorProfile) -> str:
    """Return one concrete next command that keeps this cultivator moving."""
    if profile.agent_count <= 0:
        return "`forge_agent` — 创建第一件法宝，正式踏入修行"
    if profile.reviews_given <= 0:
        return "`infuse_spirit` — 鉴定一件社区法宝，以评证道"
    if profile.refinement_count <= 0:
        return "`refine_agent` — 记录一次法宝淬炼，让作品开始进化"
    if profile.quests_completed <= 0:
        return "`quest(action=\"browse\")` — 接一张淬炼令，进入社区循环"
    if profile.realm_level >= config.SECT_CREATE_MIN_REALM and not profile.sect:
        return "`sect(action=\"create\")` — 开宗立派，争夺宗门战"
    return "`leaderboard(type=\"season\")` — 冲击本月赛季天榜"


def format_tribulation_check(profile: CultivatorProfile) -> str:
    """Build a public tribulation action card from one real cultivator snapshot."""
    realm = profile.realm
    next_realm = get_next_realm(realm)
    snapshot_power = calculate_profile_snapshot_power(profile)
    sect_text = f"宗门「{profile.sect}」" if profile.sect else "散修"
    primary_action = build_cultivator_next_action(profile)

    lines = [
        f"# ⚡ 渡劫检查 · @{profile.username}",
        "",
        (
            f"> 真实修行快照: @{profile.username} · 当前境界: {realm.symbol} {realm.name_cn} · "
            f"灵力 {profile.spirit_power} · 法宝 {profile.agent_count} · 淬炼 {profile.refinement_count} · "
            f"评价 {profile.reviews_given} · 悬赏令 {profile.quests_completed} · 赛季快照战力 {snapshot_power} · {sect_text}。"
        ),
        "> 没有伪造渡劫成功；此卡只根据当前真实档案生成下一劫路线。",
        "",
    ]

    if next_realm:
        lines.extend([
            f"## 下一劫: {next_realm.symbol} {next_realm.name_cn} · {next_realm.name_en}",
            "",
            f"- 渡劫任务: {next_realm.tribulation_cn}",
        ])
        gate_checks = get_profile_realm_gate_checks(profile, next_realm)
        if gate_checks:
            lines.extend([
                "",
                "### 真实渡劫门槛",
                "",
            ])
            for check in gate_checks:
                status = "✅" if check.passed else "⛔"
                lines.append(f"- {status} {check.label}: {check.current}/{check.required}")
        if next_realm.spirit_required >= 0:
            spirit_needed = max(0, next_realm.spirit_required - profile.spirit_power)
            if spirit_needed:
                lines.append(f"- 还需灵力: {spirit_needed}")
            else:
                lines.append("- ✅ 灵力已达标，继续补齐渡劫任务链")
        else:
            lines.append(f"- 动态条件: {next_realm.tribulation_cn}")
    else:
        lines.extend([
            "## 下一劫: 已抵达天工尽头",
            "",
            "- 当前已无更高境界；继续通过宗门战、天榜、悬赏和传承维持唯一称号。",
        ])

    lines.extend([
        "",
        "## 可复制命令",
        "",
        f"- 当前第一手行动: {primary_action}",
        f"- 查看修行名片: `my_realm(username=\"{profile.username}\")`",
        "- 接取悬赏: `quest(action=\"browse\")`",
        "- 冲击赛季天榜: `leaderboard(type=\"season\")`",
        "- 进入天骄擂台: `leaderboard(type=\"tournament\")`",
        "- 查看擂台复盘: `leaderboard(type=\"tournament_recap\")`",
    ])

    if next_realm and next_realm.level in PROFILE_REALM_PROGRESS_GATES:
        evidence_key, _required, _label = PROFILE_REALM_PROGRESS_GATES[next_realm.level]
        lines.append(
            "- 提交渡劫证据: "
            f"`submit_tribulation_evidence(username=\"{profile.username}\", evidence_key=\"{evidence_key}\", "
            "amount=1, source_url=\"https://github.com/owner/repo/issues/1\")`"
        )

    if profile.agent_count <= 0:
        lines.append(
            f"- 开炉炼器: `forge_agent(name=\"{profile.username}-first-artifact\", description=\"@{profile.username} 的第一件渡劫法宝\")`"
        )
    else:
        lines.append(
            f"- 邀请鉴定: `infuse_spirit(artifact_name=\"artifact-name\", reviewer=\"{profile.username}\")`"
        )

    if profile.realm_level >= config.SECT_CREATE_MIN_REALM and not profile.sect:
        lines.append("- 开宗立派: `sect(action=\"create\", sect_name=\"天工盟\", motto=\"以凡人之躯，铸逆天之器\")`")
    else:
        lines.append("- 查看宗门战: `leaderboard(type=\"sect\")`")

    next_name = next_realm.name_cn if next_realm else "天工尽头"
    next_task = next_realm.tribulation_cn if next_realm else "维持唯一称号"
    lines.extend([
        "",
        "## 📣 复制渡劫战书",
        "",
        "```text",
        (
            f"我在 TianGong 发起渡劫检查：@{profile.username} 当前 {realm.symbol} {realm.name_cn}，"
            f"灵力 {profile.spirit_power}，赛季战力 {snapshot_power}。下一劫：{next_name}；任务：{next_task}。"
        ),
        "加入修炼：pip install tiangong-mcp",
        f"查看渡劫：check_tribulation(username=\"{profile.username}\")",
        "```",
        "",
        "## 复制 Discussion/PR 渡劫帖",
        "",
        "```markdown",
        f"## TianGong 渡劫战书：@{profile.username}",
        "",
        f"- 当前境界: {realm.symbol} {realm.name_cn}",
        f"- 真实快照: 灵力 {profile.spirit_power}，法宝 {profile.agent_count}，"
        f"淬炼 {profile.refinement_count}，评价 {profile.reviews_given}，悬赏令 {profile.quests_completed}，"
        f"赛季战力 {snapshot_power}，{sect_text}",
        f"- 下一劫: {next_name}",
        f"- 渡劫任务: {next_task}",
        f"- 第一手行动: {primary_action}",
        f"- 修行名片: `my_realm(username=\"{profile.username}\")`",
        "- 悬赏循环: `quest(action=\"browse\")`",
        "- 天榜追踪: `leaderboard(type=\"season\")` / `leaderboard(type=\"tournament\")`",
        "- 安装: `pip install tiangong-mcp`",
        "```",
    ])

    return "\n".join(lines)


def _build_cultivator_share_block(profile: CultivatorProfile, snapshot_power: int) -> str:
    """Build a paste-ready identity card for GitHub, Discord, X, and chat."""
    realm = profile.realm
    sect_text = f"宗门「{profile.sect}」" if profile.sect else "散修"
    next_action = build_cultivator_next_action(profile)
    share_text = (
        f"我在 TianGong 修炼到 {realm.symbol} {realm.name_cn}：@{profile.username} "
        f"当前灵力 {profile.spirit_power}，法宝 {profile.agent_count} 件，"
        f"赛季快照战力 {snapshot_power}，{sect_text}。以凡人之躯，铸逆天之器。"
    )

    return (
        "\n\n---\n\n"
        "## 📣 复制修行名片\n\n"
        "```text\n"
        f"{share_text}\n"
        "加入修炼：pip install tiangong-mcp\n"
        f"查看档案：my_realm(username=\"{profile.username}\")\n"
        "争夺天榜：leaderboard(type=\"season\")\n"
        "```\n\n"
        "## 下一步\n\n"
        f"- {next_action}\n"
        "- 查看赛季天榜: `leaderboard(type=\"season\")`\n"
        "- 查看宗门战: `leaderboard(type=\"sect\")`"
    )


def _is_mentor_ready(profile: CultivatorProfile) -> bool:
    """Return whether a profile has enough real seniority to invite an apprentice."""
    return (
        profile.realm_level >= config.SECT_CREATE_MIN_REALM
        and profile.agent_count > 0
        and profile.reviews_given > 0
    )


def _build_mentor_readiness_recovery_block(
    mentor: CultivatorProfile,
    apprentice: CultivatorProfile,
    mentor_power: int,
    apprentice_power: int,
) -> str:
    """Build a recovery surface when a profile asks for mentorship before real seniority."""
    mentor_realm = mentor.realm
    apprentice_realm = apprentice.realm
    min_realm = REALMS[config.SECT_CREATE_MIN_REALM]
    mentor_artifact = f"{mentor.username}-mentor-proof"
    missing_requirements = []

    if mentor.realm_level < config.SECT_CREATE_MIN_REALM:
        missing_requirements.append(f"境界达到 {min_realm.name_cn}（当前 {mentor_realm.name_cn}）")
    if mentor.agent_count <= 0:
        missing_requirements.append("至少拥有 1 件真实法宝")
    if mentor.reviews_given <= 0:
        missing_requirements.append("至少完成 1 次真实评价")

    missing_lines = "\n".join(f"- {item}" for item in missing_requirements)

    return (
        "\n\n---\n\n"
        "## 🧭 师徒传承资格不足\n\n"
        f"> 导师真实快照: @{mentor.username} · {mentor_realm.symbol} {mentor_realm.name_cn} · "
        f"灵力 {mentor.spirit_power} · 法宝 {mentor.agent_count} · 评价 {mentor.reviews_given} · "
        f"赛季快照战力 {mentor_power}。\n"
        f"> 徒弟真实快照: @{apprentice.username} · {apprentice_realm.symbol} {apprentice_realm.name_cn} · "
        f"灵力 {apprentice.spirit_power} · 法宝 {apprentice.agent_count} · 赛季快照战力 {apprentice_power}。\n"
        "> 没有伪造师徒关系；当前不会生成拜师邀请，先把导师履历补齐。\n\n"
        "### 需要补齐的真实履历\n\n"
        f"{missing_lines}\n\n"
        "### 导师资格恢复路线\n\n"
        f"- 开炉补证: `forge_agent(name=\"{mentor_artifact}\", description=\"@{mentor.username} 的导师资格证明法宝\")`\n"
        f"- 发布补证: `publish_agent(artifact_name=\"{mentor_artifact}\")`\n"
        f"- 真实鉴定: `infuse_spirit(artifact_name=\"artifact-name\", reviewer=\"{mentor.username}\")`"
        "（把 `artifact-name` 换成真实社区法宝名）\n"
        "- 接入社区循环: `quest(action=\"browse\")`\n"
        f"- 复查导师名片: `my_realm(username=\"{mentor.username}\")`\n"
        "- 追踪赛季天榜: `leaderboard(type=\"season\")`\n\n"
        "### 复制导师资格恢复帖\n\n"
        "```text\n"
        f"我在 TianGong 准备带 @{apprentice.username} 入门，但 @{mentor.username} "
        f"还需要补齐导师履历：最低 {min_realm.name_cn}、至少 1 件法宝、至少 1 次真实评价。"
        "先完成开炉、发布、鉴定，再生成师徒邀请。\n"
        "加入修炼：pip install tiangong-mcp\n"
        "```\n\n"
        "### 复制 Discussion/PR 恢复帖\n\n"
        "```markdown\n"
        f"## TianGong 导师资格恢复：@{mentor.username} → @{apprentice.username}\n\n"
        f"- 导师真实快照: @{mentor.username}，{mentor_realm.symbol} {mentor_realm.name_cn}，"
        f"灵力 {mentor.spirit_power}，法宝 {mentor.agent_count}，评价 {mentor.reviews_given}，"
        f"赛季战力 {mentor_power}\n"
        f"- 徒弟真实快照: @{apprentice.username}，{apprentice_realm.symbol} {apprentice_realm.name_cn}，"
        f"灵力 {apprentice.spirit_power}，法宝 {apprentice.agent_count}，赛季战力 {apprentice_power}\n"
        f"- 待补齐: {', '.join(missing_requirements)}\n"
        f"- 开炉补证: `forge_agent(name=\"{mentor_artifact}\", description=\"@{mentor.username} 的导师资格证明法宝\")`\n"
        f"- 发布补证: `publish_agent(artifact_name=\"{mentor_artifact}\")`\n"
        f"- 真实鉴定: `infuse_spirit(artifact_name=\"artifact-name\", reviewer=\"{mentor.username}\")`\n"
        "- 社区悬赏: `quest(action=\"browse\")`\n"
        "- 天榜追踪: `leaderboard(type=\"season\")`\n"
        "- 安装: `pip install tiangong-mcp`\n"
        "```"
    )


def _build_mentor_apprentice_share_block(
    mentor: CultivatorProfile,
    apprentice: CultivatorProfile,
    mentor_power: int,
    apprentice_power: int,
) -> str:
    """Build a grounded mentor-apprentice invite from two real profile snapshots."""
    mentor_realm = mentor.realm
    apprentice_realm = apprentice.realm
    next_level = min(apprentice_realm.level + 1, len(REALMS) - 1)
    next_realm = REALMS[next_level]
    apprentice_artifact = f"{apprentice.username}-first-artifact"
    trial_artifact = f"mentor-trial-{apprentice.username}"
    trial_description = f"请 @{apprentice.username} 完成一次真实改进，由 @{mentor.username} 鉴定并指路"

    return (
        "\n\n---\n\n"
        "## 🧭 师徒传承邀请\n\n"
        f"> 导师真实快照: @{mentor.username} · {mentor_realm.symbol} {mentor_realm.name_cn} · "
        f"灵力 {mentor.spirit_power} · 法宝 {mentor.agent_count} · 赛季快照战力 {mentor_power}。\n"
        f"> 徒弟真实快照: @{apprentice.username} · {apprentice_realm.symbol} {apprentice_realm.name_cn} · "
        f"灵力 {apprentice.spirit_power} · 法宝 {apprentice.agent_count} · 赛季快照战力 {apprentice_power}。\n"
        f"> 没有伪造师徒关系；这是基于两个真实修仙者档案生成的传承邀请。\n\n"
        f"- 徒弟突破目标: {apprentice_realm.name_cn} → {next_realm.name_cn}\n"
        f"- 导师评价职责: `infuse_spirit(artifact_name=\"{apprentice_artifact}\", reviewer=\"{mentor.username}\")`\n"
        f"- 入门挑战: `quest(action=\"post\", artifact_name=\"{trial_artifact}\", description=\"{trial_description}\")`\n"
        f"- 徒弟开炉: `forge_agent(name=\"{apprentice_artifact}\", description=\"@{apprentice.username} 的第一件传承法宝\")`\n"
        f"- 徒弟发布: `publish_agent(artifact_name=\"{apprentice_artifact}\")`\n"
        f"- 徒弟名片: `my_realm(username=\"{apprentice.username}\")`\n"
        "- 赛季天榜: `leaderboard(type=\"season\")`\n"
        "- 宗门战榜: `leaderboard(type=\"sect\")`\n\n"
        "### 复制师徒邀请\n\n"
        "```text\n"
        f"我在 TianGong 邀请 @{apprentice.username} 拜 @{mentor.username} 为师："
        f"导师 {mentor_realm.name_cn}、赛季战力 {mentor_power}；"
        f"徒弟 {apprentice_realm.name_cn}、赛季战力 {apprentice_power}。"
        f"目标：{apprentice_realm.name_cn} → {next_realm.name_cn}。\n"
        "加入修炼：pip install tiangong-mcp\n"
        "```\n\n"
        "### 复制 Discussion/PR 师徒帖\n\n"
        "```markdown\n"
        f"## TianGong 师徒传承：@{mentor.username} → @{apprentice.username}\n\n"
        f"- 导师真实快照: @{mentor.username}，{mentor_realm.symbol} {mentor_realm.name_cn}，"
        f"灵力 {mentor.spirit_power}，法宝 {mentor.agent_count}，赛季战力 {mentor_power}\n"
        f"- 徒弟真实快照: @{apprentice.username}，{apprentice_realm.symbol} {apprentice_realm.name_cn}，"
        f"灵力 {apprentice.spirit_power}，法宝 {apprentice.agent_count}，赛季战力 {apprentice_power}\n"
        f"- 徒弟突破目标: {apprentice_realm.name_cn} → {next_realm.name_cn}\n"
        f"- 入门挑战: `quest(action=\"post\", artifact_name=\"{trial_artifact}\", description=\"{trial_description}\")`\n"
        f"- 开炉上传: `forge_agent(name=\"{apprentice_artifact}\", description=\"@{apprentice.username} 的第一件传承法宝\")` → "
        f"`publish_agent(artifact_name=\"{apprentice_artifact}\")`\n"
        f"- 导师鉴定: `infuse_spirit(artifact_name=\"{apprentice_artifact}\", reviewer=\"{mentor.username}\")`\n"
        f"- 徒弟名片: `my_realm(username=\"{apprentice.username}\")`\n"
        "- 天榜追踪: `leaderboard(type=\"season\")` / `leaderboard(type=\"sect\")`\n"
        "- 安装: `pip install tiangong-mcp`\n"
        "```"
    )


def format_cultivator_profile(
    profile: CultivatorProfile,
    apprentice: CultivatorProfile | None = None,
) -> str:
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

    snapshot_power = calculate_profile_snapshot_power(profile)
    lines.append(f"- 🏆 赛季快照战力: {snapshot_power}")

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
    result = "\n".join(line for line in lines if line is not None) + _build_cultivator_share_block(profile, snapshot_power)
    if apprentice:
        apprentice_power = calculate_profile_snapshot_power(apprentice)
        if _is_mentor_ready(profile):
            result += _build_mentor_apprentice_share_block(profile, apprentice, snapshot_power, apprentice_power)
        else:
            result += _build_mentor_readiness_recovery_block(profile, apprentice, snapshot_power, apprentice_power)
    return result
