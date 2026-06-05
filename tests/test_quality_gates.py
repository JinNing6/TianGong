"""Quality-gate contracts for making the TianGong growth loop publishable."""

from __future__ import annotations

from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10 compatibility
    import tomli as tomllib


ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = ROOT / "pyproject.toml"
QUALITY_WORKFLOW = ROOT / ".github" / "workflows" / "quality-gates.yml"
PUBLISH_WORKFLOW = ROOT / ".github" / "workflows" / "publish-pypi.yml"


def _pyproject() -> dict:
    return tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))


def test_pyproject_declares_dev_quality_gate_extra():
    """Contributors should have one documented extra that installs every local gate."""
    optional = _pyproject()["project"]["optional-dependencies"]
    dev_deps = optional["dev"]

    required_prefixes = [
        "pytest",
        "pytest-asyncio",
        "ruff",
        "build",
        "twine",
    ]
    for prefix in required_prefixes:
        assert any(dep == prefix or dep.startswith(f"{prefix}>=") for dep in dev_deps), prefix


def test_runtime_version_matches_project_metadata():
    """The package should not publish contradictory runtime and build metadata versions."""
    import importlib.metadata as metadata

    import tiangong

    project_version = _pyproject()["project"]["version"]

    assert project_version == "0.1.3"
    assert tiangong.__version__ == project_version
    assert metadata.version("tiangong-mcp") == project_version


def test_quality_workflow_installs_dev_extra_and_runs_release_gates():
    """CI should prove lint, tests, build, and package metadata before public scaling."""
    workflow = QUALITY_WORKFLOW.read_text(encoding="utf-8")

    assert "pull_request_target" not in workflow
    assert "permissions:" in workflow
    assert "contents: read" in workflow
    assert "actions/checkout@" in workflow
    assert "actions/setup-python@" in workflow
    assert "cache: pip" in workflow
    assert "python -m pip install -e \".[dev]\"" in workflow
    assert "python -m ruff check ." in workflow
    assert "python -m pytest -q" in workflow
    assert "tiangong-mcp public-launch-assets" in workflow
    assert "python -m build" in workflow
    assert "python -m twine check dist/*" in workflow
    assert "tiangong-mcp public-release-boundary" in workflow


def test_pypi_publish_workflow_uses_trusted_publishing_after_release_gates():
    """PyPI publishing should be automated through OIDC after the same quality gates pass."""
    workflow = PUBLISH_WORKFLOW.read_text(encoding="utf-8")

    assert "pull_request_target" not in workflow
    assert "release:" in workflow
    assert "types: [published]" in workflow
    assert "push:" in workflow
    assert "tags:" in workflow
    assert '"v*"' in workflow or "'v*'" in workflow
    assert "workflow_dispatch:" in workflow
    assert "inputs:" in workflow
    assert "tag:" in workflow
    assert "Existing v* tag" in workflow
    assert "github.event.release.tag_name || github.ref_name || inputs.tag" in workflow
    assert 'github.event_name }}" == "push"' in workflow
    assert 'tag="${GITHUB_REF_NAME}"' in workflow
    assert "contents: read" in workflow
    assert "id-token: write" in workflow
    assert "environment: pypi" in workflow
    assert "Resolve release tag" in workflow
    assert "Release tag must look like v0.1.0" in workflow
    assert "actions/checkout@" in workflow
    assert "ref: ${{ steps.release.outputs.tag }}" in workflow
    assert "fetch-depth: 0" in workflow
    assert "actions/setup-python@" in workflow
    assert "python -m pip install -e \".[dev]\"" in workflow
    assert "Verify release tag and package version" in workflow
    assert "git fetch --force origin main:refs/remotes/origin/main --tags" in workflow
    assert "git merge-base --is-ancestor" in workflow
    assert "pyproject.toml version" in workflow
    assert "python -m ruff check ." in workflow
    assert "python -m pytest -q" in workflow
    assert "tiangong-mcp public-launch-assets" in workflow
    assert "python -m build" in workflow
    assert "python -m twine check dist/*" in workflow
    assert "tiangong-mcp public-release-boundary" in workflow
    assert "pypa/gh-action-pypi-publish@release/v1" in workflow
    assert "PYPI_TOKEN" not in workflow
    assert "password:" not in workflow
    assert "username:" not in workflow


def test_readmes_document_one_command_dev_install_and_quality_gate():
    """The public docs should make the contribution quality loop executable."""
    for filename in ["README.md", "README.zh-CN.md"]:
        text = (ROOT / filename).read_text(encoding="utf-8")

        assert "python -m pip install -e \".[dev]\"" in text
        assert "python -m ruff check ." in text
        assert "python -m pytest -q" in text
        assert "tiangong-mcp public-launch-assets" in text
        assert "tiangong-mcp public-install-command" in text
        assert "python -m build" in text
        assert "python -m twine check dist/*" in text
        assert "tiangong-mcp public-release-boundary" in text
        assert ".github/workflows/quality-gates.yml" in text
        assert ".github/workflows/publish-pypi.yml" in text
        assert "Trusted Publishing" in text
        assert "tag push" in text or "tag 推送" in text
        assert "workflow_dispatch" in text
        assert "origin/main" in text
        assert "pyproject.toml" in text
        assert "publish-pypi.yml" in text
        assert "environment `pypi`" in text
        assert "invalid-publisher" in text
        assert "Current Candidate Git Tag Install Bridge" in text
        assert 'python -m pip install --upgrade "tiangong-mcp @ git+https://github.com/JinNing6/TianGong.git@v0.1.3"' in text
        assert "PYPI_TOKEN" in text


def test_readmes_document_mcp_public_proof_pack_tool():
    """The no-network proof pack should be visible from the MCP tool table, not only the CLI runbook."""
    for filename in ["README.md", "README.zh-CN.md"]:
        text = (ROOT / filename).read_text(encoding="utf-8")

        assert "`public_proof_pack`" in text
        assert "`public_install_command`" in text
        assert "public-proof-pack" in text
        assert "public-install-command" in text
        assert "External Contributor" in text or "外部贡献者" in text
        assert "does not invent" in text or "不伪造" in text
