"""GitHub IssueOps surfaces for the TianGong growth loop."""

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
ISSUE_TEMPLATE_DIR = ROOT / ".github" / "ISSUE_TEMPLATE"
WORKFLOW = ROOT / ".github" / "workflows" / "issueops-onboarding.yml"


def _read_form(name: str) -> str:
    return (ISSUE_TEMPLATE_DIR / name).read_text(encoding="utf-8")


def test_issueops_yaml_files_are_parseable():
    """GitHub Issue Forms and workflows should be valid YAML before they are pushed live."""
    paths = sorted((ROOT / ".github").rglob("*.yml"))

    assert paths
    for path in paths:
        assert yaml.safe_load(path.read_text(encoding="utf-8")) is not None, path


def test_issueops_forms_cover_external_growth_routes():
    """Public GitHub forms should cover the missing acquisition loop surfaces."""
    expected = {
        "tiangong-refinement-quest.yml": ("tiangong:quest", "Artifact name", "Refinement request"),
        "tiangong-growth-flywheel.yml": ("tiangong:growth", "Growth bottleneck", "Campaign hook"),
        "tiangong-season-board.yml": ("tiangong:season", "Board request", "Campaign hook"),
        "tiangong-tournament.yml": ("tiangong:tournament", "Cup name", "Entry rule"),
        "tiangong-mentor-pact.yml": ("tiangong:mentor", "Mentor username", "Apprentice username"),
        "tiangong-sect-recruitment.yml": ("tiangong:sect", "Sect name", "Candidate username"),
        "tiangong-share-proof.yml": ("tiangong:share", "Contribution type", "Public share URL"),
    }

    for filename, (route_label, first_field, second_field) in expected.items():
        form = _read_form(filename)

        assert form.startswith("name: TianGong")
        assert route_label in form
        assert 'title: "[TianGong ' in form
        assert f"label: {first_field}" in form
        assert f"label: {second_field}" in form
        assert "type: markdown" in form


def test_issueops_workflow_is_comment_only_and_least_privilege():
    """IssueOps onboarding should not run project code or request broad token access."""
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert "issues: write" in workflow
    assert "contents: write" not in workflow
    assert "pull_request_target" not in workflow
    assert "actions/checkout" not in workflow
    assert "\n        run:" not in workflow
    assert "<!-- tiangong:issueops-onboarding:v1 -->" in workflow
    assert "does not checkout code, execute repository scripts" in workflow
    assert "_?no response_?" in workflow


def test_issueops_workflow_routes_forms_to_real_public_tools():
    """Every public route should point back to callable TianGong tools."""
    workflow = WORKFLOW.read_text(encoding="utf-8")

    for label in [
        "tiangong:quest",
        "tiangong:growth",
        "tiangong:season",
        "tiangong:tournament",
        "tiangong:mentor",
        "tiangong:sect",
        "tiangong:share",
    ]:
        assert label in workflow

    for command in [
        'record_growth_referral(route=',
        'quest(action="post"',
        'quest(action="browse")',
        'growth_flywheel()',
        'growth_campaign(campaign_name=',
        'target_contributors=${targetContributors}',
        'public_growth_report(record_snapshot=True, target_contributors=${targetContributors})',
        'public_launch_preflight(target_contributors=${targetContributors})',
        'public_proof_pack(target_contributors=${targetContributors})',
        'leaderboard(type="growth")',
        'share_attribution_report()',
        'leaderboard(type="share")',
        'leaderboard(type="season")',
        'leaderboard(type="tournament")',
        'leaderboard(type="tournament_recap")',
        'record_share_attribution(contribution=',
        'share_attribution_report()',
        'leaderboard(type="share")',
        'my_realm(username=',
        'sect(action="info"',
        'sect(action="join"',
        'leaderboard(type="sect")',
    ]:
        assert command in workflow


def test_issueops_workflow_comments_candidate_install_before_pypi_install():
    """The first public bot comment must not route cold visitors to the stale PyPI package."""
    workflow = WORKFLOW.read_text(encoding="utf-8")
    candidate = (
        'Current candidate install: `python -m pip install --upgrade '
        '"tiangong-mcp @ git+https://github.com/JinNing6/TianGong.git@v0.1.13"`'
    )
    canonical = "PyPI-current install after registry readiness: `pip install -U tiangong-mcp`"

    assert candidate in workflow
    assert "Install decision after installation: `tiangong-mcp public-install-command`" in workflow
    assert canonical in workflow
    assert "Install: `pip install tiangong-mcp`" not in workflow
    assert workflow.index(candidate) < workflow.index(canonical)


def test_issueops_workflow_records_external_return_before_next_commands():
    """IssueOps comments should make the external-to-MCP return measurable."""
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert "const issueUrl = issue.html_url;" in workflow
    assert 'record_growth_referral(route="${route.key}"' in workflow
    assert 'source_url="${issueUrl}"' in workflow
    assert 'issue_number=${issue.number}' in workflow
    assert "activation_funnel()" in workflow
    assert "growth_campaign(campaign_name=" in workflow
    assert "public_growth_report(record_snapshot=True, target_contributors=${targetContributors})" in workflow
    assert "public_launch_preflight(target_contributors=${targetContributors})" in workflow
    assert "public_proof_pack(target_contributors=${targetContributors})" in workflow
    assert "readPositiveIntegerField('Target contributors', 10)" in workflow
    assert "const targetContributors" in workflow
    assert 'share_url="${shareUrl}"' in workflow
    assert "share_attribution_report()" in workflow


def test_issueops_docs_expose_public_forms_and_workflow():
    """README claims should expose the GitHub forms and safe workflow."""
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    readme_cn = (ROOT / "README.zh-CN.md").read_text(encoding="utf-8")

    for text in (readme, readme_cn):
        assert ".github/ISSUE_TEMPLATE" in text
        assert ".github/workflows/issueops-onboarding.yml" in text
        assert "tiangong:quest" in text
        assert "tiangong:growth" in text
        assert "tiangong:season" in text
        assert "tiangong:tournament" in text
        assert "tiangong:mentor" in text
        assert "tiangong:sect" in text
        assert "tiangong:share" in text
        assert "share_attribution_report" in text
        assert "growth_campaign" in text
        assert "public_growth_report" in text
        assert "public_launch_preflight" in text
        assert "public_proof_pack" in text
        assert "Growth/Share Proof" in text
        assert "onboarding" in text.lower()
        assert "activation" in text.lower() or "激活" in text
        assert "record_snapshot=True" in text
        assert "target_contributors" in text
        assert "First Public Proof Action" in text
        assert "copy-ready" in text or "可直接复制传播" in text
        assert "Contents API" in text
        assert "launch blocker" in text or "公开 launch blocker" in text
        assert "GitHub Releases API" in text
        assert "v0.1.13" in text
        assert "PyPI JSON API" in text
        assert "Public Launch Closure Checklist" in text
        assert "stale" in text or "旧版本" in text
        assert "recap" in text.lower() or "复盘" in text
        assert "Pull Request" in text or "PR" in text
        assert "issues/new" in text
        assert "created public Issue/PR/Discussion URL" in text or "创建后的公开 Issue/PR/Discussion URL" in text


def test_growth_issue_form_collects_launch_campaign_target():
    """The growth form should let public visitors request a concrete 72h campaign target."""
    form = _read_form("tiangong-growth-flywheel.yml")

    assert "id: target_contributors" in form
    assert "label: Target contributors" in form
    assert "72-hour target number of real contributors" in form
    assert "placeholder: \"10\"" in form
