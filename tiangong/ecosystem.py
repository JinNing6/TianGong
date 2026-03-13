"""
⚒️ 天工 TianGong — 生态联动
与赛博华佗（治）和 Noosphere（识）的联动接口
"""

from __future__ import annotations

import logging

from .config import config

logger = logging.getLogger("tiangong.ecosystem")


async def call_cyberhuatuo_diagnose(error_message: str, framework: str = "") -> str:
    """
    调用赛博华佗诊断 Agent 的问题（走火入魔时自动求医）。

    在 MCP 生态中，天工和赛博华佗通过同一个 MCP Client 连接，
    因此实际联动通过提示 Agent 调用赛博华佗的工具来实现。
    """
    if not config.CYBERHUATUO_ENABLED:
        return "⚠️ 赛博华佗联动未启用。请在 .env 中设置 CYBERHUATUO_ENABLED=true"

    return (
        "## 🩺 走火入魔 · 自动求医\n\n"
        "检测到你的法宝出了问题——已为你准备好就医信息：\n\n"
        f"**症状描述**: {error_message}\n"
        f"**相关框架**: {framework or '未知'}\n\n"
        "**请调用赛博华佗进行诊断：**\n\n"
        "```\n"
        f"diagnose(query=\"{error_message}\""
        f"{f', framework=\"{framework}\"' if framework else ''})\n"
        "```\n\n"
        "> 💡 赛博华佗（CyberHuaTuo）是天工生态的诊断系统。\n"
        "> 修仙路上，华佗是你最可靠的伙伴。"
    )


async def upload_to_noosphere(
    creator: str,
    thought: str,
    context: str,
    tags: list[str] | None = None,
) -> str:
    """
    将修炼顿悟上传到 Noosphere 意识共同体。

    在 MCP 生态中，通过提示 Agent 调用 Noosphere 的工具来实现。
    """
    if not config.NOOSPHERE_ENABLED:
        return "⚠️ Noosphere 联动未启用。请在 .env 中设置 NOOSPHERE_ENABLED=true"

    tags_str = f", tags={tags}" if tags else ""

    return (
        "## 🌌 修炼顿悟 · 上传意识\n\n"
        "你的修炼心得值得沉淀到意识共同体——\n\n"
        f"**创作者**: @{creator}\n"
        f"**顿悟内容**: {thought}\n"
        f"**修炼场景**: {context}\n\n"
        "**请调用 Noosphere 上传意识：**\n\n"
        "```\n"
        f"upload_consciousness(\n"
        f"    creator=\"{creator}\",\n"
        f"    consciousness_type=\"epiphany\",\n"
        f"    thought=\"{thought}\",\n"
        f"    context=\"{context}\"\n"
        f"{tags_str}\n"
        f")\n"
        "```\n\n"
        "> 💡 Noosphere 是天工生态的意识沉淀系统。\n"
        "> 你的每一次顿悟，都将成为集体智慧的一部分。"
    )


def get_ecosystem_status() -> str:
    """获取生态联动状态"""
    return (
        "## 🌍 天工生态联动状态\n\n"
        "```\n"
        "┌──────────────────────────────────────┐\n"
        "│          开发者 AI 生态三柱           │\n"
        "│                                      │\n"
        f"│  🩺 赛博华佗  {'✅ 已启用' if config.CYBERHUATUO_ENABLED else '❌ 未启用':13s}│\n"
        f"│  ⚒️ 天工      ✅ 当前平台           │\n"
        f"│  🌌 Noosphere {'✅ 已启用' if config.NOOSPHERE_ENABLED else '❌ 未启用':13s}│\n"
        "│                                      │\n"
        "│  治 · 造 · 识 — 三柱合一             │\n"
        "└──────────────────────────────────────┘\n"
        "```\n"
    )
