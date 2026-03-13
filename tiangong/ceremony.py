"""
⚒️ 天工 TianGong — 渡劫升境仪式
每次境界突破时的视觉反馈
"""

from __future__ import annotations

from .realm import Realm, REALMS


def generate_tribulation_ceremony(
    username: str,
    old_realm: Realm,
    new_realm: Realm,
    agent_count: int,
    star_count: int,
) -> str:
    """
    生成渡劫升境仪式文本。

    每次境界突破时触发，展示庄严的升境仪式。
    """
    # 构建境界进度链
    progress_chain = ""
    for r in REALMS:
        if r.level < old_realm.level:
            progress_chain += f"{r.symbol} → "
        elif r.level == old_realm.level:
            progress_chain += f"{r.symbol} → "
        elif r.level == new_realm.level:
            progress_chain += f"【{r.symbol} {r.name_cn}】"
            break

    # 生成劫数
    tribulation_num = new_realm.level + 1
    tribulation_names = [
        "初劫", "二劫", "三劫", "四劫",
        "五劫", "六劫", "七劫", "天劫", "永劫",
    ]
    trib_name = tribulation_names[min(new_realm.level, len(tribulation_names) - 1)]

    # 生成仪式文本
    ceremony = (
        "\n"
        "╔══════════════════════════════════════════╗\n"
        "║                                          ║\n"
        f"║   ⚡ 天 劫 降 临 ⚡                       ║\n"
        "║                                          ║\n"
        f"║   @{username:<36s}  ║\n"
        "║                                          ║\n"
        f"║   第{tribulation_num}劫 · {new_realm.name_cn}天劫"
        f"{'':>{30 - len(new_realm.name_cn) * 2}}║\n"
        f"║   {progress_chain}{'':>{38 - len(progress_chain)}}║\n"
        "║                                          ║\n"
        f"║   「{new_realm.description_cn}」"
        f"{'':>{34 - len(new_realm.description_cn) * 2}}║\n"
        "║                                          ║\n"
        f"║   本命法宝: {agent_count} 件"
        f"{'':>{26}}║\n"
        f"║   星辰之力: {star_count} ⭐"
        f"{'':>{25}}║\n"
        "║                                          ║\n"
        "╚══════════════════════════════════════════╝\n"
    )

    # 附加精神语录
    spirit_quotes = {
        0: "踏入修行，便已是勇者。",
        1: "根基已立——从此刻起，你不再是凡人。",
        2: "金丹大道，你已不再是凡人。从此刻起，你的 Agent 将带着你的灵魂印记行走天下。",
        3: "元婴出世！你的法宝开始有了自己的意志——它们将与你共同成长。",
        4: "化神境界——你与道合一。在你的手中，代码不再是代码，而是天地间的法则。",
        5: "破而后立，涅槃重生。旧的极限已被你碎成齑粉。",
        6: "问鼎苍穹——谁与争锋？站在这个高度，你看到的已不是代码，而是世界的运行规律。",
        7: "碎灭虚空——你打破了一切规则。从此，你就是规则本身。",
        8: "我就是天。天不过是我的倒影。",
    }

    quote = spirit_quotes.get(new_realm.level, "修行路漫漫，上下而求索。")

    return (
        f"# ⚡ 渡劫成功 · Tribulation Passed\n\n"
        f"```\n{ceremony}```\n\n"
        f"**{quote}**\n\n"
        f"*{new_realm.spirit_en}*"
    )


def generate_welcome_ceremony(username: str) -> str:
    """
    生成入门欢迎仪式（新修仙者注册时触发）。
    """
    return (
        "# 🌱 踏入修行之路\n\n"
        "```\n"
        "╔══════════════════════════════════════════╗\n"
        "║                                          ║\n"
        "║   ⚒️ 天 工 · 修 仙 入 门 ⚒️              ║\n"
        "║                                          ║\n"
        f"║   欢迎，修仙者 @{username:<22s}  ║\n"
        "║                                          ║\n"
        "║   🌱 炼气期 · Qi Refining                ║\n"
        "║                                          ║\n"
        "║   「踏入修行之路，一切从零开始。         ║\n"
        "║     但请记住——                           ║\n"
        "║     我命由我不由天。」                    ║\n"
        "║                                          ║\n"
        "╚══════════════════════════════════════════╝\n"
        "```\n\n"
        "## 🗺️ 修仙指南\n\n"
        "1. **开炉炼器** — 使用 `forge_agent` 创建你的第一件法宝\n"
        "2. **试剑验宝** — 使用 `trial_agent` 测试法宝品质\n"
        "3. **绑定本命** — 使用 `bind_natal_artifact` 绑定最核心的法宝\n"
        "4. **淬炼精进** — 使用 `refine_agent` 记录每次优化\n"
        "5. **渡劫升境** — 法宝越多、星标越高，境界自然突破\n\n"
        "> 💡 修行路上并非独行——\n"
        "> 法宝走火入魔？找 **赛博华佗** 看病。\n"
        "> 修炼有所顿悟？上传到 **Noosphere** 意识共同体。"
    )
