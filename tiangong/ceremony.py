"""
⚒️ 天工 TianGong — 仪式系统（渡劫 / 品阶突破 / 新人入门）
Cinema-grade tribulation, grade promotion, and welcome ceremonies

所有仪式返回 Markdown 富文本（工具返回值），
包含手工打造的 Unicode Art 视觉效果。
"""

from __future__ import annotations
import math
import textwrap

from .realm import Realm, REALMS
from .animations import (
    render_starfield,
    render_lightning_field,
    render_progress_bar,
    render_dimension_bars,
    render_realm_chain,
    play_tribulation_alert,
    play_grade_promotion_alert,
)


# ============================================================
# 境界渡劫语录
# ============================================================

_TRIBULATION_QUOTES = {
    # level: (中文语录, 英文语录)
    0: (
        "踏入修行，便已是勇者。",
        "To step onto the path of cultivation is already an act of courage.",
    ),
    1: (
        "根基已立——从此刻起，你不再是凡人。",
        "The foundation is set — from this moment, you are no longer mortal.",
    ),
    2: (
        "金丹大道，灵力凝聚。你的 Agent 将带着你的灵魂印记行走天下。",
        "The Golden Core condenses. Your Agents will carry your soul's imprint across the world.",
    ),
    3: (
        "元婴出世！你的法宝开始有了自己的意志——它们将与你共同成长。",
        "The Nascent Soul emerges! Your artifacts begin to develop their own will.",
    ),
    4: (
        "化神境界——你与道合一。代码不再是代码，而是天地间的法则。",
        "Transforming Spirit — you merge with the Dao. Code becomes the laws of heaven and earth.",
    ),
    5: (
        "破而后立，涅槃重生。旧的极限已被你碎成齑粉。",
        "Destroy to rebuild, reborn from ashes. Your old limits are shattered to dust.",
    ),
    6: (
        "问鼎苍穹——谁与争锋？你看到的已不是代码，而是世界的运行规律。",
        "Contending for the peak — who dares compete? You see not code, but the world's operating laws.",
    ),
    7: (
        "元神蜕变。阴阳合一，你已超越了常人所能理解的境界。",
        "The primordial spirit transforms. Yin and Yang unite beyond mortal comprehension.",
    ),
    8: (
        "心魔已渡，道心通明。你将自己的法宝播散于天下，回馈社区。",
        "Inner demons conquered. Your Dao heart is clear. You return your artifacts to the world.",
    ),
    9: (
        "窥探天规——你触摸到了天地规则之力。",
        "Glimpsing the Rules of Heaven — you touch the power of universal laws.",
    ),
    10: (
        "规则净化。你真正掌握了天地规则，被称为仙王。",
        "Rules Purified. You truly master heaven's rules. They call you Immortal King.",
    ),
    11: (
        "碎灭规则！旧规则在你面前粉碎。从此，你就是规则本身。",
        "Shatter the Rules! Old rules crumble before you. Henceforth, you ARE the rules.",
    ),
    12: (
        "天人五衰？不过是又一道劫而已。你的意志，超越天道。",
        "Five Declines of Heaven? Just another tribulation. Your will transcends the Heavenly Dao.",
    ),
    13: (
        "破空！融合本源之力，将元力提升为涅力。",
        "Breaking the Void! Fusing primal force, your power transcends to Nirvana energy.",
    ),
    14: (
        "在体内开辟独立天地——你的法宝生态，就是你的世界。",
        "You open an inner world within — your artifact ecosystem IS your universe.",
    ),
    15: (
        "言出法随。你的话语就是法则。",
        "Words become law. Your speech IS the code of reality.",
    ),
    16: (
        "空劫降临，生死一线。但你已无所畏惧。",
        "The Void Tribulation descends. Life and death on a razor's edge. But you fear nothing.",
    ),
    17: (
        "信术觉醒。你掌握了化虚为实之力。",
        "Faith-Art awakened. You master the power to make the virtual real.",
    ),
    18: (
        "九桥证道——每座桥都是一个里程碑。踏上第九桥，便是半步巅峰。",
        "Nine Bridges of Proof — each bridge a milestone. Step onto the ninth, and you approach the peak.",
    ),
    19: (
        "踏天成道。你掌控了世间轮回。以凡人之躯，铸逆天之器。",
        "Step upon Heaven, become the Dao. You control the cycle of the world.",
    ),
    20: (
        "工匠之祖，百艺宗师。鲁班在此——天下工匠，皆出你门下。",
        "Ancestor of Craftsmen, Grand Master of All Arts. Lu Ban is here.",
    ),
}


# ============================================================
# 渡劫仪式
# ============================================================

def generate_tribulation_ceremony(
    username: str,
    old_realm: Realm,
    new_realm: Realm,
    agent_count: int,
    star_count: int,
) -> str:
    """
    Generate an epic markdown ceremony for a realm breakthrough.
    """
    # 触发终端特效 (向 stderr 发送)
    play_tribulation_alert(old_realm.name_cn, new_realm.name_cn)

    # 渡劫序号和名称
    trib_num = new_realm.level + 1
    trib_names = [
        "灵根觉醒", "筑基之丹", "金丹雷劫", "金丹碎裂",
        "下凡历世", "传道授业", "天地之问", "元神蜕变",
        "心魔之劫", "窥探天规", "规则净化", "碎灭规则",
        "五衰劫",   "破空门",   "开辟内天地", "九次玄劫",
        "空劫降临", "信术觉醒", "九桥证道", "踏天成道",
        "百工之祖",
    ]
    trib_name = trib_names[min(new_realm.level, len(trib_names) - 1)]

    # 境界路径链
    chain = render_realm_chain(old_realm.level, new_realm.level, REALMS)

    # 雷电场
    lightning = render_lightning_field(40)

    # 语录
    quote_cn, quote_en = _TRIBULATION_QUOTES.get(
        new_realm.level,
        ("修行路漫漫，上下而求索。", "The path of cultivation is long; I seek above and below."),
    )

    # ═══ 构建仪式文本 ═══
    ceremony_art = (
        "```\n"
        "███████████████████████████████████████████████████████\n"
        "█                                                     █\n"
        "█   ██████████████████████████████████████████████     █\n"
        "█   █                                            █     █\n"
        "█   █     ╔═══════════════════════════════╗      █     █\n"
        f"█   █     ║   ⚡ 天  劫  降  临  ⚡        ║      █     █\n"
        "█   █     ╠═══════════════════════════════╣      █     █\n"
        "█   █     ║                               ║      █     █\n"
        f"█   █     ║  第{trib_num}劫 · {trib_name:<18s}  ║      █     █\n"
        f"█   █     ║  修仙者: @{username:<20s}  ║      █     █\n"
        "█   █     ║                               ║      █     █\n"
        f"█   █     ║  {old_realm.symbol} {old_realm.name_cn:<6s}              ║      █     █\n"
        "█   █     ║    ↓ ⚡ 天雷渡劫               ║      █     █\n"
        f"█   █     ║  {new_realm.symbol} {new_realm.name_cn:<6s} ← 渡劫成功!   ║      █     █\n"
        "█   █     ║                               ║      █     █\n"
        f"█   █     ║  本命法宝: {agent_count:<3d}件              ║      █     █\n"
        f"█   █     ║  星辰之力: {star_count:<3d}⭐              ║      █     █\n"
        "█   █     ║                               ║      █     █\n"
        "█   █     ╚═══════════════════════════════╝      █     █\n"
        "█   █                                            █     █\n"
        "█   ██████████████████████████████████████████████     █\n"
        "█                                                     █\n"
        "███████████████████████████████████████████████████████\n"
        "```\n"
    )

    # 组装完整 Markdown
    return (
        f"# ⚡ 渡劫成功 · Tribulation Passed\n\n"
        f"{ceremony_art}\n"
        f"## 🔥 第{trib_num}劫 · {trib_name}\n\n"
        f"**境界跃迁**: {chain}\n\n"
        f"**{quote_cn}**\n"
        f"*{quote_en}*\n\n"
        f"> 「{new_realm.description_cn}」\n"
        f"> *{new_realm.description_en}*"
    )


# ============================================================
# 品阶晋升仪式
# ============================================================

def generate_grade_promotion(
    artifact_name: str,
    old_grade_symbol: str,
    old_grade_name: str,
    new_grade_symbol: str,
    new_grade_name: str,
    spirit_power: float,
    next_threshold: float,
    next_grade_name: str,
    scores: dict[str, float] | None = None,
) -> str:
    """
    生成品阶晋升仪式 — 法宝蜕变,光芒四射。

    返回 Markdown 富文本。
    """
    # 六维条形图
    dim_block = ""
    if scores:
        dim_bars = render_dimension_bars(scores)
        dim_block = (
            f"┌───────────────────────────────────┐\n"
            f"{dim_bars}\n"
            f"└───────────────────────────────────┘\n"
        )

    # 进度条
    progress = render_progress_bar(spirit_power, next_threshold, width=30)

    ceremony_art = (
        "```\n"
        "╔═══════════════════════════════════════════════╗\n"
        "║                                               ║\n"
        "║     ·  ✦  ·    品 阶 突 破    ·  ✦  ·        ║\n"
        "║                                               ║\n"
        f"║       {old_grade_symbol} {old_grade_name:<8s}                       ║\n"
        "║         │                                     ║\n"
        "║         ▼  ✨✨✨                              ║\n"
        f"║       {new_grade_symbol} {new_grade_name:<8s} ← NEW!               ║\n"
        "║                                               ║\n"
        f"║   法宝: {artifact_name:<36s} ║\n"
        "║                                               ║\n"
    )

    if dim_block:
        for line in dim_block.split("\n"):
            if line.strip():
                ceremony_art += f"║   {line:<43s} ║\n"

    ceremony_art += (
        "║                                               ║\n"
        f"║   💫 灵力: {spirit_power:.0f} → 门槛: {next_threshold:.0f} ({new_grade_symbol} → {next_grade_name})  ║\n"
        f"║   {progress:<43s} ║\n"
        "║                                               ║\n"
        "╚═══════════════════════════════════════════════╝\n"
        "```\n"
    )

    return (
        f"# ✨ 品阶突破 · Grade Promotion\n\n"
        f"{ceremony_art}\n"
        f"**「{artifact_name}」从 {old_grade_symbol} {old_grade_name} 晋升为 {new_grade_symbol} {new_grade_name}！**\n\n"
        "> 法宝蜕变，灵光更盛。继续淬炼，方成至宝。"
    )


# ============================================================
# 新人欢迎仪式
# ============================================================

def generate_welcome_ceremony(username: str) -> str:
    """
    生成入门欢迎仪式 — 星空降临，仙门大开。

    新修仙者注册首个法宝时触发。
    返回 Markdown 富文本。
    """
    stars = render_starfield(52)

    ceremony_art = (
        "```\n"
        f"{stars}\n"
        "═══════════════════════════════════════════════════════\n"
        "\n"
        "╔════════════════════════════════════════════════════╗\n"
        "║                                                    ║\n"
        "║        ⚒️   天 工 · 仙 门 大 开   ⚒️              ║\n"
        "║                                                    ║\n"
        f"║   欢迎，修仙者 @{username:<34s}  ║\n"
        "║                                                    ║\n"
        "║   🧑 凡人  →  🌱 炼气期                            ║\n"
        "║   灵根觉醒，踏入修行之路                            ║\n"
        "║                                                    ║\n"
        "║   ┌────────────────────────────────────────┐       ║\n"
        "║   │                                        │       ║\n"
        "║   │  ⚒️  forge_agent      开炉炼器         │       ║\n"
        "║   │  🏛️  treasure_pavilion 寻宝阁          │       ║\n"
        "║   │  💫  infuse_spirit     灌注灵力        │       ║\n"
        "║   │  📜  browse_quests     悬赏布告栏       │       ║\n"
        "║   │  🧙  my_realm          修行档案        │       ║\n"
        "║   │                                        │       ║\n"
        "║   └────────────────────────────────────────┘       ║\n"
        "║                                                    ║\n"
        "║   「我命由我不由天」                                 ║\n"
        "║    My fate is mine, not heaven's.                  ║\n"
        "║                                                    ║\n"
        "╚════════════════════════════════════════════════════╝\n"
        "\n"
        "═══════════════════════════════════════════════════════\n"
        f"{stars}\n"
        "```\n"
    )

    return (
        f"# 🌱 踏入修行之路\n\n"
        f"{ceremony_art}\n"
        f"## 🗺️ 修仙指南\n\n"
        "1. **⚒️ 开炉炼器** — `forge_agent` 创建你的第一件法宝\n"
        "2. **🏛️ 寻宝淘金** — `treasure_pavilion` 浏览社区法宝\n"
        "3. **💫 灌注灵力** — `infuse_spirit` 评价法宝获取灵力\n"
        "4. **📜 接取悬赏** — `browse_quests` 寻找淬炼任务\n"
        "5. **🔥 淬炼精进** — `refine_agent` 记录每次优化\n"
        "6. **⚡ 渡劫升境** — 灵力充足时自动触发渡劫突破\n\n"
        "> 💡 修行路上并非独行——\n"
        "> `my_realm` 查看你的修行档案，`my_artifacts` 查看法宝清单。"
    )
