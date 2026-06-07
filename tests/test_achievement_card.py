"""Conversation-native achievement card contracts."""

from __future__ import annotations

import base64
from dataclasses import asdict
from io import StringIO
from pathlib import Path

from tiangong.achievement_card import (
    achievement_card_data_uri,
    format_achievement_card,
    format_achievement_card_missing_username,
    render_achievement_card_svg,
)
from tiangong.cultivator import CultivatorProfile

ROOT = Path(__file__).resolve().parents[1]


def _profile() -> CultivatorProfile:
    return CultivatorProfile(
        username="visual-crafter",
        spirit_power=180,
        agent_count=5,
        refinement_count=3,
        reviews_given=5,
        quests_completed=1,
        sect="Celestial Forge",
        sect_role="inner",
    )


def test_achievement_card_renders_decodable_svg_from_real_profile():
    """The visual card should be a deterministic SVG from real cultivator fields."""
    profile = _profile()

    svg = render_achievement_card_svg(profile)
    data_uri = achievement_card_data_uri(svg)
    decoded = base64.b64decode(data_uri.split(",", 1)[1]).decode("utf-8")

    assert svg.startswith("<svg ")
    assert decoded == svg
    assert "visual-crafter" in svg
    assert profile.realm.name_cn in svg
    assert str(profile.spirit_power) in svg
    assert str(profile.agent_count) in svg
    assert "Snapshot Power" in svg
    assert "No downloads, rewards, referrals, or adoption metrics are invented." in svg

    mortal_svg = render_achievement_card_svg(CultivatorProfile(username="mortal"))
    assert "Stage 0/9" in mortal_svg


def test_achievement_card_markdown_is_chat_visible_and_non_fabricating():
    """MCP clients should receive a Markdown image plus proof wording and next action."""
    profile = _profile()

    output = format_achievement_card(profile)

    assert "# TianGong Achievement Card" in output
    assert "![TianGong achievement card for @visual-crafter](data:image/svg+xml;base64," in output
    assert "Generated from the current TianGong cultivator profile" in output
    assert "does not invent downloads" in output
    assert "achievement_card(username=\"visual-crafter\")" in output
    assert "leaderboard(type=\"season\")" in output


def test_achievement_card_missing_username_asks_for_identity_without_fake_data():
    """A missing identity should not create an anonymous achievement."""
    output = format_achievement_card_missing_username()

    assert "GitHub username is required" in output
    assert "No achievement card was generated" in output
    assert "achievement_card(username=\"your_github_username\")" in output


def test_cli_achievement_card_prints_visual_markdown(monkeypatch):
    """Terminal users should be able to generate the same user-facing visual card."""
    import tiangong.cultivator as cultivator_module
    from tiangong import cli

    profile_data = asdict(_profile())

    async def fake_load():
        return {"visual-crafter": profile_data}

    async def fake_save(_data, message=""):
        raise AssertionError(f"achievement-card should not save existing profile data: {message}")

    monkeypatch.setattr(cultivator_module, "_load_all_cultivators", fake_load)
    monkeypatch.setattr(cultivator_module, "_save_all_cultivators", fake_save)

    stdout = StringIO()
    assert cli.main(["achievement-card", "--username", "visual-crafter"], stdout=stdout) == 0
    output = stdout.getvalue()

    assert "TianGong Achievement Card" in output
    assert "data:image/svg+xml;base64," in output
    assert "visual-crafter" in output


async def test_mcp_achievement_card_exposes_visual_surface(monkeypatch):
    """MCP users should not need terminal access to show a visual achievement card."""
    from tiangong import mcp_server

    async def fake_get_cultivator(username: str):
        profile = _profile()
        profile.username = username
        return profile

    monkeypatch.setattr(mcp_server, "get_cultivator", fake_get_cultivator)

    output = await mcp_server.achievement_card(username="visual-crafter")

    assert "TianGong Achievement Card" in output
    assert "data:image/svg+xml;base64," in output
    assert "visual-crafter" in output
    assert "not invent downloads" in output


def test_readmes_document_conversation_achievement_card():
    """The public docs should make visual achievements discoverable to all users."""
    for filename in ["README.md", "README.zh-CN.md"]:
        text = (ROOT / filename).read_text(encoding="utf-8")
        assert "achievement_card(username=\"your_github_username\")" in text
        assert "tiangong-mcp achievement-card --username your_github_username" in text
        assert "data:image/svg+xml;base64" in text
