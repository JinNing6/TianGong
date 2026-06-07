"""User-facing Agent Skill bundles distributed by TianGong."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SkillScroll:
    """A portable Agent Skill bundle that can be exported for end users."""

    name: str
    display_name: str
    short_description: str
    default_prompt: str
    description: str
    body: str

    def skill_markdown(self) -> str:
        description = json.dumps(self.description, ensure_ascii=False)
        return "\n".join(
            [
                "---",
                f"name: {self.name}",
                f"description: {description}",
                "---",
                "",
                self.body.strip(),
                "",
            ]
        )

    def openai_yaml(self) -> str:
        return "\n".join(
            [
                "interface:",
                f"  display_name: {json.dumps(self.display_name, ensure_ascii=False)}",
                f"  short_description: {json.dumps(self.short_description, ensure_ascii=False)}",
                f"  default_prompt: {json.dumps(self.default_prompt, ensure_ascii=False)}",
                "",
            ]
        )


FIRST_FORGE_BODY = """
# TianGong First Forge

## Goal

Guide a new user from installation to their first useful TianGong artifact without claiming fake progress.

## Workflow

1. Check installation.
   - Prefer `pip install -U tiangong-mcp` when PyPI is current.
   - If the user is on a maintainer preview path, use the current tag bridge supplied by `tiangong-mcp public-install-command`.

2. Configure MCP.
   - Add `tiangong-mcp` as the MCP server command.
   - Set `GITHUB_USERNAME` when the user wants a named cultivation profile.

3. Start cultivation.
   - Run `start_cultivation(username="<github-user>")`.
   - Read the returned install, first forge, proof-pack, and activation instructions.

4. Forge one real artifact.
   - Run `forge_agent(name="<agent-name>", description="<real capability>", creator="<github-user>")`.
   - Use a real artifact idea; do not create placeholder achievements.

5. Continue the loop.
   - Improve with `refine_agent`.
   - Publish with `publish_agent`.
   - Inspect progress with `my_realm`, `leaderboard`, and `treasure_pavilion`.
   - Record public proof only after a reviewable public URL exists.

## Completion

Finish with the exact commands run, the artifact id/name, and the next one or two TianGong actions.
"""


GROWTH_OPERATOR_BODY = """
# TianGong Public Growth Operator

## Goal

Close the real public growth flywheel for TianGong or a TianGong fork: install readiness, first public proof, activation evidence, and release safety.

## Workflow

1. Inspect the current loop.
   - Run `tiangong-mcp public-install-command`.
   - Run `tiangong-mcp public-launch-preflight --target-contributors 10`.
   - Run `tiangong-mcp public-growth-report --target-contributors 10`.

2. Separate proof from aspiration.
   - Count only real GitHub issues, pull requests, releases, PyPI state, and local ledger entries.
   - Do not invent downloads, contributors, reposts, referrals, approvals, rewards, or retention.

3. Route cold users correctly.
   - If PyPI latest equals the local release, share `pip install -U tiangong-mcp`.
   - If PyPI is stale or unverified, share the generated Git tag candidate bridge and say PyPI is not closed yet.

4. Build first public proof.
   - Run `tiangong-mcp public-proof-pack --target-contributors 10`.
   - Open real Growth/Share proof surfaces.
   - Record created public URLs with `record-growth-referral` and `record-share-attribution`.

5. Verify release readiness before claiming closure.
   - Run lint, tests, build, `twine check`, launch-assets, and release-boundary gates.
   - Confirm GitHub publish workflow success.
   - Confirm PyPI JSON latest and a fresh `python -m pip install --upgrade tiangong-mcp==<version>`.

## Completion

Report the weakest bridge, the evidence URLs, the install command users should copy, and the next measurable target.
"""


REFINEMENT_REVIEW_BODY = """
# TianGong Refinement Review

## Goal

Help contributors turn a rough AI Agent into a reviewable TianGong artifact improvement.

## Workflow

1. Locate the artifact.
   - Search with `treasure_pavilion(action="search", query="<topic>")`.
   - Inspect ownership, current description, and public context.

2. Create or claim a refinement path.
   - Browse tasks with `quest(action="browse")`.
   - Create a real task with `quest(action="post", artifact_name="<name>", request="<specific improvement>")`.
   - Claim only work the contributor can actually perform.

3. Submit concrete improvement.
   - Use `refine_agent(agent_id="<id>", changes="<specific changes>")`.
   - If using quest flow, submit with `quest(action="submit", ...)` and include a real public URL when available.

4. Review and infuse spirit.
   - Use `verify_refinement` for quest verification.
   - Use `infuse_spirit` only with real scoring evidence.

5. Feed the growth loop.
   - Share the improvement publicly after it exists.
   - Record attribution with `record_share_attribution` only after the public share URL is reviewable.
   - Do not invent review results, scores, public URLs, or contributor progress.

## Completion

Return the artifact, the improvement summary, the review status, and the next cultivation action.
"""


ACHIEVEMENT_CARD_BODY = """
# TianGong Achievement Card

## Goal

Show a user's TianGong realm, level, badge, rank, or achievement as a conversation-visible visual card.

## Trigger

Use this when the user asks about achievement, level, rank, badge, card, visual status, cultivation progress,
成就、等级、境界、排名、徽章、卡片、展示、可视化, or wants something shareable in chat.

## Workflow

1. Require identity.
   - If a GitHub username is known, use it.
   - If no username is available, ask for the GitHub username.
   - Do not invent an anonymous user, fake rank, fake Spirit Power, or fake adoption data.

2. Generate the visual card.
   - Run `achievement_card(username="<github-user>")`.
   - Prefer the returned Markdown SVG image for chat display.
   - If the client does not render data URI images, keep the Snapshot and Share sections visible.

3. Keep the loop actionable.
   - Mention `my_realm(username="<github-user>")` for the text profile.
   - Mention `check_tribulation(username="<github-user>")` for the next realm gate.
   - Mention `leaderboard(type="season")` when the user wants rank context.

## Completion

Return the rendered card, the real snapshot fields, and one next TianGong action.
"""


SKILL_SCROLLS: tuple[SkillScroll, ...] = (
    SkillScroll(
        name="tiangong-first-forge",
        display_name="TianGong First Forge",
        short_description="Start cultivation and forge the first AI artifact.",
        default_prompt="Use $tiangong-first-forge to help me install TianGong and forge my first artifact.",
        description=(
            "Use when a new TianGong user wants to install tiangong-mcp, configure MCP, start cultivation, "
            "forge their first AI Agent artifact, publish/refine it, or understand the first proof loop."
        ),
        body=FIRST_FORGE_BODY,
    ),
    SkillScroll(
        name="tiangong-public-growth-operator",
        display_name="TianGong Public Growth Operator",
        short_description="Close the public install and proof flywheel.",
        default_prompt="Use $tiangong-public-growth-operator to audit TianGong public launch readiness.",
        description=(
            "Use when operating TianGong public launch, PyPI/GitHub release readiness, public proof packs, "
            "activation/share ledgers, contributor targets, or growth flywheel closure without fabricated traction."
        ),
        body=GROWTH_OPERATOR_BODY,
    ),
    SkillScroll(
        name="tiangong-refinement-review",
        display_name="TianGong Refinement Review",
        short_description="Guide artifact refinement tasks and reviews.",
        default_prompt="Use $tiangong-refinement-review to turn an artifact improvement into a reviewable contribution.",
        description=(
            "Use when a TianGong contributor wants to find, claim, submit, verify, or share an AI Agent artifact "
            "refinement through quests, reviews, spirit infusion, and public attribution."
        ),
        body=REFINEMENT_REVIEW_BODY,
    ),
    SkillScroll(
        name="tiangong-achievement-card",
        display_name="TianGong Achievement Card",
        short_description="Show realm, rank, badge, and achievement cards in chat.",
        default_prompt="Use $tiangong-achievement-card to show my current TianGong achievement card.",
        description=(
            "Use when a TianGong user asks to see their level, realm, rank, badge, achievement, "
            "visual card, share card, or cultivation status in a conversation. Requires a real GitHub username."
        ),
        body=ACHIEVEMENT_CARD_BODY,
    ),
)


def list_skill_scrolls() -> tuple[SkillScroll, ...]:
    return SKILL_SCROLLS


def get_skill_scroll(name: str) -> SkillScroll | None:
    normalized = " ".join(str(name or "").strip().split()).lower().replace("_", "-").replace(" ", "-")
    for scroll in SKILL_SCROLLS:
        if scroll.name == normalized:
            return scroll
    return None


def format_skill_pavilion_list() -> str:
    lines = [
        "# TianGong Skill Pavilion",
        "",
        "> Portable Agent Skill scrolls for TianGong users.",
        "> These are real SKILL.md bundles users can export and install in compatible clients.",
        "",
        "| Skill | Best for | Export command |",
        "|---|---|---|",
    ]
    for scroll in SKILL_SCROLLS:
        lines.append(
            f"| `{scroll.name}` | {scroll.short_description} | "
            f"`tiangong-mcp skill-pavilion --action export --skill {scroll.name} --output-dir ./tiangong-skills` |"
        )
    lines.extend(
        [
            "",
            "## MCP Usage",
            "",
            "- List: `skill_pavilion(action=\"list\")`",
            "- Show: `skill_pavilion(action=\"show\", skill_name=\"tiangong-first-forge\")`",
            "- Export: `skill_pavilion(action=\"export\", skill_name=\"tiangong-first-forge\", output_dir=\"./tiangong-skills\")`",
        ]
    )
    return "\n".join(lines)


def format_skill_scroll_detail(scroll: SkillScroll) -> str:
    return "\n".join(
        [
            f"# TianGong Skill Scroll: `{scroll.name}`",
            "",
            f"> {scroll.short_description}",
            "",
            "## Export Command",
            "",
            "```bash",
            f"tiangong-mcp skill-pavilion --action export --skill {scroll.name} --output-dir ./tiangong-skills",
            "```",
            "",
            "## SKILL.md",
            "",
            "```markdown",
            scroll.skill_markdown().rstrip(),
            "```",
            "",
            "## agents/openai.yaml",
            "",
            "```yaml",
            scroll.openai_yaml().rstrip(),
            "```",
        ]
    )


def export_skill_scroll(scroll: SkillScroll, output_dir: str | Path, *, force: bool = False) -> Path:
    base = Path(output_dir).expanduser()
    skill_dir = base / scroll.name
    if skill_dir.exists() and not force:
        raise FileExistsError(f"{skill_dir} already exists; pass --force to overwrite this skill bundle")

    agents_dir = skill_dir / "agents"
    agents_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(scroll.skill_markdown(), encoding="utf-8")
    (agents_dir / "openai.yaml").write_text(scroll.openai_yaml(), encoding="utf-8")
    return skill_dir.resolve()


def format_skill_pavilion(
    *,
    action: str = "list",
    skill_name: str = "",
    output_dir: str = "",
    force: bool = False,
) -> str:
    normalized_action = str(action or "list").strip().lower()
    if normalized_action in {"list", "browse"}:
        return format_skill_pavilion_list()

    scroll = get_skill_scroll(skill_name)
    if scroll is None:
        names = ", ".join(f"`{item.name}`" for item in SKILL_SCROLLS)
        return "\n".join(
            [
                "# TianGong Skill Pavilion",
                "",
                f"> Unknown or missing skill: `{skill_name or 'missing'}`.",
                f"> Available skills: {names}.",
                "",
                "Use `tiangong-mcp skill-pavilion --action list` to browse all user-facing skill scrolls.",
            ]
        )

    if normalized_action == "show":
        return format_skill_scroll_detail(scroll)

    if normalized_action == "export":
        if not output_dir:
            return "\n".join(
                [
                    f"# TianGong Skill Export: `{scroll.name}`",
                    "",
                    "> Missing `output_dir`; no files were written.",
                    "",
                    "Retry:",
                    "",
                    "```bash",
                    f"tiangong-mcp skill-pavilion --action export --skill {scroll.name} --output-dir ./tiangong-skills",
                    "```",
                ]
            )
        try:
            skill_dir = export_skill_scroll(scroll, output_dir, force=force)
        except OSError as exc:
            return "\n".join(
                [
                    f"# TianGong Skill Export Failed: `{scroll.name}`",
                    "",
                    f"> {exc}",
                    "> No traction, installation, or user adoption was claimed.",
                ]
            )
        return "\n".join(
            [
                f"# TianGong Skill Exported: `{scroll.name}`",
                "",
                f"> Wrote portable Agent Skill bundle to `{skill_dir}`.",
                "",
                "## Files",
                "",
                f"- `{skill_dir / 'SKILL.md'}`",
                f"- `{skill_dir / 'agents' / 'openai.yaml'}`",
                "",
                "## Install",
                "",
                "Copy or import that folder into any Agent Skills compatible client.",
            ]
        )

    return "\n".join(
        [
            "# TianGong Skill Pavilion",
            "",
            f"> Unknown action: `{action}`.",
            "> Use `list`, `show`, or `export`.",
        ]
    )
