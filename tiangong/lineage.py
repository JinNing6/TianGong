"""
⚒️ 天工 TianGong — 传承谱系追踪（Phase 2）
法宝之间的引用/继承/fork 关系追踪

三种传承关系:
- fork: 🔱 分支传承（基于别人的法宝改造）
- inspired: 💡 悟道传承（受启发从零重写）
- depends: 🔗 法宝联动（运行时依赖其他法宝）
"""

from __future__ import annotations

import json
import logging

import httpx

from .config import config

logger = logging.getLogger("tiangong.lineage")

GITHUB_API = "https://api.github.com"

# 传承关系类型
LINEAGE_TYPES = {
    "fork": {"symbol": "🔱", "name_cn": "分支传承", "spirit_bonus": 2},
    "inspired": {"symbol": "💡", "name_cn": "悟道传承", "spirit_bonus": 1},
    "depends": {"symbol": "🔗", "name_cn": "法宝联动", "spirit_bonus": 3},
}


def _get_headers() -> dict:
    headers = {"Accept": "application/vnd.github.v3+json"}
    if config.GITHUB_TOKEN:
        headers["Authorization"] = f"token {config.GITHUB_TOKEN}"
    return headers


def parse_lineage_from_meta(meta: dict) -> dict | None:
    """
    从法宝元数据中解析传承信息。

    tiangong.yaml 中的相关字段:
        lineage:
          parent: search-serpent
          parent_version: 1.0.0
          type: fork
        dependencies:
          - data-dragon
          - translate-fox
    """
    lineage_info = meta.get("lineage", {})
    deps = meta.get("dependencies", [])

    if not lineage_info and not deps:
        return None

    result = {
        "parent": lineage_info.get("parent"),
        "parent_version": lineage_info.get("parent_version"),
        "lineage_type": lineage_info.get("type", "fork"),
        "dependencies": deps,
    }

    return result


async def get_artifact_lineage(artifact_name: str) -> dict:
    """
    获取法宝的完整传承谱系。

    Returns:
        {
            "name": "search-serpent",
            "children": [
                {"name": "search-serpent-pro", "type": "fork", "children": [...]},
                {"name": "deep-search", "type": "inspired", "children": []},
            ],
            "dependents": ["data-pipeline"],
        }
    """
    tree = {
        "name": artifact_name,
        "children": [],
        "dependents": [],
    }

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            # 搜索所有 Issue 中引用此法宝的
            search_url = f"{GITHUB_API}/search/issues"
            search_query = (
                f"{artifact_name} "
                f"repo:{config.GITHUB_REPO_OWNER}/{config.GITHUB_REPO_NAME} "
                f"label:artifact"
            )
            resp = await client.get(
                search_url,
                headers=_get_headers(),
                params={"q": search_query, "per_page": 50},
            )

            if resp.status_code == 200:
                items = resp.json().get("items", [])
                for issue in items:
                    title = issue.get("title", "")
                    body = issue.get("body", "")
                    # 检查是否在 body 中声明了传承关系
                    if f"parent: {artifact_name}" in body or f"fork 自 {artifact_name}" in body:
                        child_name = _extract_artifact_name(title)
                        if child_name != artifact_name:
                            tree["children"].append({
                                "name": child_name,
                                "type": "fork",
                                "issue": issue.get("number"),
                            })
                    elif f"inspired: {artifact_name}" in body:
                        child_name = _extract_artifact_name(title)
                        if child_name != artifact_name:
                            tree["children"].append({
                                "name": child_name,
                                "type": "inspired",
                                "issue": issue.get("number"),
                            })
                    elif f"depends: {artifact_name}" in body or f"- {artifact_name}" in body:
                        child_name = _extract_artifact_name(title)
                        if child_name != artifact_name:
                            tree["dependents"].append(child_name)

    except Exception as e:
        logger.warning(f"获取传承谱系失败: {e}")

    return tree


def _extract_artifact_name(title: str) -> str:
    """从 Issue 标题中提取法宝名"""
    if "(" in title and ")" in title:
        return title.split("(")[-1].split(")")[0].strip()
    return title.replace("🔮", "").replace("[法宝]", "").strip()


def format_lineage_tree(tree: dict, indent: int = 0) -> str:
    """格式化传承谱系展示"""
    name = tree["name"]
    lines = []

    if indent == 0:
        lines.append(f"# 📜 {name} 传承谱系")
        lines.append("")

    prefix = "│   " * indent
    connector = "├── " if indent > 0 else ""

    lines.append(f"{prefix}{connector}{name}")

    for child in tree.get("children", []):
        child_type = child.get("type", "fork")
        type_info = LINEAGE_TYPES.get(child_type, LINEAGE_TYPES["fork"])
        child_prefix = "│   " * (indent + 1)
        lines.append(f"{child_prefix}├── {type_info['symbol']} {child['name']}")

    dependents = tree.get("dependents", [])
    if dependents:
        lines.append("")
        lines.append(f"依赖此法宝的: {', '.join(dependents)}")

    if not tree.get("children") and not dependents:
        lines.append("")
        lines.append("> 暂无传承记录。")

    return "\n".join(lines)


def calculate_lineage_bonus(artifact_name: str, tree: dict) -> int:
    """
    计算传承带来的灵力加成。

    Rules:
    - 被 fork: +2 灵力
    - 被声明为灵感来源: +1 灵力
    - 被声明为依赖: +3 灵力
    """
    bonus = 0

    for child in tree.get("children", []):
        child_type = child.get("type", "fork")
        type_info = LINEAGE_TYPES.get(child_type, LINEAGE_TYPES["fork"])
        bonus += type_info["spirit_bonus"]

    for _ in tree.get("dependents", []):
        bonus += LINEAGE_TYPES["depends"]["spirit_bonus"]

    return bonus
