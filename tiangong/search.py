"""
⚒️ 天工 TianGong — 寻宝阁搜索引擎（Phase 2）
统一关键词搜索，一个 query 匹配品阶、类别、框架、创作者等所有维度

用法示例：
    treasure_pavilion(query="仙器")        → 按品阶
    treasure_pavilion(query="crewai")     → 按框架
    treasure_pavilion(query="@JinNing6")  → 按创作者
    treasure_pavilion(query="数据分析")    → 按类别/标签
    treasure_pavilion(query="仙器 crewai") → 组合搜索
    treasure_pavilion()                   → 热门推荐
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import httpx

from .config import config
from .artifact_system import GRADE_BY_NAME

logger = logging.getLogger("tiangong.search")

# 已知品阶名称（用于关键词类型判断）
GRADE_KEYWORDS = {"凡器", "灵器", "宝器", "仙器", "神器", "太古神器"}

# 已知框架名（用于关键词类型判断）
KNOWN_FRAMEWORKS = {
    "crewai", "langchain", "langgraph", "openai", "openai-agents",
    "anthropic", "autogen", "dspy", "llamaindex", "haystack",
    "agno", "strands", "pydantic-ai", "litellm", "groq", "mistralai",
}

# GitHub API
GITHUB_API = "https://api.github.com"


def _get_headers() -> dict:
    """获取 GitHub API 请求头"""
    headers = {"Accept": "application/vnd.github.v3+json"}
    if config.GITHUB_TOKEN:
        headers["Authorization"] = f"token {config.GITHUB_TOKEN}"
    return headers


def classify_query(query: str) -> dict:
    """
    对用户输入的查询进行分类。

    智能识别查询中包含的品阶、创作者、框架等筛选条件。

    Returns:
        {
            "grade_filter": str | None,
            "creator_filter": str | None,
            "framework_filter": str | None,
            "text_query": str,
        }
    """
    result = {
        "grade_filter": None,
        "creator_filter": None,
        "framework_filter": None,
        "text_query": "",
    }

    if not query:
        return result

    remaining_words = []

    for word in query.strip().split():
        # 1. 品阶匹配
        if word in GRADE_KEYWORDS:
            result["grade_filter"] = word
        # 2. 创作者匹配（@开头）
        elif word.startswith("@"):
            result["creator_filter"] = word[1:]
        # 3. 框架匹配
        elif word.lower() in KNOWN_FRAMEWORKS:
            result["framework_filter"] = word.lower()
        else:
            remaining_words.append(word)

    result["text_query"] = " ".join(remaining_words)

    return result


async def search_marketplace(
    query: str = "",
    top_n: int = 20,
) -> list[dict]:
    """
    在寻宝阁中搜索法宝。

    搜索范围：
    1. 常驻法宝体（marketplace/ 目录）
    2. 瞬时法宝体（GitHub Issues with label:artifact）

    Args:
        query: 搜索关键词
        top_n: 返回前 N 个结果

    Returns:
        法宝列表
    """
    filters = classify_query(query)
    results = []

    # 搜索常驻法宝体（marketplace/ 目录）
    resident_artifacts = await _search_resident_artifacts(filters)
    results.extend(resident_artifacts)

    # 搜索瞬时法宝体（GitHub Issues）
    transient_artifacts = await _search_transient_artifacts(filters)
    results.extend(transient_artifacts)

    # 排序: 品阶降序 → 灵力降序 → 名称字母序
    grade_order = {"太古神器": 5, "神器": 4, "仙器": 3, "宝器": 2, "灵器": 1, "凡器": 0}
    results.sort(key=lambda a: (
        -grade_order.get(a.get("grade_name", "凡器"), 0),
        -a.get("spirit_power", 0),
        a.get("name", ""),
    ))

    return results[:top_n]


async def _search_resident_artifacts(filters: dict) -> list[dict]:
    """搜索常驻法宝体（marketplace/）"""
    results = []

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            dir_url = (
                f"{GITHUB_API}/repos/{config.GITHUB_REPO_OWNER}/{config.GITHUB_REPO_NAME}"
                f"/contents/{config.MARKETPLACE_DIR}"
            )
            resp = await client.get(dir_url, headers=_get_headers())

            if resp.status_code != 200:
                return results

            items = resp.json()
            if not isinstance(items, list):
                return results

            for item in items:
                if item["type"] != "dir":
                    continue

                artifact = {
                    "name": item["name"],
                    "layer": "🏛️ 常驻",
                    "source": "marketplace",
                    "grade_name": "凡器",
                    "spirit_power": 0,
                }

                # 应用过滤
                if _match_filters(artifact, filters):
                    results.append(artifact)

    except Exception as e:
        logger.warning(f"搜索常驻法宝失败: {e}")

    return results


async def _search_transient_artifacts(filters: dict) -> list[dict]:
    """搜索瞬时法宝体（GitHub Issues）"""
    results = []

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            params = {
                "labels": "artifact",
                "state": "open",
                "per_page": 50,
            }

            # 如果有文本关键词，加到搜索
            if filters.get("text_query"):
                # 使用 GitHub Search API
                search_url = f"{GITHUB_API}/search/issues"
                search_query = (
                    f"{filters['text_query']} "
                    f"repo:{config.GITHUB_REPO_OWNER}/{config.GITHUB_REPO_NAME} "
                    f"label:artifact is:open"
                )
                resp = await client.get(
                    search_url,
                    headers=_get_headers(),
                    params={"q": search_query, "per_page": 50},
                )
            else:
                # 列出所有 artifact Issues
                resp = await client.get(
                    f"{GITHUB_API}/repos/{config.GITHUB_REPO_OWNER}/{config.GITHUB_REPO_NAME}/issues",
                    headers=_get_headers(),
                    params=params,
                )

            if resp.status_code != 200:
                return results

            data = resp.json()
            issues = data.get("items", data) if isinstance(data, dict) else data

            for issue in issues:
                if not isinstance(issue, dict):
                    continue

                artifact = {
                    "name": _extract_artifact_name(issue.get("title", "")),
                    "layer": "🔮 瞬时",
                    "source": f"issue#{issue.get('number', '?')}",
                    "grade_name": "凡器",
                    "spirit_power": 0,
                    "issue_url": issue.get("html_url", ""),
                    "creator": issue.get("user", {}).get("login", "unknown"),
                    "status": "⏳ 待炼化",
                }

                if _match_filters(artifact, filters):
                    results.append(artifact)

    except Exception as e:
        logger.warning(f"搜索瞬时法宝失败: {e}")

    return results


def _extract_artifact_name(title: str) -> str:
    """从 Issue 标题中提取法宝名"""
    # 格式: 🔮 [法宝] 搜索灵蛇 (search-serpent)
    if "(" in title and ")" in title:
        return title.split("(")[-1].split(")")[0].strip()
    return title.replace("🔮", "").replace("[法宝]", "").strip()


def _match_filters(artifact: dict, filters: dict) -> bool:
    """检查法宝是否匹配过滤条件"""
    # 品阶过滤
    if filters.get("grade_filter"):
        if artifact.get("grade_name") != filters["grade_filter"]:
            return False

    # 创作者过滤
    if filters.get("creator_filter"):
        if artifact.get("creator", "").lower() != filters["creator_filter"].lower():
            return False

    # 框架过滤
    if filters.get("framework_filter"):
        if artifact.get("framework", "").lower() != filters["framework_filter"]:
            return False

    # 文本模糊匹配
    if filters.get("text_query"):
        text = filters["text_query"].lower()
        name = artifact.get("name", "").lower()
        desc = artifact.get("description", "").lower()
        if text not in name and text not in desc:
            return False

    return True


# ============================================================
# 格式化展示
# ============================================================

def format_search_results(artifacts: list[dict], query: str = "") -> str:
    """格式化搜索结果"""
    title = "🏛️ 寻宝阁"
    if query:
        title += f" — 「{query}」"

    if not artifacts:
        return (
            f"## {title}\n\n"
            "> 未找到匹配的法宝。试试其他关键词？\n\n"
            "**搜索技巧**：\n"
            "- 品阶: `仙器`、`宝器`\n"
            "- 框架: `crewai`、`langchain`\n"
            "- 创作者: `@JinNing6`\n"
            "- 组合: `仙器 crewai`"
        )

    lines = [
        f"## {title}",
        "",
        f"共找到 {len(artifacts)} 件法宝：",
        "",
        "| 法宝 | 品阶 | 层级 | 来源 | 灵力 |",
        "|------|------|------|------|------|",
    ]

    for a in artifacts:
        grade = a.get("grade_name", "凡器")
        grade_symbol = {"太古神器": "🔴", "神器": "🟡", "仙器": "🟣", "宝器": "🔵", "灵器": "🟢", "凡器": "⚪"}.get(grade, "⚪")
        lines.append(
            f"| {a['name']} | {grade_symbol} {grade} | {a['layer']} | {a['source']} | {a.get('spirit_power', 0)} |"
        )

    return "\n".join(lines)
