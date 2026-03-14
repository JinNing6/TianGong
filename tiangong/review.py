"""
⚒️ 天工 TianGong — 淬炼令系统（Phase 2）
淬炼/Review 机制：发布需求 → 认领任务 → 提交修改 → 验证完成

这是渡劫任务的核心验证机制。
"""

from __future__ import annotations

import json
import logging
import time

import httpx

from .config import config
from .artifact_system import DIMENSIONS

logger = logging.getLogger("tiangong.review")

# GitHub API
GITHUB_API = "https://api.github.com"


def _get_headers() -> dict:
    headers = {"Accept": "application/vnd.github.v3+json"}
    if config.GITHUB_TOKEN:
        headers["Authorization"] = f"token {config.GITHUB_TOKEN}"
    return headers


# ============================================================
# 灵力灌注（给法宝评分）
# ============================================================

async def infuse_spirit(
    artifact_name: str,
    reviewer: str,
    scores: dict[str, int],
    comment: str = "",
) -> str:
    """
    灌注灵力——对法宝进行六维评分。

    Args:
        artifact_name: 法宝名称
        reviewer: 评价者用户名
        scores: 六维评分 {"inscription": 8, "formation": 7, ...}
        comment: 评价内容

    Returns:
        评价结果消息
    """
    # 校验评分格式
    for dim in DIMENSIONS:
        key = dim["key"]
        if key not in scores:
            return f"⚠️ 缺少维度 `{key}`（{dim['name_cn']}）的评分"
        val = scores[key]
        if not isinstance(val, int) or val < 1 or val > 10:
            return f"⚠️ `{key}` 评分必须为 1-10 的整数，当前: {val}"

    # 检查评价资格
    from .cultivator import can_review, record_review, get_cultivator
    can, msg = can_review(reviewer)
    if not can:
        return msg

    # 不能自评
    # (需要从 marketplace 元数据中获取创建者信息来检查)

    # 获取评价者信息
    reviewer_profile = get_cultivator(reviewer)

    # 计算灵力值
    avg_score = sum(scores.values()) / len(scores)
    spirit_value = avg_score * reviewer_profile.review_weight

    # 记录评价
    record_review(reviewer)

    # 通过 GitHub Issue 评论记录评价
    review_data = {
        "reviewer": reviewer,
        "reviewer_realm": reviewer_profile.realm.name_cn,
        "reviewer_weight": reviewer_profile.review_weight,
        "scores": scores,
        "spirit_value": round(spirit_value, 1),
        "comment": comment,
        "timestamp": time.time(),
    }

    # 发布评价到 GitHub Issue
    posted = await _post_review_to_issue(artifact_name, review_data)

    # 更新法宝灵力值（给法宝创作者加灵力）
    from .cultivator import update_cultivator_stats
    # 评价者也获得少量灵力奖励（鼓励评价）
    update_cultivator_stats(username=reviewer, spirit_delta=1, review_delta=1)

    # 格式化评分展示
    lines = [
        f"# 💫 灵力灌注成功！",
        "",
        f"法宝: `{artifact_name}`",
        f"评价者: @{reviewer} ({reviewer_profile.realm.symbol} {reviewer_profile.realm.name_cn})",
        f"评价权重: ×{reviewer_profile.review_weight}",
        "",
        "### 六维评分",
        "",
        "| 维度 | 评分 |",
        "|------|------|",
    ]

    for dim in DIMENSIONS:
        key = dim["key"]
        score = scores[key]
        bar = "█" * score + "░" * (10 - score)
        lines.append(f"| {dim['name_cn']} | {bar} {score}/10 |")

    lines.extend([
        "",
        f"**六维均分**: {avg_score:.1f}",
        f"**灌注灵力**: +{spirit_value:.1f}",
    ])

    if posted:
        lines.append(f"\n> 评价已记录到 GitHub Issue")

    return "\n".join(lines)


async def _post_review_to_issue(artifact_name: str, review_data: dict) -> bool:
    """将评价发布到对应的 GitHub Issue 评论"""
    if not config.GITHUB_TOKEN:
        return False

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            # 搜索法宝对应的 Issue
            search_url = f"{GITHUB_API}/search/issues"
            search_query = (
                f"{artifact_name} "
                f"repo:{config.GITHUB_REPO_OWNER}/{config.GITHUB_REPO_NAME} "
                f"label:artifact"
            )
            resp = await client.get(
                search_url,
                headers=_get_headers(),
                params={"q": search_query, "per_page": 1},
            )

            if resp.status_code != 200:
                return False

            items = resp.json().get("items", [])
            if not items:
                return False

            issue_number = items[0]["number"]

            # 发布评论
            comment_body = _format_review_comment(review_data)
            resp = await client.post(
                f"{GITHUB_API}/repos/{config.GITHUB_REPO_OWNER}/{config.GITHUB_REPO_NAME}"
                f"/issues/{issue_number}/comments",
                headers=_get_headers(),
                json={"body": comment_body},
            )
            return resp.status_code == 201

    except Exception as e:
        logger.warning(f"发布评价失败: {e}")
        return False


def _format_review_comment(review_data: dict) -> str:
    """格式化评价 Issue 评论"""
    scores = review_data["scores"]
    lines = [
        f"## 💫 灵力灌注 by @{review_data['reviewer']}",
        "",
        f"- 境界: {review_data['reviewer_realm']}",
        f"- 权重: ×{review_data['reviewer_weight']}",
        f"- 灵力值: +{review_data['spirit_value']}",
        "",
        "| 维度 | 评分 |",
        "|------|------|",
    ]

    for dim in DIMENSIONS:
        key = dim["key"]
        score = scores.get(key, 0)
        lines.append(f"| {dim['name_cn']} | {'⭐' * score} ({score}/10) |")

    if review_data.get("comment"):
        lines.extend(["", f"> {review_data['comment']}"])

    return "\n".join(lines)


# ============================================================
# 淬炼令系统（发布需求 → 认领 → 提交 → 验证）
# ============================================================

async def post_refine_quest(
    artifact_name: str,
    quest_description: str,
    creator: str,
    current_code_url: str = "",
) -> str:
    """
    发布淬炼令——悬赏帮忙改进法宝。

    Args:
        artifact_name: 法宝名称
        quest_description: 需求描述
        creator: 发布者
        current_code_url: 当前代码链接

    Returns:
        发布结果消息
    """
    if not config.GITHUB_TOKEN:
        return "⚠️ 未配置 GITHUB_TOKEN"

    issue_title = f"🔥 [淬炼令] {artifact_name} — {quest_description[:50]}"
    issue_body = f"""## 🔥 淬炼令

- **法宝**: `{artifact_name}`
- **发布者**: @{creator}
- **需求**: {quest_description}
- **代码链接**: {current_code_url or '见法宝目录'}

### 认领方式

在此 Issue 下评论"认领"即可。完成后提交代码链接和说明。

### 验证方式

发布者审核通过 → 淬炼完成 → 认领者获得灵力奖励。

---
> 此淬炼令通过天工 MCP `post_refine_quest` 工具发布。
"""

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                f"{GITHUB_API}/repos/{config.GITHUB_REPO_OWNER}/{config.GITHUB_REPO_NAME}/issues",
                headers=_get_headers(),
                json={
                    "title": issue_title,
                    "body": issue_body,
                    "labels": ["refine-quest", "help-wanted"],
                },
            )

            if resp.status_code == 201:
                issue_data = resp.json()
                return (
                    f"# ✅ 淬炼令已发布！\n\n"
                    f"- Issue: #{issue_data['number']}\n"
                    f"- 链接: {issue_data['html_url']}\n\n"
                    "> 等待有缘人认领此令。"
                )
            else:
                return f"❌ 发布失败: {resp.status_code}"

    except Exception as e:
        return f"❌ 发布失败: {e}"


async def claim_refine_quest(
    quest_issue_number: int,
    refiner: str,
) -> str:
    """
    认领淬炼令。

    Args:
        quest_issue_number: 淬炼令 Issue 编号
        refiner: 认领者

    Returns:
        认领结果
    """
    if not config.GITHUB_TOKEN:
        return "⚠️ 未配置 GITHUB_TOKEN"

    comment_body = f"""## 🙋 认领淬炼令

- **认领者**: @{refiner}

> 我已认领此淬炼令，将尽快提交优化成果。
"""

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                f"{GITHUB_API}/repos/{config.GITHUB_REPO_OWNER}/{config.GITHUB_REPO_NAME}"
                f"/issues/{quest_issue_number}/comments",
                headers=_get_headers(),
                json={"body": comment_body},
            )

            if resp.status_code == 201:
                return (
                    f"# 🙋 认领成功！\n\n"
                    f"- Issue: #{quest_issue_number}\n"
                    f"- 认领者: @{refiner}\n\n"
                    "> 请在完成后使用 `complete_quest` 提交成果。"
                )
            else:
                return f"❌ 认领失败: {resp.status_code}"

    except Exception as e:
        return f"❌ 认领失败: {e}"


async def complete_refine_quest(
    quest_issue_number: int,
    refiner: str,
    solution_description: str,
) -> str:
    """
    提交淬炼成果。

    Args:
        quest_issue_number: 淬炼令 Issue 编号
        refiner: 淬炼者
        solution_description: 解决方案描述

    Returns:
        提交结果
    """
    if not config.GITHUB_TOKEN:
        return "⚠️ 未配置 GITHUB_TOKEN"

    comment_body = f"""## ✅ 淬炼完成提交

- **淬炼者**: @{refiner}
- **解决方案**: {solution_description}

> 请发布者审核。审核通过后请关闭此 Issue。
"""

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                f"{GITHUB_API}/repos/{config.GITHUB_REPO_OWNER}/{config.GITHUB_REPO_NAME}"
                f"/issues/{quest_issue_number}/comments",
                headers=_get_headers(),
                json={"body": comment_body},
            )

            if resp.status_code == 201:
                # 给淬炼者加灵力
                from .cultivator import update_cultivator_stats
                update_cultivator_stats(
                    username=refiner,
                    spirit_delta=5,
                    quest_delta=1,
                    refinement_delta=1,
                )

                return (
                    f"# ✅ 淬炼成果已提交！\n\n"
                    f"- Issue: #{quest_issue_number}\n"
                    f"- 灵力奖励: +5\n\n"
                    "> 等待发布者审核确认。"
                )
            else:
                return f"❌ 提交失败: {resp.status_code}"

    except Exception as e:
        return f"❌ 提交失败: {e}"
