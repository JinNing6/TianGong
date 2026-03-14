"""
⚒️ 天工 TianGong — 双层法宝体系（Phase 2）
瞬时法宝体（GitHub Issue） → AI审核 → 常驻法宝体（marketplace/）

飞升上界 + 请宝下凡 完整流程
"""

from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path

import httpx

from .config import config
from .vault import ensure_cave, save_artifact_meta, check_artifact_exists

logger = logging.getLogger("tiangong.marketplace")

# GitHub API 基础配置
GITHUB_API = "https://api.github.com"


def _get_headers() -> dict:
    """获取 GitHub API 请求头"""
    headers = {"Accept": "application/vnd.github.v3+json"}
    if config.GITHUB_TOKEN:
        headers["Authorization"] = f"token {config.GITHUB_TOKEN}"
    return headers


# ============================================================
# 飞升上界（publish_agent）
# ============================================================

def validate_artifact_for_publish(artifact_dir: Path) -> tuple[bool, list[str]]:
    """
    本地校验法宝是否满足发布要求。

    Returns:
        (是否通过, 错误列表)
    """
    errors = []

    meta = {}
    # 1. 检查 tiangong.yaml 是否存在
    yaml_file = artifact_dir / "tiangong.yaml"
    if not yaml_file.exists():
        errors.append("❌ 缺少 `tiangong.yaml` 元数据文件")
    else:
        try:
            import yaml
            meta = yaml.safe_load(yaml_file.read_text(encoding="utf-8"))
        except ImportError:
            # 如果没装 yaml，尝试 JSON 替代
            json_file = artifact_dir / "tiangong.json"
            if json_file.exists():
                meta = json.loads(json_file.read_text(encoding="utf-8"))
            else:
                errors.append("❌ 无法解析 `tiangong.yaml`（缺少 pyyaml 依赖）")
                meta = {}
        except Exception as e:
            errors.append(f"❌ `tiangong.yaml` 解析失败: {e}")
            meta = {}

        if meta:
            required_fields = ["name", "description", "entry", "version"]
            for field in required_fields:
                if not meta.get(field):
                    errors.append(f"❌ `tiangong.yaml` 缺少必填字段: `{field}`")

    # 2. 检查 README.md
    readme = artifact_dir / "README.md"
    if not readme.exists():
        errors.append("❌ 缺少 `README.md` 使用说明")
    else:
        content = readme.read_text(encoding="utf-8", errors="ignore")
        if len(content) < 100:
            errors.append(f"❌ `README.md` 内容过少（{len(content)} 字符，要求 ≥ 100）")

    # 3. 检查入口文件
    if meta and meta.get("entry"):
        entry_file = artifact_dir / meta["entry"]
        if not entry_file.exists():
            errors.append(f"❌ 入口文件 `{meta['entry']}` 不存在")

    return len(errors) == 0, errors


async def publish_agent(
    artifact_name: str,
    is_anonymous: bool = False,
) -> str:
    """
    飞升上界——将法宝发布为瞬时法宝体（GitHub Issue）。

    Args:
        artifact_name: 法宝名称（forge/ 目录下的文件夹名）
        is_anonymous: 是否匿名上传

    Returns:
        发布结果消息
    """
    ensure_cave()

    artifact_dir = Path(config.FORGE_DIR) / artifact_name
    if not artifact_dir.exists():
        return (
            f"⚠️ 炼器炉中未找到法宝 `{artifact_name}`\n"
            f"请确保法宝目录存在于: `{config.FORGE_DIR}/{artifact_name}/`"
        )

    # 1. 本地校验
    valid, errors = validate_artifact_for_publish(artifact_dir)
    if not valid:
        return (
            f"❌ 法宝 `{artifact_name}` 未通过本地校验：\n\n"
            + "\n".join(errors)
            + "\n\n> 请修复上述问题后重新飞升"
        )

    # 2. 读取元数据
    meta = _load_artifact_meta(artifact_dir)

    # 3. 匿名处理
    creator = "无名散修" if is_anonymous else config.GITHUB_USERNAME

    # 4. 构建 Issue 内容
    issue_title = f"🔮 [法宝] {meta.get('name_cn', artifact_name)} ({artifact_name})"
    issue_body = _build_issue_body(meta, artifact_name, creator, artifact_dir)

    # 5. 通过 GitHub API 创建 Issue
    if not config.GITHUB_TOKEN:
        return (
            "⚠️ 未配置 GITHUB_TOKEN\n"
            "飞升上界需要 GitHub Token。请在 `.env` 中配置 GITHUB_TOKEN。"
        )

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{GITHUB_API}/repos/{config.GITHUB_REPO_OWNER}/{config.GITHUB_REPO_NAME}/issues",
                headers=_get_headers(),
                json={
                    "title": issue_title,
                    "body": issue_body,
                    "labels": ["artifact", "pending-review"],
                },
            )

            if resp.status_code == 201:
                issue_data = resp.json()
                issue_number = issue_data["number"]
                issue_url = issue_data["html_url"]

                return (
                    f"# ✅ 飞升上界成功！\n\n"
                    f"法宝 `{artifact_name}` 已上传为 **🔮 瞬时法宝体**\n\n"
                    f"- 📝 Issue: #{issue_number}\n"
                    f"- 🔗 链接: {issue_url}\n"
                    f"- 👤 创建者: {creator}\n"
                    f"- ⏳ 状态: **待炼化**（等待 AI 审核）\n\n"
                    "> AI 审核通过后将自动晋升为 🏛️ 常驻法宝体，正式入驻寻宝阁。"
                )
            else:
                return f"❌ 飞升失败: GitHub API 返回 {resp.status_code}\n{resp.text}"

    except Exception as e:
        return f"❌ 飞升失败: {e}"


def _load_artifact_meta(artifact_dir: Path) -> dict:
    """加载法宝元数据"""
    yaml_file = artifact_dir / "tiangong.yaml"
    json_file = artifact_dir / "tiangong.json"

    if yaml_file.exists():
        try:
            import yaml
            return yaml.safe_load(yaml_file.read_text(encoding="utf-8")) or {}
        except ImportError:
            pass

    if json_file.exists():
        try:
            return json.loads(json_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass

    return {}


def _build_issue_body(meta: dict, artifact_name: str, creator: str, artifact_dir: Path) -> str:
    """构建 Issue 正文"""
    readme_file = artifact_dir / "README.md"
    readme_content = ""
    if readme_file.exists():
        readme_content = readme_file.read_text(encoding="utf-8", errors="ignore")[:2000]

    body = f"""## 🔮 法宝元数据

| 属性 | 值 |
|------|-----|
| **名称** | {meta.get('name', artifact_name)} |
| **中文名** | {meta.get('name_cn', 'N/A')} |
| **创建者** | @{creator} |
| **框架** | {meta.get('framework', 'N/A')} |
| **语言** | {meta.get('language', 'python')} |
| **版本** | {meta.get('version', '0.1.0')} |
| **描述** | {meta.get('description', 'N/A')} |

## 📖 使用说明

{readme_content}

---

> 此法宝通过天工 MCP `publish_agent` 工具上传。
> 状态: ⏳ 待炼化（Pending AI Review）
"""
    return body


# ============================================================
# 请宝下凡（summon_artifact）
# ============================================================

async def summon_artifact(artifact_name: str) -> str:
    """
    请宝下凡——从寻宝阁拉取法宝到本地藏宝阁。

    Args:
        artifact_name: 法宝名称

    Returns:
        拉取结果消息
    """
    ensure_cave()

    # 1. 检查本地是否已存在
    if check_artifact_exists(artifact_name, "vault"):
        return (
            f"⚠️ 法宝 `{artifact_name}` 已存在于藏宝阁\n"
            f"- 路径: `{config.VAULT_DIR}/{artifact_name}/`\n\n"
            "> 如需更新版本，请先使用 `banish_artifact` 封印旧版"
        )

    # 2. 从 GitHub API 查询法宝
    meta = await _fetch_artifact_meta(artifact_name)
    if not meta:
        return f"⚠️ 寻宝阁中未找到法宝 `{artifact_name}`"

    # 3. 下载法宝文件
    target_dir = Path(config.VAULT_DIR) / artifact_name
    target_dir.mkdir(parents=True, exist_ok=True)

    success = await _download_artifact_files(artifact_name, target_dir)
    if not success:
        return f"❌ 法宝 `{artifact_name}` 下载失败"

    # 4. 写入元信息
    save_artifact_meta(
        artifact_dir=target_dir,
        name=artifact_name,
        version=meta.get("version", "unknown"),
        source=f"github:{config.GITHUB_REPO_OWNER}/{config.GITHUB_REPO_NAME}",
        grade=meta.get("grade", "⚪ 凡器"),
        creator=meta.get("creator", "unknown"),
    )

    # 5. 检查 .env 配置
    env_example = target_dir / ".env.example"
    env_hint = ""
    if env_example.exists():
        env_hint = (
            "\n\n### ⚠️ 需要配置 API Key\n"
            f"请检查 `{target_dir}/.env.example` 并创建 `.env` 文件配置所需 API Key。"
        )

    return (
        f"# ✅ 请宝下凡成功！\n\n"
        f"法宝 `{artifact_name}` 已入藏宝阁\n\n"
        f"- 📁 位置: `{target_dir}`\n"
        f"- 📦 版本: {meta.get('version', 'unknown')}\n"
        f"- 👤 创建者: {meta.get('creator', 'unknown')}\n"
        f"- {meta.get('grade', '⚪ 凡器')}"
        f"{env_hint}"
    )


async def _fetch_artifact_meta(artifact_name: str) -> dict | None:
    """从 GitHub 读取法宝元数据"""
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            # 优先从 marketplace/ 目录读取
            meta_url = (
                f"{GITHUB_API}/repos/{config.GITHUB_REPO_OWNER}/{config.GITHUB_REPO_NAME}"
                f"/contents/{config.MARKETPLACE_DIR}/{artifact_name}/tiangong.yaml"
            )
            resp = await client.get(meta_url, headers=_get_headers())

            if resp.status_code == 200:
                import base64
                content = base64.b64decode(resp.json()["content"]).decode("utf-8")
                try:
                    import yaml
                    return yaml.safe_load(content)
                except ImportError:
                    # 如果没有 yaml，尝试从 JSON 获取
                    pass

            # 尝试 JSON 格式
            json_url = meta_url.replace("tiangong.yaml", "tiangong.json")
            resp = await client.get(json_url, headers=_get_headers())
            if resp.status_code == 200:
                import base64
                content = base64.b64decode(resp.json()["content"]).decode("utf-8")
                return json.loads(content)

    except Exception as e:
        logger.warning(f"获取法宝元数据失败: {e}")

    return None


async def _download_artifact_files(artifact_name: str, target_dir: Path) -> bool:
    """从 GitHub 下载法宝文件"""
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            # 获取目录列表
            dir_url = (
                f"{GITHUB_API}/repos/{config.GITHUB_REPO_OWNER}/{config.GITHUB_REPO_NAME}"
                f"/contents/{config.MARKETPLACE_DIR}/{artifact_name}"
            )
            resp = await client.get(dir_url, headers=_get_headers())

            if resp.status_code != 200:
                return False

            files = resp.json()
            if not isinstance(files, list):
                return False

            # 下载每个文件
            for file_info in files:
                if file_info["type"] == "file":
                    await _download_single_file(client, file_info, target_dir)
                elif file_info["type"] == "dir":
                    # 递归下载子目录
                    sub_dir = target_dir / file_info["name"]
                    sub_dir.mkdir(parents=True, exist_ok=True)
                    sub_resp = await client.get(file_info["url"], headers=_get_headers())
                    if sub_resp.status_code == 200:
                        for sub_file in sub_resp.json():
                            if sub_file["type"] == "file":
                                await _download_single_file(client, sub_file, sub_dir)

        return True

    except Exception as e:
        logger.error(f"下载法宝文件失败: {e}")
        return False


async def _download_single_file(client: httpx.AsyncClient, file_info: dict, target_dir: Path) -> None:
    """下载单个文件"""
    import base64
    try:
        resp = await client.get(file_info["url"], headers=_get_headers())
        if resp.status_code == 200:
            content = base64.b64decode(resp.json()["content"])
            file_path = target_dir / file_info["name"]
            file_path.write_bytes(content)
    except Exception as e:
        logger.warning(f"下载文件 {file_info['name']} 失败: {e}")


# ============================================================
# 封印法宝（banish_artifact）
# ============================================================

def banish_artifact(artifact_name: str) -> str:
    """封印（归档）藏宝阁中的法宝"""
    from .vault import archive_artifact
    success, message = archive_artifact(artifact_name)
    return message
