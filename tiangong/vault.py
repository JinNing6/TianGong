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
                try:
                    meta = json.loads(meta_file.read_text(encoding="utf-8"))
                except (json.JSONDecodeError, OSError):
                    pass

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
            # 检查是否有 tiangong.yaml
            yaml_file = item / "tiangong.yaml"
            has_config = yaml_file.exists()

            artifacts.append({
                "name": item.name,
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
            "> 还没有拉取任何法宝。使用 `summon_artifact(\"法宝名\")` 请宝下凡！"
        )

    lines = [
        "## ✨ 藏宝阁",
        "",
        f"共 {len(artifacts)} 件法宝：",
        "",
        "| 法宝 | 品阶 | 版本 | 来源 | 拉取时间 |",
        "|------|------|------|------|---------|",
    ]

    for a in artifacts:
        lines.append(
            f"| {a['name']} | {a['grade']} | {a['version']} | {a['source']} | {a['pulled_at'][:10]} |"
        )

    return "\n".join(lines)


def format_forge_list(artifacts: list[dict]) -> str:
    """格式化炼器炉列表"""
    if not artifacts:
        return (
            "## 🔨 炼器炉（空）\n\n"
            "> 还没有创作任何法宝。开始在 `forge/` 目录中打造你的法宝！"
        )

    lines = [
        "## 🔨 炼器炉",
        "",
        f"共 {len(artifacts)} 件法宝：",
        "",
        "| 法宝 | 状态 | 路径 |",
        "|------|------|------|",
    ]

    for a in artifacts:
        status = "✅ 就绪" if a["status"] == "ready" else "📝 草稿（缺 tiangong.yaml）"
        lines.append(f"| {a['name']} | {status} | `{a['path']}` |")

    return "\n".join(lines)


def format_cave_status() -> str:
    """格式化洞府全景状态"""
    forge_items = list_forge()
    vault_items = list_vault()

    lines = [
        "# 🏛️ 洞府全景",
        "",
        f"- 📁 位置: `{config.CAVE_DIR}`",
        f"- 🔨 炼器炉: {len(forge_items)} 件法宝",
        f"- ✨ 藏宝阁: {len(vault_items)} 件法宝",
        "",
    ]

    lines.append(format_forge_list(forge_items))
    lines.append("")
    lines.append(format_vault_list(vault_items))

    return "\n".join(lines)
