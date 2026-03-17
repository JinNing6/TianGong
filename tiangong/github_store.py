"""
⚒️ 天工 TianGong — GitHub 统一存储层
将 Agent 注册表和修仙者档案存储到 GitHub 仓库，实现全平台共享。

数据路径：
    data/registry.json     — Agent 注册表
    data/cultivators.json   — 修仙者档案
"""

from __future__ import annotations

import base64
import json
import logging
import time
from typing import Any

import httpx

from .config import config

logger = logging.getLogger("tiangong.github_store")

# GitHub API
GITHUB_API = "https://api.github.com"

# 缓存 TTL（秒）
CACHE_TTL = 60  # 1 分钟内重复读取使用缓存

# 最大重试次数（SHA 冲突时）
MAX_RETRIES = 3

# 数据文件路径
REGISTRY_PATH = "data/registry.json"
CULTIVATORS_PATH = "data/cultivators.json"


class _Cache:
    """简单的内存缓存"""

    def __init__(self):
        self._data: dict[str, Any] = {}
        self._sha: dict[str, str] = {}
        self._timestamp: dict[str, float] = {}

    def get(self, path: str) -> tuple[Any | None, str | None]:
        """获取缓存数据和 SHA，如果过期返回 None"""
        ts = self._timestamp.get(path, 0)
        if time.time() - ts > CACHE_TTL:
            return None, None
        return self._data.get(path), self._sha.get(path)

    def set(self, path: str, data: Any, sha: str) -> None:
        """设置缓存"""
        self._data[path] = data
        self._sha[path] = sha
        self._timestamp[path] = time.time()

    def invalidate(self, path: str) -> None:
        """清除指定路径的缓存"""
        self._data.pop(path, None)
        self._sha.pop(path, None)
        self._timestamp.pop(path, 0)


# 全局缓存实例
_cache = _Cache()


def _get_headers() -> dict:
    """获取 GitHub API 请求头"""
    headers = {"Accept": "application/vnd.github.v3+json"}
    if config.GITHUB_TOKEN:
        headers["Authorization"] = f"token {config.GITHUB_TOKEN}"
    return headers


async def read_json(path: str) -> tuple[dict, str]:
    """
    从 GitHub 仓库读取 JSON 文件。

    Args:
        path: 仓库中的文件路径（如 "data/registry.json"）

    Returns:
        (解析后的 dict, 文件 SHA)

    Raises:
        如果文件不存在，返回空 dict 和空 SHA（首次使用时自动创建）
    """
    # 检查缓存
    cached_data, cached_sha = _cache.get(path)
    if cached_data is not None and cached_sha is not None:
        return cached_data, cached_sha

    if not config.GITHUB_TOKEN:
        logger.warning("未配置 GITHUB_TOKEN，无法读取 GitHub 数据")
        return {}, ""

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            url = (
                f"{GITHUB_API}/repos/{config.GITHUB_REPO_OWNER}/"
                f"{config.GITHUB_REPO_NAME}/contents/{path}"
            )
            resp = await client.get(url, headers=_get_headers())

            if resp.status_code == 200:
                resp_data = resp.json()
                content = base64.b64decode(resp_data["content"]).decode("utf-8")
                data = json.loads(content) if content.strip() else {}
                sha = resp_data["sha"]
                _cache.set(path, data, sha)
                return data, sha

            elif resp.status_code == 404:
                # 文件不存在，首次使用
                logger.info(f"GitHub 文件 {path} 不存在，将在首次写入时创建")
                return {}, ""

            else:
                logger.error(f"读取 GitHub 文件失败: {resp.status_code} {resp.text}")
                return {}, ""

    except Exception as e:
        logger.error(f"读取 GitHub 文件异常: {e}")
        return {}, ""


async def write_json(path: str, data: dict, message: str = "") -> bool:
    """
    将 JSON 数据写入 GitHub 仓库文件。

    使用 GitHub Contents API 的 PUT 方法，带 SHA 防冲突。
    如果 SHA 冲突，自动重试（最多 MAX_RETRIES 次）。

    Args:
        path: 仓库中的文件路径
        data: 要写入的数据
        message: Git commit message

    Returns:
        是否写入成功
    """
    if not config.GITHUB_TOKEN:
        logger.warning("未配置 GITHUB_TOKEN，无法写入 GitHub 数据")
        return False

    if not message:
        message = f"⚒️ TianGong: update {path}"

    content_b64 = base64.b64encode(
        json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
    ).decode("ascii")

    url = (
        f"{GITHUB_API}/repos/{config.GITHUB_REPO_OWNER}/"
        f"{config.GITHUB_REPO_NAME}/contents/{path}"
    )

    for attempt in range(MAX_RETRIES):
        # 获取最新 SHA
        _, sha = _cache.get(path)
        if sha is None:
            # 缓存中没有 SHA，先读一次
            _, sha = await read_json(path)

        try:
            async with httpx.AsyncClient(timeout=15) as client:
                payload: dict[str, Any] = {
                    "message": message,
                    "content": content_b64,
                }
                # 文件已存在时需要 SHA
                if sha:
                    payload["sha"] = sha

                resp = await client.put(
                    url, headers=_get_headers(), json=payload
                )

                if resp.status_code in (200, 201):
                    # 写入成功，更新缓存
                    new_sha = resp.json()["content"]["sha"]
                    _cache.set(path, data, new_sha)
                    return True

                elif resp.status_code == 409:
                    # SHA 冲突，清除缓存后重试
                    logger.warning(
                        f"GitHub 写入 SHA 冲突 (attempt {attempt + 1}/{MAX_RETRIES})，重试..."
                    )
                    _cache.invalidate(path)
                    continue

                elif resp.status_code == 422:
                    # 可能是 SHA 过期，清除缓存后重试
                    logger.warning(
                        f"GitHub 写入 422 (attempt {attempt + 1}/{MAX_RETRIES})，重试..."
                    )
                    _cache.invalidate(path)
                    continue

                else:
                    logger.error(
                        f"GitHub 写入失败: {resp.status_code} {resp.text}"
                    )
                    return False

        except Exception as e:
            logger.error(f"GitHub 写入异常: {e}")
            return False

    logger.error(f"GitHub 写入失败：超过最大重试次数 ({MAX_RETRIES})")
    return False


# ============================================================
# 便捷接口：Agent 注册表
# ============================================================

async def read_registry() -> dict:
    """读取全局 Agent 注册表"""
    data, _ = await read_json(REGISTRY_PATH)
    return data


async def write_registry(data: dict, message: str = "") -> bool:
    """写入全局 Agent 注册表"""
    if not message:
        message = "⚒️ TianGong: update agent registry"
    return await write_json(REGISTRY_PATH, data, message)


# ============================================================
# 便捷接口：修仙者档案
# ============================================================

async def read_cultivators() -> dict:
    """读取全局修仙者档案"""
    data, _ = await read_json(CULTIVATORS_PATH)
    return data


async def write_cultivators(data: dict, message: str = "") -> bool:
    """写入全局修仙者档案"""
    if not message:
        message = "⚒️ TianGong: update cultivator profiles"
    return await write_json(CULTIVATORS_PATH, data, message)
