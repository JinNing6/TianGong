"""
⚒️ 天工 TianGong — 淬炼令系统（Phase 2）
淬炼/Review 机制：发布需求 → 认领任务 → 提交修改 → 验证完成

这是渡劫任务的核心验证机制。
"""

from __future__ import annotations

import logging
import re
import time

import httpx

from .activation import format_share_attribution_command
from .artifact_system import DIMENSIONS
from .config import config
from .install_bridge import format_candidate_join_text

logger = logging.getLogger("tiangong.review")

# GitHub API
GITHUB_API = "https://api.github.com"
REFINE_QUEST_SCHEMA_VERSION = 1
REFINE_QUEST_SCHEMA_MARKER = "<!-- tiangong:refine-quest:v1 -->"
REFINE_CLAIM_SCHEMA_MARKER = "<!-- tiangong:refine-claim:v1 -->"
REFINE_SUBMIT_SCHEMA_MARKER = "<!-- tiangong:refine-submit:v1 -->"
REFINE_VERIFY_SCHEMA_MARKER = "<!-- tiangong:refine-verify:v1 -->"


def _get_headers() -> dict:
    headers = {"Accept": "application/vnd.github.v3+json"}
    if config.GITHUB_TOKEN:
        headers["Authorization"] = f"token {config.GITHUB_TOKEN}"
    return headers


def _build_infuse_share_block(
    artifact_name: str,
    reviewer: str,
    reviewer_realm: str,
    avg_score: float,
    spirit_value: float,
) -> str:
    """Build a paste-ready share block for successful artifact appraisals."""
    share_text = (
        f"我在 TianGong 为法宝 `{artifact_name}` 灌注灵力：@{reviewer} "
        f"以 {reviewer_realm} 境界完成六维鉴定，均分 {avg_score:.1f}，"
        f"灌注灵力 +{spirit_value:.1f}。帮别人变强，也是自己的修行。"
    )

    return (
        "\n\n---\n\n"
        "## 📣 复制分享\n\n"
        "```text\n"
        f"{share_text}\n"
        f"{format_candidate_join_text()}\n"
        "```\n\n"
        "## 下一步\n\n"
        "- 继续鉴定: `infuse_spirit` with `artifact_name=\"community-artifact\"`\n"
        "- 查看修行名片: `my_realm()`\n"
        "- 冲击赛季天榜: `leaderboard(type=\"season\")`\n"
        f"- 记录公开分享归因: {format_share_attribution_command(contribution='infuse', actor=reviewer, artifact_name=artifact_name)}"
    )


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
    from .cultivator import can_review, get_cultivator, record_review
    can, msg = await can_review(reviewer)
    if not can:
        return msg

    # 不能自评
    # (需要从 marketplace 元数据中获取创建者信息来检查)

    # 获取评价者信息
    reviewer_profile = await get_cultivator(reviewer)

    # 计算灵力值
    avg_score = sum(scores.values()) / len(scores)
    spirit_value = avg_score * reviewer_profile.review_weight

    # 记录评价
    await record_review(reviewer)

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
    await update_cultivator_stats(username=reviewer, spirit_delta=1, review_delta=1)

    # 格式化评分展示
    lines = [
        "# 💫 灵力灌注成功！",
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
        lines.append("\n> 评价已记录到 GitHub Issue")

    return "\n".join(lines) + _build_infuse_share_block(
        artifact_name=artifact_name,
        reviewer=reviewer,
        reviewer_realm=reviewer_profile.realm.name_cn,
        avg_score=avg_score,
        spirit_value=spirit_value,
    )


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

def _build_quest_share_block(
    artifact_name: str,
    quest_description: str,
    creator: str,
    issue_number: int,
    issue_url: str,
) -> str:
    """Build a paste-ready recruitment block for new refinement quests."""
    share_text = (
        f"我在 TianGong 发布淬炼令：请道友帮 `{artifact_name}` 淬炼"
        f"「{quest_description}」。发布者 @{creator}，Issue #{issue_number}: {issue_url}"
    )

    return (
        "\n\n---\n\n"
        "## 📣 复制分享\n\n"
        "```text\n"
        f"{share_text}\n"
        f"{format_candidate_join_text()}\n"
        "```\n\n"
        "## 下一步\n\n"
        f"- 认领此令: `quest(action=\"claim\", quest_issue_number={issue_number})`\n"
        "- 浏览悬赏: `quest(action=\"browse\")`\n"
        f"- 发布者验收: `verify_refinement` with `quest_issue_number={issue_number}`\n"
        f"- 记录公开分享归因: {format_share_attribution_command(contribution='quest_post', actor=creator, artifact_name=artifact_name, share_url=issue_url)}"
    )


def _build_claim_share_block(quest_issue_number: int, refiner: str) -> str:
    """Build a paste-ready share block for claimed refinement quests."""
    share_text = (
        f"我在 TianGong 认领了淬炼令 Issue #{quest_issue_number}：@{refiner} "
        "正在打磨一件社区法宝。接令、淬炼、验收，都是修行。"
    )

    return (
        "\n\n---\n\n"
        "## 📣 复制分享\n\n"
        "```text\n"
        f"{share_text}\n"
        f"{format_candidate_join_text()}\n"
        "```\n\n"
        "## 下一步\n\n"
        f"- 提交成果: `quest(action=\"submit\", quest_issue_number={quest_issue_number}, solution=\"...\")`\n"
        "- 继续接令: `quest(action=\"browse\")`\n"
        f"- 查看进展: Issue #{quest_issue_number}\n"
        f"- 记录公开分享归因: {format_share_attribution_command(contribution='quest_claim', actor=refiner, artifact_name=f'quest-{quest_issue_number}')}"
    )


def _build_submit_share_block(
    quest_issue_number: int,
    refiner: str,
    solution_description: str,
) -> str:
    """Build a paste-ready share block for submitted refinement work."""
    share_text = (
        f"我在 TianGong 提交了淬炼成果：@{refiner} 完成 Issue #{quest_issue_number}，"
        f"方案是「{solution_description}」。请发布者验收，淬炼通过即入修行战绩。"
    )

    return (
        "\n\n---\n\n"
        "## 📣 复制分享\n\n"
        "```text\n"
        f"{share_text}\n"
        f"{format_candidate_join_text()}\n"
        "```\n\n"
        "## 下一步\n\n"
        f"- 发布者验收: `verify_refinement` with `quest_issue_number={quest_issue_number}`\n"
        f"- 查看修行名片: `my_realm(username=\"{refiner}\")`\n"
        "- 继续接令: `quest(action=\"browse\")`\n"
        f"- 记录公开分享归因: {format_share_attribution_command(contribution='quest_submit', actor=refiner, artifact_name=f'quest-{quest_issue_number}')}"
    )


def _build_verify_approval_share_block(
    quest_issue_number: int,
    refiner: str,
    reviewer: str,
) -> str:
    """Build a paste-ready share block for approved refinement quests."""
    share_text = (
        f"我在 TianGong 完成一张淬炼令：@{reviewer} 验收通过 Issue #{quest_issue_number}，"
        f"@{refiner} 获得 +50 灵力。社区悬赏、真实交付、即时晋升。"
    )

    return (
        "\n\n---\n\n"
        "## 📣 复制分享\n\n"
        "```text\n"
        f"{share_text}\n"
        f"{format_candidate_join_text()}\n"
        "```\n\n"
        "## 下一步\n\n"
        f"- 查看修行名片: `my_realm(username=\"{refiner}\")`\n"
        "- 冲击赛季天榜: `leaderboard(type=\"season\")`\n"
        "- 继续接令: `quest(action=\"browse\")`\n"
        f"- 记录公开分享归因: {format_share_attribution_command(contribution='quest_verify', actor=reviewer, artifact_name=f'quest-{quest_issue_number}')}"
    )


def _build_bounty_board_share_block(items: list[dict], total_count: int) -> str:
    """Build a paste-ready share block for the live refinement bounty board."""
    top_numbers = ", ".join(f"#{item['number']}" for item in items[:3])
    share_text = (
        f"我在 TianGong 看到 {total_count} 张正在招募的淬炼令，"
        f"最新悬赏 {top_numbers}，每张完成后 +50 灵力。接令即修行。"
    )

    return (
        "\n\n---\n\n"
        "## 📣 复制分享\n\n"
        "```text\n"
        f"{share_text}\n"
        f"{format_candidate_join_text()}\n"
        "```\n\n"
        "## 下一步\n\n"
        "- 认领悬赏: `quest(action=\"claim\", quest_issue_number=...)`\n"
        "- 发布悬赏: `quest(action=\"post\")`\n"
        "- 刷新悬赏榜: `quest(action=\"browse\")`"
    )


def _one_line(value: str, fallback: str = "") -> str:
    """Keep canonical Issue fields parseable as single-line Markdown list values."""
    text = str(value or fallback).strip()
    return " ".join(text.splitlines())


def build_refine_quest_issue_body(
    artifact_name: str,
    quest_description: str,
    creator: str,
    current_code_url: str = "",
) -> str:
    """Build the canonical public Issue body for a refinement quest."""
    artifact = _one_line(artifact_name)
    description = _one_line(quest_description)
    creator_name = _one_line(creator)
    code_url = _one_line(current_code_url, fallback="见法宝目录")

    return f"""## 🔥 淬炼令

{REFINE_QUEST_SCHEMA_MARKER}

- **法宝**: `{artifact}`
- **发布者**: @{creator_name}
- **需求**: {description}
- **代码链接**: {code_url}
- **来源命令**: `quest(action="post")`

### 认领方式

在此 Issue 下评论"认领"即可。完成后提交代码链接和说明。

### 验证方式

发布者审核通过 → 淬炼完成 → 认领者获得灵力奖励。

---
> 此淬炼令通过天工 MCP `quest(action="post")` 工具发布。
"""


def _parse_markdown_list_field(body: str, label: str) -> str:
    pattern = rf"^- \*\*{re.escape(label)}\*\*: (.+)$"
    match = re.search(pattern, body, flags=re.MULTILINE)
    if not match:
        raise ValueError(f"missing refine quest field: {label}")
    return match.group(1).strip()


def _strip_inline_code(value: str) -> str:
    if len(value) >= 2 and value.startswith("`") and value.endswith("`"):
        return value[1:-1]
    return value


def _strip_github_mention(value: str) -> str:
    text = value.strip()
    if text.startswith("@"):
        return text[1:]
    return text


def parse_refine_quest_issue_body(body: str) -> dict[str, str | int]:
    """Parse a canonical refinement quest Issue body generated by TianGong."""
    if REFINE_QUEST_SCHEMA_MARKER not in body:
        raise ValueError("missing refine quest schema marker")

    creator = _parse_markdown_list_field(body, "发布者")
    if creator.startswith("@"):
        creator = creator[1:]

    return {
        "schema_version": REFINE_QUEST_SCHEMA_VERSION,
        "artifact_name": _strip_inline_code(_parse_markdown_list_field(body, "法宝")),
        "creator": creator,
        "quest_description": _parse_markdown_list_field(body, "需求"),
        "current_code_url": _parse_markdown_list_field(body, "代码链接"),
        "source_command": _strip_inline_code(_parse_markdown_list_field(body, "来源命令")),
    }


def build_claim_refine_quest_comment_body(refiner: str) -> str:
    """Build the canonical public comment body for claiming a refinement quest."""
    refiner_name = _one_line(refiner)

    return f"""## 🙋 认领淬炼令

{REFINE_CLAIM_SCHEMA_MARKER}

- **认领者**: @{refiner_name}
- **状态**: 进行中
- **来源命令**: `quest(action="claim")`
- **下一步命令**: `quest(action="submit")`

> 我已认领此淬炼令，将尽快提交优化成果。

---
> 此认领通过天工 MCP `quest(action="claim")` 工具提交。
> 完成后请使用 `quest(action="submit")` 提交成果。
"""


def parse_claim_refine_quest_comment_body(body: str) -> dict[str, str | int]:
    """Parse a canonical refinement-quest claim comment generated by TianGong."""
    if REFINE_CLAIM_SCHEMA_MARKER not in body:
        raise ValueError("missing refine claim schema marker")

    return {
        "schema_version": REFINE_QUEST_SCHEMA_VERSION,
        "refiner": _strip_github_mention(_parse_markdown_list_field(body, "认领者")),
        "status": _parse_markdown_list_field(body, "状态"),
        "source_command": _strip_inline_code(_parse_markdown_list_field(body, "来源命令")),
        "next_command": _strip_inline_code(_parse_markdown_list_field(body, "下一步命令")),
    }


def build_submit_refinement_comment_body(refiner: str, solution_description: str) -> str:
    """Build the canonical public comment body for submitting refinement work."""
    refiner_name = _one_line(refiner)
    solution = _one_line(solution_description)

    return f"""## 🛠️ 提交淬炼成果

{REFINE_SUBMIT_SCHEMA_MARKER}

- **淬炼者**: @{refiner_name}
- **解决方案**: {solution}
- **来源命令**: `quest(action="submit")`
- **下一步命令**: `verify_refinement`

> 请发布者使用 `verify_refinement` 审核。审核通过后此令即告完成。

---
> 此成果通过天工 MCP `quest(action="submit")` 工具提交。
"""


def parse_submit_refinement_comment_body(body: str) -> dict[str, str | int]:
    """Parse a canonical refinement submission comment generated by TianGong."""
    if REFINE_SUBMIT_SCHEMA_MARKER not in body:
        raise ValueError("missing refine submit schema marker")

    return {
        "schema_version": REFINE_QUEST_SCHEMA_VERSION,
        "refiner": _strip_github_mention(_parse_markdown_list_field(body, "淬炼者")),
        "solution_description": _parse_markdown_list_field(body, "解决方案"),
        "source_command": _strip_inline_code(_parse_markdown_list_field(body, "来源命令")),
        "next_command": _strip_inline_code(_parse_markdown_list_field(body, "下一步命令")),
    }


def build_verify_refinement_comment_body(
    refiner: str,
    reviewer: str,
    is_approved: bool,
    feedback: str = "",
) -> str:
    """Build the canonical public comment body for verifying refinement work."""
    refiner_name = _one_line(refiner)
    reviewer_name = _one_line(reviewer)
    feedback_text = _one_line(feedback, fallback="无")
    result = "✅ 通过" if is_approved else "❌ 未通过"
    follow_up = (
        "> 淬炼令已圆满完成！淬炼者将获得 +50 灵力奖励。"
        if is_approved
        else "> 成果尚需打磨，请淬炼者根据反馈修改后再次提交。"
    )

    return f"""## ⚖️ 淬炼成果审核

{REFINE_VERIFY_SCHEMA_MARKER}

- **审核者**: @{reviewer_name}
- **淬炼者**: @{refiner_name}
- **结果**: {result}
- **反馈**: {feedback_text}
- **来源命令**: `verify_refinement`

{follow_up}

---
> 此审核通过天工 MCP `verify_refinement` 工具提交。"""


def parse_verify_refinement_comment_body(body: str) -> dict[str, str | int | bool]:
    """Parse a canonical refinement verification comment generated by TianGong."""
    if REFINE_VERIFY_SCHEMA_MARKER not in body:
        raise ValueError("missing refine verify schema marker")

    result_value = _parse_markdown_list_field(body, "结果")
    is_approved = "通过" in result_value and "未通过" not in result_value

    return {
        "schema_version": REFINE_QUEST_SCHEMA_VERSION,
        "reviewer": _strip_github_mention(_parse_markdown_list_field(body, "审核者")),
        "refiner": _strip_github_mention(_parse_markdown_list_field(body, "淬炼者")),
        "is_approved": is_approved,
        "result": "通过" if is_approved else "未通过",
        "feedback": _parse_markdown_list_field(body, "反馈"),
        "source_command": _strip_inline_code(_parse_markdown_list_field(body, "来源命令")),
    }


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
    issue_body = build_refine_quest_issue_body(
        artifact_name=artifact_name,
        quest_description=quest_description,
        creator=creator,
        current_code_url=current_code_url,
    )

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
                ) + _build_quest_share_block(
                    artifact_name=artifact_name,
                    quest_description=quest_description,
                    creator=creator,
                    issue_number=issue_data["number"],
                    issue_url=issue_data["html_url"],
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

    comment_body = build_claim_refine_quest_comment_body(refiner)

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
                    f"> 请在完成后使用 `quest(action=\"submit\", quest_issue_number={quest_issue_number}, solution=\"...\")` "
                    "提交成果。"
                ) + _build_claim_share_block(
                    quest_issue_number=quest_issue_number,
                    refiner=refiner,
                )
            else:
                return f"❌ 认领失败: {resp.status_code}"

    except Exception as e:
        return f"❌ 认领失败: {e}"


async def submit_refinement(
    quest_issue_number: int,
    refiner: str,
    solution_description: str,
) -> str:
    """提交淬炼成果"""
    if not config.GITHUB_TOKEN:
        return "⚠️ 未配置 GITHUB_TOKEN"

    comment_body = build_submit_refinement_comment_body(refiner, solution_description)

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
                    f"# 🛠️ 淬炼成果已提交！\n\n"
                    f"- Issue: #{quest_issue_number}\n\n"
                    f"> 等待发布者审核确认（使用 verify_refinement）。"
                ) + _build_submit_share_block(
                    quest_issue_number=quest_issue_number,
                    refiner=refiner,
                    solution_description=solution_description,
                )
            else:
                return f"❌ 提交失败: {resp.status_code}"

    except Exception as e:
        return f"❌ 提交失败: {e}"


async def verify_refinement(
    quest_issue_number: int,
    refiner: str,
    reviewer: str,
    is_approved: bool,
    feedback: str = "",
) -> str:
    """审核淬炼成果"""
    if not config.GITHUB_TOKEN:
        return "⚠️ 未配置 GITHUB_TOKEN"

    comment_body = build_verify_refinement_comment_body(
        refiner=refiner,
        reviewer=reviewer,
        is_approved=is_approved,
        feedback=feedback,
    )

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                f"{GITHUB_API}/repos/{config.GITHUB_REPO_OWNER}/{config.GITHUB_REPO_NAME}"
                f"/issues/{quest_issue_number}/comments",
                headers=_get_headers(),
                json={"body": comment_body},
            )

            if resp.status_code == 201:
                if is_approved:
                    # 给淬炼者加灵力
                    from .cultivator import update_cultivator_stats
                    await update_cultivator_stats(
                        username=refiner,
                        spirit_delta=50,
                        quest_delta=1,
                        refinement_delta=1,
                    )

                    # 尝试关闭 Issue
                    await client.patch(
                        f"{GITHUB_API}/repos/{config.GITHUB_REPO_OWNER}/{config.GITHUB_REPO_NAME}/issues/{quest_issue_number}",
                        headers=_get_headers(),
                        json={"state": "closed", "state_reason": "completed"},
                    )

                    return (
                        f"# ✅ 淬炼审核通过！\n\n"
                        f"- Issue: #{quest_issue_number}\n"
                        f"- 淬炼者: @{refiner} 已获得 +50 灵力奖励！\n\n"
                        "> 淬炼令已圆满完成并关闭。"
                    ) + _build_verify_approval_share_block(
                        quest_issue_number=quest_issue_number,
                        refiner=refiner,
                        reviewer=reviewer,
                    )
                else:
                    return (
                        f"# ❌ 淬炼需要修改！\n\n"
                        f"- Issue: #{quest_issue_number}\n"
                        f"- 已通知 @{refiner} 继续改进。\n"
                    )
            else:
                return f"❌ 审核评价失败: {resp.status_code}"

    except Exception as e:
        return f"❌ 审核评价失败: {e}"


async def browse_quests(limit: int = 10) -> str:
    """浏览待认领的淬炼令"""
    if not config.GITHUB_TOKEN:
        return "⚠️ 未配置 GITHUB_TOKEN"

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            search_url = f"{GITHUB_API}/search/issues"
            search_query = (
                f"repo:{config.GITHUB_REPO_OWNER}/{config.GITHUB_REPO_NAME} "
                f"state:open is:issue label:refine-quest"
            )
            resp = await client.get(
                search_url,
                headers=_get_headers(),
                params={"q": search_query, "per_page": limit, "sort": "created", "order": "desc"},
            )

            if resp.status_code != 200:
                return f"❌ 获取淬炼令失败: {resp.status_code}"

            payload = resp.json()
            items = payload.get("items", [])
            if not items:
                return "📭 目前没有待认领的淬炼令。"

            total_count = payload.get("total_count", len(items))
            lines = [
                "# 📜 悬赏天榜 (Refinement Bounties)",
                "",
                "当前数据源: GitHub open Issues 快照",
                "筛选: `state:open is:issue label:refine-quest`",
                "悬赏: +50 灵力 / 完成验收的淬炼令",
                "",
                f"当前有 {len(items)} 个活跃的淬炼令（GitHub 匹配总数: {total_count}）：",
                "",
                "| 编号 | 标题 | 发布者 | 发布时间 | 奖励 | 认领命令 | 悬赏连接 |",
                "|------|------|--------|----------|------|----------|----------|",
            ]

            for item in items:
                author = item["user"]["login"]
                date = item["created_at"][:10]
                claim_command = f"`quest(action=\"claim\", quest_issue_number={item['number']})`"
                lines.append(
                    f"| #{item['number']} | {item['title']} | @{author} | {date} | +50 灵力 | "
                    f"{claim_command} | [点击查看]({item['html_url']}) |"
                )

            return "\n".join(lines) + _build_bounty_board_share_block(items, total_count)

    except Exception as e:
        return f"❌ 获取淬炼令失败: {e}"
