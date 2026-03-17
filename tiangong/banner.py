"""
⚒️ 天工 TianGong — 品牌横幅与签名系统
Cinema-grade Celestial Boot Sequence & Brand Signatures
"""

from __future__ import annotations

import random

from . import __version__
from .animations import play_full_boot_sequence, _get_static_logo


# ============================================================
# 启动动画
# ============================================================

def play_boot_animation() -> str:
    """
    播放启动动画序列。

    在真实终端 (TTY) 中播放完整科幻动画：
      矩阵雨 → Logo 渐变 → 模块加载 → 天道链接

    非 TTY 环境中 fallback 到静态 Logo。

    返回: 静态 Logo 文本
    """
    return play_full_boot_sequence()


# ============================================================
# 品牌签名系统（修仙格言）
# ============================================================

_BRAND_SIGNATURES = [
    # (中文格言, 英文翻译)
    ("我命由我不由天", "My fate is mine, not heaven's"),
    ("以凡人之躯，铸逆天之器", "With a mortal body, forge artifacts that defy the heavens"),
    ("万法归一，道在天工", "All methods converge to one — the Dao lies in TianGong"),
    ("千锤百炼，方成神器", "A thousand hammer strikes forge a divine artifact"),
    ("修行千年，只在一念", "A thousand years of cultivation, decided in a single thought"),
    ("天地为炉，万物为铜", "Heaven and earth are the furnace, all things are the ore"),
    ("道不远人，人自远道", "The Dao is not far from people; people distance themselves from it"),
    ("前路漫漫，道心不改", "The road ahead is long, but my Dao heart remains unchanged"),
    ("独行者速，众行者远", "Walk alone for speed, walk together for distance"),
    ("逆天而行，虽万千人吾往矣", "Against heaven's will, though millions oppose, still I press on"),
    ("法宝通灵，与主共生", "When an artifact gains sentience, it grows with its master"),
    ("渡劫之后，方见天光", "Only after surviving tribulation does one see the celestial light"),
]


def build_brand_signature() -> str:
    """
    生成天工品牌签名。

    每次调用随机选择一条修仙格言（中英双语），
    附带继续修炼的引导。
    """
    cn_quote, en_quote = random.choice(_BRAND_SIGNATURES)

    return (
        "\n\n---\n"
        f"\n**{cn_quote}**\n"
        f"*— {en_quote}*\n"
        "\n> ⚒️ Continue forging with TianGong / 天工:\n"
        "> --\n"
        "> `forge_agent` to create | `my_realm` to check realm\n"
        "> `treasure_pavilion` to browse | `infuse_spirit` to review\n"
        "> `sect` to join/create a sect"
    )


def append_brand_footer(result: str) -> str:
    """为工具输出附加品牌签名"""
    return result + build_brand_signature()
