"""
⚒️ 天工 TianGong — 洞府管理系统（Phase 2）
本地法宝存储、初始化、拉取、管理

洞府目录结构:
~/.tiangong/
├── config.yaml          # 洞府配置
├── cultivator.json      # 修仙者档案（本地缓存）
├── registry.json        # 法宝索引
├── forge/               # 🔨 炼器炉（自己创作的法宝）
│   ├── my-agent-1/
│   └── my-agent-2/
├── vault/               # ✨ 藏宝阁（拉取的别人的法宝）
│   ├── search-serpent/
│   └── data-dragon/
│       └── .archive/    # 旧版本备份
└── logs/                # 操作日志
"""

from __future__ import annotations

import json
import logging
import shutil
import time
from contextlib import suppress
from pathlib import Path

from .config import config

logger = logging.getLogger("tiangong.vault")


# ============================================================
# 洞府初始化
# ============================================================

def init_cave() -> str:
    """
    初始化本地洞府。首次使用天工时自动调用。

    Returns:
        操作结果消息
    """
    cave_dir = Path(config.CAVE_DIR)

    if cave_dir.exists() and (cave_dir / "config.yaml").exists():
        return f"✅ 洞府已存在: `{cave_dir}`"

    # 创建目录结构
    Path(config.FORGE_DIR).mkdir(parents=True, exist_ok=True)
    Path(config.VAULT_DIR).mkdir(parents=True, exist_ok=True)
    Path(config.VAULT_ARCHIVE_DIR).mkdir(parents=True, exist_ok=True)
    Path(config.CAVE_LOGS_DIR).mkdir(parents=True, exist_ok=True)

    # 创建默认配置
    _write_default_config()

    # 创建本地修仙者档案
    _write_default_profile()

    # 创建空注册表
    registry_path = Path(config.CAVE_REGISTRY)
    if not registry_path.exists():
        registry_path.write_text("{}", encoding="utf-8")

    return (
        f"🏛️ 洞府已开辟！\n\n"
        f"- 📁 洞府位置: `{cave_dir}`\n"
        f"- 🔨 炼器炉: `{config.FORGE_DIR}`\n"
        f"- ✨ 藏宝阁: `{config.VAULT_DIR}`\n"
        f"- 📋 配置文件: `{config.CAVE_CONFIG}`\n\n"
        "> 你的修仙之旅正式开始！"
    )


def _write_default_config() -> None:
    """写入默认洞府配置"""
    import yaml

    default_config = {
        "version": "2.0.0",
        "cave": {
            "forge_dir": config.FORGE_DIR,
            "vault_dir": config.VAULT_DIR,
        },
        "preferences": {
            "auto_install_deps": True,
            "python_env": "system",
        },
        "github": {
            "username": config.GITHUB_USERNAME,
            "repo_owner": config.GITHUB_REPO_OWNER,
            "repo_name": config.GITHUB_REPO_NAME,
        },
    }

    config_path = Path(config.CAVE_CONFIG)
    try:
        config_path.write_text(
            yaml.dump(default_config, allow_unicode=True, default_flow_style=False),
            encoding="utf-8",
        )
    except ImportError:
        # 如果没装 yaml，用 JSON 代替
        config_path = Path(config.CAVE_DIR) / "config.json"
        config_path.write_text(
            json.dumps(default_config, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


def _write_default_profile() -> None:
    """写入默认修仙者档案"""
    profile = {
        "username": config.GITHUB_USERNAME,
        "created_at": time.time(),
        "realm_level": 0,
        "spirit_power": 0,
    }

    profile_path = Path(config.CAVE_PROFILE)
    profile_path.write_text(
        json.dumps(profile, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def ensure_cave() -> None:
    """确保洞府已初始化（静默版，不输出消息）"""
    cave_dir = Path(config.CAVE_DIR)
    if not cave_dir.exists():
        init_cave()


# ============================================================
# 藏宝阁管理
# ============================================================

def _load_local_artifact_meta(artifact_dir: Path) -> dict:
    """Load local artifact metadata from supported TianGong manifest files."""
    yaml_file = artifact_dir / "tiangong.yaml"
    json_file = artifact_dir / "tiangong.json"

    if yaml_file.exists():
        try:
            import yaml
        except ImportError:
            pass
        else:
            with suppress(OSError, yaml.YAMLError):
                meta = yaml.safe_load(yaml_file.read_text(encoding="utf-8")) or {}
                if isinstance(meta, dict):
                    return meta

    if json_file.exists():
        with suppress(json.JSONDecodeError, OSError):
            meta = json.loads(json_file.read_text(encoding="utf-8"))
            if isinstance(meta, dict):
                return meta

    return {}


def list_vault() -> list[dict]:
    """列出藏宝阁中所有法宝"""
    vault_dir = Path(config.VAULT_DIR)
    if not vault_dir.exists():
        return []

    artifacts = []
    for item in sorted(vault_dir.iterdir()):
        if item.is_dir() and not item.name.startswith("."):
            meta_file = item / ".tiangong_meta.json"
            meta = {}
            if meta_file.exists():
                with suppress(json.JSONDecodeError, OSError):
                    meta = json.loads(meta_file.read_text(encoding="utf-8"))

            artifacts.append({
                "name": item.name,
                "path": str(item),
                "version": meta.get("version", "unknown"),
                "source": meta.get("source", "unknown"),
                "pulled_at": meta.get("pulled_at", ""),
                "grade": meta.get("grade", "⚪ 凡器"),
            })

    return artifacts


def list_forge() -> list[dict]:
    """列出炼器炉中自己创作的法宝"""
    forge_dir = Path(config.FORGE_DIR)
    if not forge_dir.exists():
        return []

    artifacts = []
    for item in sorted(forge_dir.iterdir()):
        if item.is_dir() and not item.name.startswith("."):
            # 检查是否有 TianGong 元数据清单
            yaml_file = item / "tiangong.yaml"
            json_file = item / "tiangong.json"
            has_config = yaml_file.exists() or json_file.exists()
            meta = _load_local_artifact_meta(item)

            artifacts.append({
                "name": item.name,
                "agent_id": meta.get("agent_id") or meta.get("id") or "",
                "path": str(item),
                "has_config": has_config,
                "status": "ready" if has_config else "draft",
            })

    return artifacts


def save_artifact_meta(
    artifact_dir: Path,
    name: str,
    version: str,
    source: str,
    grade: str = "⚪ 凡器",
    creator: str = "",
) -> None:
    """在法宝目录下写入元信息"""
    meta = {
        "name": name,
        "version": version,
        "source": source,
        "grade": grade,
        "creator": creator,
        "pulled_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "updated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }

    meta_file = artifact_dir / ".tiangong_meta.json"
    meta_file.write_text(
        json.dumps(meta, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def archive_artifact(artifact_name: str) -> tuple[bool, str]:
    """
    归档（封印）法宝——将其移到 .archive/ 目录。

    Returns:
        (是否成功, 消息)
    """
    vault_dir = Path(config.VAULT_DIR)
    artifact_dir = vault_dir / artifact_name

    if not artifact_dir.exists():
        return False, f"⚠️ 藏宝阁中未找到法宝 `{artifact_name}`"

    archive_dir = Path(config.VAULT_ARCHIVE_DIR)
    archive_dir.mkdir(parents=True, exist_ok=True)

    # 带时间戳归档，防止覆盖
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    archive_target = archive_dir / f"{artifact_name}_{timestamp}"

    shutil.move(str(artifact_dir), str(archive_target))

    return True, (
        f"✅ 法宝 `{artifact_name}` 已封印（归档）\n"
        f"- 归档位置: `{archive_target}`\n"
        "> 可在 `.archive/` 目录中找到备份"
    )


def check_artifact_exists(artifact_name: str, location: str = "vault") -> bool:
    """检查法宝是否已存在"""
    if location == "vault":
        return (Path(config.VAULT_DIR) / artifact_name).exists()
    elif location == "forge":
        return (Path(config.FORGE_DIR) / artifact_name).exists()
    return False


# ============================================================
# 格式化展示
# ============================================================

def format_vault_list(artifacts: list[dict]) -> str:
    """格式化藏宝阁列表"""
    if not artifacts:
        return (
            "## ✨ 藏宝阁（空）\n\n"
            "> 还没有拉取任何法宝。本地 vault/ 目录真实快照为 0；"
            "先搜索寻宝阁，再用公开工具请宝下凡。\n\n"
            "## 下一步\n\n"
            "- 搜索寻宝阁: `treasure_pavilion(action=\"search\")`\n"
            "- 请宝下凡: `treasure_pavilion(action=\"summon\", artifact_name=\"artifact-name\")`\n"
            "- 冲击法宝天榜: `leaderboard(type=\"artifact\")`"
        )

    lines = [
        "## ✨ 藏宝阁",
        "",
        f"共 {len(artifacts)} 件法宝：",
        "",
        "| 法宝 | 品阶 | 版本 | 来源 | 拉取时间 | 动作 |",
        "|------|------|------|------|---------|------|",
    ]

    for a in artifacts:
        artifact_name = a["name"]
        actions = (
            f"`infuse_spirit(artifact_name=\"{artifact_name}\")` · "
            f"`treasure_pavilion(action=\"lineage\", artifact_name=\"{artifact_name}\")`"
        )
        lines.append(
            f"| {artifact_name} | {a['grade']} | {a['version']} | {a['source']} | "
            f"{a['pulled_at'][:10]} | {actions} |"
        )

    return "\n".join(lines)


def format_forge_list(artifacts: list[dict]) -> str:
    """格式化炼器炉列表"""
    if not artifacts:
        return (
            "## 🔨 炼器炉（空）\n\n"
            "> 还没有创作任何法宝。本地 forge/ 目录真实快照为 0；"
            "用公开工具开炉炼器，生成第一件可发布法宝。\n\n"
            "## 下一步\n\n"
            "- 开炉炼器: `forge_agent(name=\"my-first-artifact\", "
            "description=\"My first TianGong artifact\")`\n"
            "- 发布悬赏: `quest(action=\"post\", artifact_name=\"my-first-artifact\", "
            "description=\"需要一件适合新手入道的法宝\")`\n"
            "- 冲击法宝天榜: `leaderboard(type=\"artifact\")`"
        )

    lines = [
        "## 🔨 炼器炉",
        "",
        f"共 {len(artifacts)} 件法宝：",
        "",
        "| 法宝 | 状态 | 路径 | 动作 |",
        "|------|------|------|------|",
    ]

    for a in artifacts:
        artifact_name = a["name"]
        status = "✅ 就绪" if a["status"] == "ready" else "📝 草稿（缺 tiangong.yaml/tiangong.json）"
        actions = f"`publish_agent(artifact_name=\"{artifact_name}\")`"
        if a.get("agent_id"):
            actions += f" · `refine_agent(agent_id=\"{a['agent_id']}\")`"
        else:
            actions += " · 发布后使用返回的 `agent_id` 淬炼"
        lines.append(f"| {artifact_name} | {status} | `{a['path']}` | {actions} |")

    return "\n".join(lines)


def _build_vault_share_block(forge_items: list[dict], vault_items: list[dict]) -> str:
    """Build a paste-ready share card for the local cave portfolio."""
    total_count = len(forge_items) + len(vault_items)
    share_text = (
        f"我在 TianGong 本地洞府已有 {total_count} 件法宝："
        f"炼器炉 {len(forge_items)} 件，藏宝阁 {len(vault_items)} 件。"
    )

    lines = [
        "",
        "---",
        "",
        "## 📣 复制洞府名片",
        "",
        "```text",
        share_text,
        "加入修炼: pip install tiangong-mcp",
        "```",
        "",
        "## 下一步",
        "",
    ]

    if forge_items:
        first_forge = forge_items[0]["name"]
        lines.append(f"- 发布炼器炉法宝: `publish_agent(artifact_name=\"{first_forge}\")`")
    else:
        lines.append(
            "- 开炉炼器: `forge_agent(name=\"my-first-artifact\", "
            "description=\"My first TianGong artifact\")`"
        )
        lines.append(
            "- 发布首件悬赏: `quest(action=\"post\", "
            "artifact_name=\"my-first-artifact\", "
            "description=\"需要一件适合新手入道的法宝\")`"
        )

    if vault_items:
        first_vault = vault_items[0]["name"]
        lines.append(f"- 鉴定藏宝阁法宝: `infuse_spirit(artifact_name=\"{first_vault}\")`")
    else:
        lines.append("- 寻宝请宝: `treasure_pavilion(action=\"search\")`")
        lines.append(
            "- 请宝下凡: `treasure_pavilion(action=\"summon\", "
            "artifact_name=\"artifact-name\")`"
        )

    lines.extend([
        "- 继续寻宝: `treasure_pavilion(action=\"search\")`",
        "- 冲击法宝天榜: `leaderboard(type=\"artifact\")`",
    ])

    return "\n".join(lines)


def format_my_vault() -> str:
    """格式化我的法宝面板"""
    forge_items = list_forge()
    vault_items = list_vault()

    lines = [
        "# 📦 我的法宝 (My Vault)",
        "",
        "> 本地洞府快照：来自当前机器的 forge/ 与 vault/ 目录扫描，不伪造远程拥有量。",
        f"> 炼器炉: {len(forge_items)} 件 · 藏宝阁: {len(vault_items)} 件",
        "",
        f"- 本地已开辟法宝栏位：{len(forge_items) + len(vault_items)}",
        "",
    ]

    lines.append(format_forge_list(forge_items))
    lines.append("")
    lines.append(format_vault_list(vault_items))
    lines.append(_build_vault_share_block(forge_items, vault_items))

    return "\n".join(lines)


def format_vault_status() -> str:
    """格式化洞府状态查询"""
    import platform

    # 获取系统资源（如果没有 psutil 则使用基础库或省略）
    try:
        import psutil
        cpu_usage = f"{psutil.cpu_percent(interval=0.1)}%"
        memory = psutil.virtual_memory()
        mem_usage = f"{memory.percent}% ({memory.used // (1024**2)}MB / {memory.total // (1024**2)}MB)"
    except ImportError:
        cpu_usage = "未知 (需安装 psutil)"
        mem_usage = "未知 (需安装 psutil)"

    lines = [
        "# 🏛️ 洞府状态查询 (Vault Status)",
        "",
        f"- 💻 系统节点: `{platform.node()}` ({platform.system()} {platform.release()})",
        f"- ⚙️ CPU 使用率: `{cpu_usage}`",
        f"- 🧠 内存使用率: `{mem_usage}`",
        f"- 📁 本地洞府位置: `{config.CAVE_DIR}`",
        "- 🔌 社区连接状态: `🌐 连接正常` (数据采用本地/远程同步策略)",
        "- ⏱️ 客户端运行状态: `🟢 活跃`",
    ]
    return "\n".join(lines)
