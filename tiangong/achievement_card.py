"""Conversation-native visual achievement cards for TianGong users."""

from __future__ import annotations

import base64
import html
from dataclasses import dataclass

from .cultivator import (
    CultivatorProfile,
    build_cultivator_next_action,
    calculate_profile_snapshot_power,
    get_profile_realm_gate_checks,
)
from .install_bridge import format_candidate_join_lines
from .realm import MAX_STAGE, get_next_realm


@dataclass(frozen=True)
class AchievementTheme:
    """SVG palette for a visual achievement card."""

    background: str
    surface: str
    surface_2: str
    text: str
    muted: str
    accent: str
    accent_2: str
    accent_3: str
    line: str


THEMES: dict[str, AchievementTheme] = {
    "celestial": AchievementTheme(
        background="#10131a",
        surface="#171c26",
        surface_2="#202838",
        text="#f5f7fb",
        muted="#aab4c5",
        accent="#f3c96b",
        accent_2="#7dd3fc",
        accent_3="#f472b6",
        line="#30394a",
    ),
    "light": AchievementTheme(
        background="#f6f2ea",
        surface="#ffffff",
        surface_2="#edf4f7",
        text="#1e293b",
        muted="#64748b",
        accent="#b7791f",
        accent_2="#0f766e",
        accent_3="#be185d",
        line="#d7dee8",
    ),
}


def _theme(name: str) -> AchievementTheme:
    return THEMES.get(str(name or "celestial").strip().lower(), THEMES["celestial"])


def _x(value: object) -> str:
    return html.escape(str(value), quote=True)


def _clean_username(username: str) -> str:
    return " ".join(str(username or "").strip().lstrip("@").split())


def _svg_text(value: str, *, x: int, y: int, size: int, fill: str, weight: int = 500) -> str:
    return (
        f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" '
        f'fill="{fill}">{_x(value)}</text>'
    )


def _truncate(value: str, limit: int) -> str:
    text = " ".join(str(value or "").split())
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 1)].rstrip() + "…"


def _gate_summary(profile: CultivatorProfile) -> tuple[str, str]:
    next_realm = get_next_realm(profile.realm)
    if next_realm is None:
        return "Top realm reached", "Keep proving value through artifacts, reviews, quests, and public evidence."

    checks = get_profile_realm_gate_checks(profile, next_realm)
    if not checks:
        return f"Next: {next_realm.name_cn}", next_realm.tribulation_cn

    passed = sum(1 for check in checks if check.passed)
    first_missing = next((check for check in checks if not check.passed), None)
    if first_missing is None:
        detail = "All known gates are ready; continue with the breakthrough action."
    else:
        detail = f"{first_missing.label}: {first_missing.current}/{first_missing.required}"
    return f"Next: {next_realm.name_cn} · {passed}/{len(checks)} gates", detail


def _progress_width(profile: CultivatorProfile) -> int:
    if profile.stage <= 0:
        return 8
    return max(8, min(380, int(380 * profile.stage / MAX_STAGE)))


def render_achievement_card_svg(profile: CultivatorProfile, *, theme: str = "celestial") -> str:
    """Render a deterministic SVG achievement card from one real cultivator profile."""
    palette = _theme(theme)
    realm = profile.realm
    snapshot_power = calculate_profile_snapshot_power(profile)
    gate_title, gate_detail = _gate_summary(profile)
    next_action = _truncate(build_cultivator_next_action(profile).replace("`", ""), 54)
    sect = profile.sect or "Independent cultivator"
    stage = f"{profile.stage}/{MAX_STAGE}" if profile.stage > 0 else f"0/{MAX_STAGE}"
    progress_width = _progress_width(profile)
    username = _clean_username(profile.username) or "unknown"

    cards = [
        ("Spirit Power", str(profile.spirit_power), palette.accent),
        ("Artifacts", str(profile.agent_count), palette.accent_2),
        ("Reviews", str(profile.reviews_given), palette.accent_3),
        ("Refinements", str(profile.refinement_count), palette.accent),
        ("Quests", str(profile.quests_completed), palette.accent_2),
        ("Snapshot Power", str(snapshot_power), palette.accent_3),
    ]

    card_nodes: list[str] = []
    for index, (label, value, color) in enumerate(cards):
        col = index % 3
        row = index // 3
        x = 56 + col * 292
        y = 294 + row * 92
        card_nodes.extend(
            [
                f'<rect x="{x}" y="{y}" width="252" height="68" rx="14" fill="{palette.surface_2}" stroke="{palette.line}"/>',
                _svg_text(label, x=x + 18, y=y + 26, size=16, fill=palette.muted, weight=500),
                _svg_text(value, x=x + 18, y=y + 54, size=24, fill=color, weight=760),
            ]
        )

    return "\n".join(
        [
            '<svg xmlns="http://www.w3.org/2000/svg" width="980" height="560" viewBox="0 0 980 560" role="img">',
            f"<title>TianGong Achievement Card for @{_x(username)}</title>",
            "<desc>Conversation-native visual achievement card generated from a TianGong cultivator profile.</desc>",
            "<style>",
            "text{font-family:Inter,Segoe UI,Microsoft YaHei,Arial,sans-serif;letter-spacing:0}",
            "</style>",
            f'<rect width="980" height="560" rx="0" fill="{palette.background}"/>',
            f'<circle cx="878" cy="92" r="86" fill="{palette.accent}" opacity="0.16"/>',
            f'<circle cx="112" cy="462" r="102" fill="{palette.accent_2}" opacity="0.12"/>',
            f'<rect x="34" y="34" width="912" height="492" rx="24" fill="{palette.surface}" stroke="{palette.line}"/>',
            _svg_text("TianGong Achievement Card", x=56, y=82, size=22, fill=palette.muted, weight=650),
            _svg_text(f"@{username}", x=56, y=136, size=46, fill=palette.text, weight=800),
            _svg_text(f"{realm.symbol} {realm.name_cn} · {realm.name_en}", x=56, y=184, size=25, fill=palette.accent, weight=760),
            _svg_text(_truncate(realm.description_en, 62), x=56, y=220, size=18, fill=palette.muted, weight=520),
            f'<rect x="56" y="246" width="380" height="12" rx="6" fill="{palette.surface_2}"/>',
            f'<rect x="56" y="246" width="{progress_width}" height="12" rx="6" fill="{palette.accent_2}"/>',
            _svg_text(f"Stage {stage}", x=456, y=260, size=17, fill=palette.muted, weight=620),
            f'<rect x="552" y="80" width="344" height="142" rx="18" fill="{palette.surface_2}" stroke="{palette.line}"/>',
            _svg_text(gate_title, x=578, y=122, size=22, fill=palette.text, weight=760),
            _svg_text(_truncate(gate_detail, 42), x=578, y=158, size=17, fill=palette.muted, weight=520),
            _svg_text(_truncate(f"Next action: {next_action}", 48), x=578, y=194, size=16, fill=palette.accent_2, weight=620),
            *card_nodes,
            f'<line x1="56" y1="476" x2="896" y2="476" stroke="{palette.line}"/>',
            _svg_text(f"Sect: {sect}", x=56, y=510, size=16, fill=palette.muted, weight=520),
            _svg_text("No downloads, rewards, referrals, or adoption metrics are invented.", x=504, y=510, size=16, fill=palette.muted, weight=520),
            "</svg>",
        ]
    )


def achievement_card_data_uri(svg: str) -> str:
    """Return a Markdown-safe SVG data URI."""
    encoded = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    return f"data:image/svg+xml;base64,{encoded}"


def format_achievement_card(profile: CultivatorProfile, *, theme: str = "celestial") -> str:
    """Format a chat-visible Markdown achievement card from a real profile."""
    username = _clean_username(profile.username)
    svg = render_achievement_card_svg(profile, theme=theme)
    realm = profile.realm
    snapshot_power = calculate_profile_snapshot_power(profile)
    data_uri = achievement_card_data_uri(svg)
    next_action = build_cultivator_next_action(profile)

    lines = [
        "# TianGong Achievement Card",
        "",
        f"![TianGong achievement card for @{username}]({data_uri})",
        "",
        "> Generated from the current TianGong cultivator profile.",
        "> This visual card does not invent downloads, rewards, referrals, retention, or off-chain adoption.",
        "",
        "## Snapshot",
        "",
        f"- Cultivator: @{username}",
        f"- Realm: {realm.symbol} {realm.name_cn} / {realm.name_en}",
        f"- Spirit Power: {profile.spirit_power}",
        f"- Artifacts: {profile.agent_count}",
        f"- Reviews: {profile.reviews_given}",
        f"- Refinements: {profile.refinement_count}",
        f"- Quests: {profile.quests_completed}",
        f"- Snapshot Power: {snapshot_power}",
        f"- Sect: {profile.sect or 'Independent cultivator'}",
        "",
        "## Next Action",
        "",
        f"- {next_action}",
        f"- Visual check: `achievement_card(username=\"{username}\")`",
        f"- Text profile: `my_realm(username=\"{username}\")`",
        "- Season chase: `leaderboard(type=\"season\")`",
        "",
        "## Share",
        "",
        "```text",
        (
            f"I generated my TianGong achievement card: @{username} is at {realm.name_en} "
            f"with {profile.spirit_power} Spirit Power, {profile.agent_count} artifacts, "
            f"and {snapshot_power} snapshot power."
        ),
        *format_candidate_join_lines(),
        f'Visual card: achievement_card(username="{username}")',
        "```",
    ]
    return "\n".join(lines)


def format_achievement_card_missing_username() -> str:
    """Return a no-fabrication recovery card when no identity is available."""
    return "\n".join(
        [
            "# TianGong Achievement Card",
            "",
            "> GitHub username is required.",
            "> No achievement card was generated, and no anonymous achievement was invented.",
            "",
            "## Retry",
            "",
            "- MCP: `achievement_card(username=\"your_github_username\")`",
            "- CLI: `tiangong-mcp achievement-card --username your_github_username`",
            "- Text profile fallback: `my_realm(username=\"your_github_username\")`",
        ]
    )
