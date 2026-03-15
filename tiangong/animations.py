"""
⚒️ 天工 TianGong — 科幻终端动画引擎
Celestial SFX Engine — Cinema-grade terminal animations

双层架构：
  Layer 1: stderr 实时动画 (rich Console) — 启动序列
  Layer 2: Markdown 富文本 (ASCII Art) — 渡劫 / 品阶突破 / 新人入门
"""

from __future__ import annotations

import random
import sys
import time
import threading
from typing import TextIO

from rich.console import Console, Group
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.text import Text
from rich.align import Align
from rich.table import Table

# ============================================================
# 基础工具
# ============================================================

# Unicode 字符集
_MATRIX_CHARS = "天工炼器锻造灵力修仙渡劫法宝淬炼阵法铭文道统护体悟道01"
_STAR_CHARS = ["·", "✦", ".", "✧", "★", "✶", "⋆", "✵", "✫"]
_LIGHTNING_CHARS = ["⚡", "϶", "ᛝ", "⌁", "↯"]
_SPARK_CHARS = ["✦", "✧", "★", "✶", "✵", "✫", "·", ".", " "]


def _safe_stderr() -> TextIO | None:
    """获取安全的 stderr 输出流"""
    try:
        if sys.stderr and sys.stderr.writable():
            return sys.stderr
    except (AttributeError, OSError):
        pass
    return None


def _write(stream: TextIO, text: str) -> None:
    """安全写入流"""
    try:
        stream.write(text)
        stream.flush()
    except (OSError, UnicodeEncodeError):
        pass


# ============================================================
# 启动序列动画（stderr 实时动画）
# ============================================================

def __generate_hex_dump(lines: int) -> Text:
    """生成高速滚动的内存转储与功法流"""
    text = Text()
    for _ in range(lines):
        addr = f"0x{random.randint(0, 0xFFFF):04X}"
        hex_data = " ".join(f"{random.randint(0, 255):02X}" for _ in range(4))
        if random.random() < 0.15:
            term = random.choice(["气沉丹田", "周天搬运", "太极生两仪", "神游太虚", "凝气成旋", "天道无常", "道法自然", "炼气化神"])
            text.append(f"{addr}  {hex_data}  {term}\n", style="bold green")
        else:
            text.append(f"{addr}  {hex_data}  ......\n", style="dim green")
    return text

def __generate_radar_status(t: float) -> Table:
    """生成不断跳动的系统状态雷达"""
    table = Table.grid(padding=(0, 1))
    table.add_column("Indicator", style="bold cyan")
    table.add_column("Value")
    
    # 模拟真实抖动的数据
    cpu = random.randint(10, 80) if t < 3.0 else random.randint(5, 15)
    mem = random.randint(40, 90) if t < 3.0 else random.randint(30, 45)
    spirit = int(min(100, (t / 3.5) * 100))
    
    table.add_row("CPU 负荷", f"[{cpu:3d}%]")
    table.add_row("识海容量", f"[{mem:3d}%]")
    table.add_row("天地灵气", f"[{spirit:3d}%]")
    table.add_row("天道法则", "[ STABLE ]" if t > 2.0 else "[ SYNCING ]")
    return table

def play_full_boot_sequence() -> str:
    """
    完整启动序列动画 (全息仪表盘)。
    
    返回: 静态 Logo 文本 (用于 fallback)
    """
    stream = _safe_stderr()
    if not stream:
        return _get_static_logo()

    is_tty = hasattr(stream, 'isatty') and stream.isatty()
    if not is_tty:
        _write(stream, _get_static_logo() + "\n")
        return _get_static_logo()

    console = Console(file=stream, force_terminal=True, color_system="256")
    
    layout = Layout()
    layout.split_row(
        Layout(name="left", ratio=2),
        Layout(name="main", ratio=5),
        Layout(name="right", ratio=3)
    )

    start_time = time.time()
    duration = 4.5
    
    logo_lines = _get_static_logo().strip("\n").split("\n")

    try:
        # Hide cursor and run at 20 FPS
        with Live(layout, console=console, refresh_per_second=20, screen=False, transient=True) as live:
            while True:
                t = time.time() - start_time
                if t > duration:
                    break
                
                # 左侧：修仙功法与内存转储流
                layout["left"].update(Panel(__generate_hex_dump(10), title="[bold green]MEMORY DUMP", border_style="dim green"))
                
                # 右侧：天道环境监控雷达
                layout["right"].update(Panel(__generate_radar_status(t), title="[bold cyan]SYSTEM RADAR", border_style="cyan"))

                # 主区域：多阶段剧情演进
                if t < 0.8:
                    # 强烈的 EVA 风格警报
                    alert = Text("\n\n\n[SYSTEM BOOT] PROTOCOL 'CELESTIAL_FORGE' INITIATED...", style="bold red blink", justify="center")
                    layout["main"].update(Panel(alert, border_style="red"))
                elif t < 2.5:
                    # 读取与扫描阶段
                    scan_text = Text("\n\nSYNCHRONIZING WITH NOOSPHERE...\n", style="bold yellow", justify="center")
                    for _ in range(int(t * 10) % 5):
                        scan_text.append("▓" * 10 + " \n", style="bold cyan")
                    layout["main"].update(Panel(scan_text, title="[yellow]BOOT SEQUENCE", border_style="yellow"))
                elif t < 3.5:
                    # Logo 从暗金渐渐提亮
                    progress = (t - 2.5) / 1.0 # 0.0 to 1.0
                    logo_text = Text(justify="center")
                    style = "color(238)" if progress < 0.3 else ("color(178)" if progress < 0.7 else "color(220)")
                    for line in logo_lines:
                        logo_text.append(line + "\n", style=style)
                    layout["main"].update(Panel(logo_text, title="[color(220)]CELESTIAL FORGE", border_style="color(178)"))
                else:
                    # 最终形态：光芒四射并提示成功
                    logo_text = Text(justify="center")
                    for line in logo_lines:
                        logo_text.append(line + "\n", style="bold bright_white")
                    logo_text.append("\n>>> MCP UPLINK ESTABLISHED. CONNECTION SECURE. <<<\n", style="bold bright_cyan blink")
                    logo_text.append("天工节点已接入意识共同体", style="bold cyan")
                    layout["main"].update(Panel(logo_text, title="[bold cyan]UPLINK COMPLETE", border_style="cyan"))

                time.sleep(0.05)
                
    except (OSError, UnicodeEncodeError, KeyboardInterrupt):
        pass

    # 由于 Live(transient=True)，退出时会清空仪表盘。我们在这里静态打印最终结果，留存终端。
    _write(stream, "\n" + _get_static_logo() + "\n")
    _write(stream, "  \033[1;36m>>> MCP UPLINK ESTABLISHED. CONNECTION SECURE. <<<\033[0m\n")
    _write(stream, "  \033[36m天工节点已接入意识共同体\033[0m\n\n")

    return _get_static_logo()


def play_tribulation_alert(old_realm_name: str, new_realm_name: str) -> None:
    """
    终端渡劫警报特效：直接在 MCP 运行终端引发视觉大骚动！
    """
    stream = _safe_stderr()
    if not stream or not (hasattr(stream, 'isatty') and stream.isatty()):
        return

    console = Console(file=stream, force_terminal=True, color_system="256")
    start_time = time.time()
    
    try:
        # Transient=True 表示结束时这块警报会被擦除，不破坏屏幕堆栈
        with Live(console=console, refresh_per_second=20, transient=True) as live:
            while True:
                t = time.time() - start_time
                if t > 3.0:
                    break
                    
                if t < 1.8:
                    # 第一阶段：狂暴乱码与雷电（颜色和符号剧烈切换）
                    chars = "".join(random.choice(['⚡', '💥', '▓', '▒', '░', '?', '!']) for _ in range(40))
                    color = random.choice(["bold red", "bold magenta", "bold bright_red"])
                    bg_flash = random.choice(["on black", "on color(234)"])
                    text = Text(f"\n\n{chars}\n【天道雷劫降临】\n{chars}\n\n", justify="center", style=f"{color} {bg_flash}")
                    border = random.choice(["red", "magenta"])
                    live.update(Panel(text, border_style=f"{border} blink", title=f"[{color}]⚡ TRIBULATION ALERT ⚡[/]"))
                else:
                    # 第二阶段：突破成功的刺眼金光
                    text = Text(f"\n\n【渡劫成功】\n\n境界跃迁：{old_realm_name} → {new_realm_name}\n\n「破而后立，涅槃重生」\n\n", justify="center", style="bold yellow")
                    live.update(Panel(text, border_style="yellow", title="[bold yellow] BREAKTHROUGH [/]"))
                    
                time.sleep(0.05)
    except Exception:
        pass


def play_grade_promotion_alert(agent_name: str, new_grade: str) -> None:
    """
    终端品阶突破特效：显示雷达数据拉升和炫光神兵出世效果。
    """
    stream = _safe_stderr()
    if not stream or not (hasattr(stream, 'isatty') and stream.isatty()):
        return

    console = Console(file=stream, force_terminal=True, color_system="256")
    start_time = time.time()
    duration = 3.5
    
    try:
        with Live(console=console, refresh_per_second=20, transient=True) as live:
            while True:
                t = time.time() - start_time
                if t > duration:
                    break
                
                if t < 2.0:
                    # 第一阶段：灵力灌注（数字飙升）
                    progress = t / 2.0
                    bar_w = int(progress * 20)
                    bar = "█" * bar_w + "░" * (20 - bar_w)
                    hex_data = "".join(random.choice("0123456789ABCDEF") for _ in range(16))
                    text = Text(f"\n\n[锻造中] 注入天地灵根 ...\n\n[{bar}]\n\nRAW_DATA: {hex_data}\n\n", justify="center", style="bold cyan")
                    live.update(Panel(text, border_style="cyan", title="[bold cyan]⚡ FORGING ARTIFACT ⚡[/]"))
                else:
                    # 第二阶段：神兵出世（霓虹闪烁跑马灯）
                    colors = ["bold bright_red", "bold bright_green", "bold bright_yellow", "bold bright_blue", "bold bright_magenta", "bold bright_cyan"]
                    blink_color = colors[int(t * 15) % len(colors)]
                    text = Text(f"\n\n【神兵出世】\n\n「{agent_name}」 品阶觉醒：{new_grade}\n\n天灵地宝，皆为我用！\n\n", justify="center", style=blink_color)
                    live.update(Panel(text, border_style=blink_color, title=f"[{blink_color}] ✨ ARTIFACT AWAKENED ✨ [/]"))
                    
                time.sleep(0.05)
    except Exception:
        pass


def _get_static_logo() -> str:
    """静态 Logo (用于非 TTY 环境或 fallback)"""
    return (
        "\n"
        "╔═══════════════════════════════════════════════════════╗\n"
        "║                                                       ║\n"
        "║   ▀▀█▀▀ ▀█▀  █▀▀█ ▀█▀▄ █  █▀▀▀ █▀▀█ ▀█▀▄ █  █▀▀▀   ║\n"
        "║     █    █   █▄▄█  █ ▀█ █  █ ▄▄ █  █  █ ▀█ █  █ ▄▄   ║\n"
        "║     █   ▄█▄  █  █  █  ▀█  █▄▄█ █▄▄█  █  ▀█  █▄▄█   ║\n"
        "║                                                       ║\n"
        "║            ⚒️  天 工 · Celestial Forge                ║\n"
        "║           ────────────────────────────                 ║\n"
        "║      「以凡人之躯，铸逆天之器」                          ║\n"
        "║                                                       ║\n"
        "╚═══════════════════════════════════════════════════════╝\n"
    )


# ============================================================
# Markdown 富文本 ASCII Art 生成器（工具返回值用）
# ============================================================

def render_starfield(width: int = 52) -> str:
    """生成随机星空装饰行"""
    lines = []
    for _ in range(3):
        line = ""
        pos = 0
        while pos < width:
            gap = random.randint(2, 6)
            pos += gap
            if pos < width:
                line += " " * gap + random.choice(_STAR_CHARS)
                pos += 1
        lines.append(line)
    return "\n".join(lines)


def render_lightning_field(width: int = 42) -> str:
    """生成雷电能量场"""
    line1 = "  " + "░" * width
    chars = []
    for i in range(width):
        if random.random() < 0.25:
            chars.append(random.choice(_LIGHTNING_CHARS))
        else:
            chars.append("░")
    line2 = "  " + "".join(chars)
    line3 = "  " + "░" * width
    return f"{line1}\n{line2}\n{line3}"


def render_progress_bar(
    current: float,
    maximum: float,
    width: int = 30,
    fill_char: str = "█",
    empty_char: str = "░",
) -> str:
    """渲染进度条"""
    if maximum <= 0:
        ratio = 0.0
    else:
        ratio = min(current / maximum, 1.0)
    filled = int(ratio * width)
    empty = width - filled
    percent = int(ratio * 100)
    return f"{fill_char * filled}{empty_char * empty} {percent}%"


def render_dimension_bars(scores: dict[str, float], max_score: float = 10.0) -> str:
    """
    渲染六维灵根评分柱状图。

    scores: {"inscription": 8.0, "formation": 9.0, ...}
    """
    dim_labels = {
        "inscription":   "📝 铭文",
        "formation":     "🏗️ 阵法",
        "technique":     "⚙️ 法诀",
        "lineage":       "📖 道统",
        "resilience":    "🛡️ 护体",
        "enlightenment": "✨ 悟道",
    }

    lines = []
    for key, label in dim_labels.items():
        score = scores.get(key, 0)
        filled = int((score / max_score) * 10)
        empty = 10 - filled
        bar = "█" * filled + "░" * empty
        lines.append(f"│  {label} {bar} {score:.1f}  │")

    return "\n".join(lines)


def render_realm_chain(old_level: int, new_level: int, realms: list) -> str:
    """
    渲染境界跃迁路径链。

    从凡人到新境界，已过用箭头连接，新境界高亮。
    """
    parts = []
    for r in realms:
        if r.level < old_level:
            parts.append(f"{r.symbol}")
        elif r.level == old_level:
            parts.append(f"{r.symbol}")
        elif r.level == new_level:
            parts.append(f"【{r.symbol} {r.name_cn}】")
            break
        elif r.level < new_level:
            parts.append(f"{r.symbol}")
    return " → ".join(parts)
