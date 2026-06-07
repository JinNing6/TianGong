"""User-facing Agent Skill Pavilion contracts."""

from __future__ import annotations

from io import StringIO
from pathlib import Path

from tiangong.skill_scrolls import list_skill_scrolls

ROOT = Path(__file__).resolve().parents[1]


def test_skill_scrolls_are_portable_agent_skill_bundles():
    """Every shipped skill should export a standard SKILL.md plus UI metadata."""
    scrolls = list_skill_scrolls()

    assert {scroll.name for scroll in scrolls} == {
        "tiangong-first-forge",
        "tiangong-public-growth-operator",
        "tiangong-refinement-review",
    }
    for scroll in scrolls:
        skill_md = scroll.skill_markdown()
        openai_yaml = scroll.openai_yaml()

        assert skill_md.startswith("---\n")
        assert f"name: {scroll.name}\n" in skill_md
        assert "description: " in skill_md
        assert "\n---\n\n# " in skill_md
        assert "## Workflow" in skill_md
        assert "Do not invent" in skill_md or "without claiming fake" in skill_md
        assert "interface:" in openai_yaml
        assert f"Use ${scroll.name}" in openai_yaml


def test_cli_skill_pavilion_lists_shows_and_exports_skill_bundle(tmp_path):
    """Installed users should be able to discover and export a real skill folder."""
    from tiangong import cli

    stdout = StringIO()
    assert cli.main(["skill-pavilion", "--action", "list"], stdout=stdout) == 0
    listing = stdout.getvalue()
    assert "TianGong Skill Pavilion" in listing
    assert "tiangong-first-forge" in listing
    assert "skill_pavilion(action=\"list\")" in listing

    stdout = StringIO()
    assert cli.main(["skill-pavilion", "--action", "show", "--skill", "tiangong-first-forge"], stdout=stdout) == 0
    detail = stdout.getvalue()
    assert "# TianGong Skill Scroll: `tiangong-first-forge`" in detail
    assert "## SKILL.md" in detail
    assert "## agents/openai.yaml" in detail

    export_dir = tmp_path / "skills"
    stdout = StringIO()
    assert (
        cli.main(
            [
                "skill-pavilion",
                "--action",
                "export",
                "--skill",
                "tiangong-first-forge",
                "--output-dir",
                str(export_dir),
            ],
            stdout=stdout,
        )
        == 0
    )
    exported = export_dir / "tiangong-first-forge"
    assert (exported / "SKILL.md").read_text(encoding="utf-8").startswith("---\nname: tiangong-first-forge")
    assert "default_prompt" in (exported / "agents" / "openai.yaml").read_text(encoding="utf-8")


def test_cli_skill_pavilion_requires_output_dir_for_export():
    """Export should not silently write to an implicit location."""
    from tiangong import cli

    stdout = StringIO()
    assert cli.main(["skill-pavilion", "--action", "export", "--skill", "tiangong-first-forge"], stdout=stdout) == 0
    output = stdout.getvalue()

    assert "Missing `output_dir`; no files were written." in output
    assert "--output-dir ./tiangong-skills" in output


def test_mcp_and_readmes_expose_user_skill_pavilion():
    """The user-facing skill feature should be visible from MCP and public docs."""
    mcp_server = (ROOT / "tiangong" / "mcp_server.py").read_text(encoding="utf-8")

    assert "async def skill_pavilion" in mcp_server
    assert "format_skill_pavilion" in mcp_server

    for filename in ["README.md", "README.zh-CN.md"]:
        text = (ROOT / filename).read_text(encoding="utf-8")
        assert "skill-pavilion --action list" in text
        assert "skill_pavilion(action=\"list\")" in text
        assert "tiangong-first-forge" in text
        assert "SKILL.md" in text
        assert "agents/openai.yaml" in text
