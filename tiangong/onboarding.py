"""First-session onboarding cards for TianGong."""

from __future__ import annotations

from .growth import build_growth_issue_url


def _clean_slug(value: str, fallback: str) -> str:
    text = str(value or "").strip()
    if not text:
        return fallback
    cleaned = "".join(char if char.isalnum() or char in "-_" else "-" for char in text)
    cleaned = "-".join(part for part in cleaned.split("-") if part)
    return cleaned[:80] or fallback


def _json_mcp_config(username: str) -> str:
    return (
        "{\n"
        '  "mcpServers": {\n'
        '    "tiangong": {\n'
        '      "command": "tiangong-mcp",\n'
        '      "env": {\n'
        f'        "GITHUB_USERNAME": "{username}"\n'
        "      }\n"
        "    }\n"
        "  }\n"
        "}"
    )


def format_start_cultivation(username: str = "", artifact_name: str = "") -> str:
    """Return a first-session card that turns install into a real first action."""
    normalized_username = _clean_slug(username, "your_github_username")
    display_username = f"@{normalized_username}"
    first_artifact = _clean_slug(artifact_name, f"{normalized_username}-first-artifact")
    if normalized_username == "your_github_username":
        first_artifact = "your-first-artifact"

    placeholder_warning = (
        "- 占位符提醒: 不要把占位符当成真实修仙者档案；把 `your_github_username` 换成真实 GitHub 用户名后再开炉。"
        if normalized_username == "your_github_username"
        else "- 身份来源: 使用你提供的 GitHub 用户名生成首件法宝命令；真正档案只会在执行公开工具后写入。"
    )
    growth_issue_url = build_growth_issue_url(
        bottleneck_label="首件法宝激活",
        campaign_hook=f"邀请 {display_username} 完成 TianGong 第一件法宝开炉",
        real_data_context="首会话起火入道入口: 尚未写入修仙档案，等待用户执行真实 forge_agent 命令",
    )

    lines = [
        "# ⚒️ 起火入道",
        "",
        f"> 首会话快照: {display_username} 准备踏入 TianGong。当前没有伪造修仙档案、灵力奖励或法宝注册。",
        "> 只有执行 `forge_agent`、`publish_agent`、`infuse_spirit` 等公开工具后，才会产生真实修炼记录。",
        "",
        "## 1. 安装",
        "",
        "```bash",
        "pip install tiangong-mcp",
        "```",
        "",
        "## 2. MCP 配置",
        "",
        "```json",
        _json_mcp_config(normalized_username),
        "```",
        "",
        "## 3. 第一件本命法宝",
        "",
        (
            f'- 开炉炼器: `forge_agent(name="{first_artifact}", '
            f'description="{display_username} 的第一件 TianGong 本命法宝", creator="{normalized_username}")`'
        ),
        f"- 查看修行名片: `my_realm(username=\"{normalized_username}\")`",
        "- 复查增长飞轮: `growth_flywheel()`",
        "- 发起 72 小时爆发战役: `growth_campaign()`",
        "- 验证公开牵引力: `public_growth_report()`",
        "- 公开发布预检: `public_launch_preflight()`",
        f"- 打开增长招募 Issue: {growth_issue_url}",
        placeholder_warning,
        "",
        "## 4. 复制入门战书",
        "",
        "```text",
        (
            f"我准备在 TianGong 起火入道：{display_username} 将开炉第一件本命法宝 `{first_artifact}`。"
            "不伪造灵力，不伪造档案，执行 forge_agent 后才算真正踏入修炼。"
        ),
        "加入修炼: pip install tiangong-mcp",
        f"首件法宝: forge_agent(name=\"{first_artifact}\", description=\"...\")",
        "复查飞轮: growth_flywheel()",
        "发起战役: growth_campaign()",
        "验证公开证明: public_growth_report()",
        "公开发布预检: public_launch_preflight()",
        f"增长招募: {growth_issue_url}",
        "```",
        "",
        "## 5. 回到飞轮",
        "",
        "- 当前瓶颈: 首件法宝激活",
        "- 下一环: 发布出世 -> 鉴定回流 -> 淬炼复访 -> 悬赏闭环 -> 宗门/赛季",
        "- 发起战役: `growth_campaign()`",
        "- 验证公开证明: `public_growth_report()`",
        "- 公开发布预检: `public_launch_preflight()`",
        f"- 重新生成此卡: `start_cultivation(username=\"{normalized_username}\", artifact_name=\"{first_artifact}\")`",
    ]

    return "\n".join(lines)
