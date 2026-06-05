"""First-session onboarding tests for the TianGong growth loop."""

from __future__ import annotations

import pytest


def test_start_cultivation_card_turns_install_into_first_action():
    """The first screen should move a new user from install to a real forge action."""
    from tiangong.onboarding import format_start_cultivation

    result = format_start_cultivation(username="newbie", artifact_name="newbie-first-artifact")

    assert "起火入道" in result
    assert "当前没有伪造修仙档案" in result
    assert 'python -m pip install --upgrade "tiangong-mcp @ git+https://github.com/JinNing6/TianGong.git@v0.1.11"' in result
    assert "tiangong-mcp public-install-command" in result
    assert "pip install -U tiangong-mcp" in result
    assert "pip install tiangong-mcp" not in result
    assert '"command": "tiangong-mcp"' in result
    assert '"GITHUB_USERNAME": "newbie"' in result
    assert '`forge_agent(name="newbie-first-artifact"' in result
    assert '`growth_flywheel()`' in result
    assert '`growth_campaign()`' in result
    assert '`public_growth_report()`' in result
    assert '`public_launch_preflight()`' in result
    assert '`public_proof_pack()`' in result
    assert "https://github.com/JinNing6/TianGong/issues/new?" in result
    assert "template=tiangong-growth-flywheel.yml" in result
    assert "start_cultivation(username=\"newbie\"" in result


def test_start_cultivation_sanitizes_empty_inputs_without_fake_identity():
    """Empty arguments should stay actionable without inventing a real GitHub identity."""
    from tiangong.onboarding import format_start_cultivation

    result = format_start_cultivation(username="", artifact_name="")

    assert "@your_github_username" in result
    assert '`forge_agent(name="your-first-artifact"' in result
    assert "不要把占位符当成真实修仙者档案" in result
    assert "growth_flywheel()" in result
    assert "growth_campaign()" in result
    assert "public_growth_report()" in result
    assert "public_launch_preflight()" in result
    assert "public_proof_pack()" in result


@pytest.mark.asyncio
async def test_mcp_start_cultivation_exposes_first_session_card(monkeypatch):
    """The public MCP server should expose the first-session onboarding surface."""
    from tiangong import mcp_server

    monkeypatch.setattr(mcp_server.config, "GITHUB_USERNAME", "newbie")

    result = await mcp_server.start_cultivation()

    assert "起火入道" in result
    assert '`forge_agent(name="newbie-first-artifact"' in result
    assert "`growth_flywheel()`" in result
    assert "`growth_campaign()`" in result
    assert "`public_growth_report()`" in result
    assert "`public_launch_preflight()`" in result
    assert "`public_proof_pack()`" in result
    assert "TianGong" in result
