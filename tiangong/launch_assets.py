"""Local public-launch asset audit for TianGong maintainers."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

import yaml

GROWTH_FORM = ".github/ISSUE_TEMPLATE/tiangong-growth-flywheel.yml"
SHARE_FORM = ".github/ISSUE_TEMPLATE/tiangong-share-proof.yml"
ISSUE_TEMPLATE_CONFIG = ".github/ISSUE_TEMPLATE/config.yml"
ISSUEOPS_WORKFLOW = ".github/workflows/issueops-onboarding.yml"
QUALITY_WORKFLOW = ".github/workflows/quality-gates.yml"
PUBLISH_WORKFLOW = ".github/workflows/publish-pypi.yml"

REMOTE_ACQUISITION_ASSETS = (
    GROWTH_FORM,
    SHARE_FORM,
    ISSUEOPS_WORKFLOW,
)

ISSUE_FORM_ASSETS = (
    ISSUE_TEMPLATE_CONFIG,
    ".github/ISSUE_TEMPLATE/tiangong-refinement-quest.yml",
    GROWTH_FORM,
    ".github/ISSUE_TEMPLATE/tiangong-season-board.yml",
    ".github/ISSUE_TEMPLATE/tiangong-tournament.yml",
    ".github/ISSUE_TEMPLATE/tiangong-mentor-pact.yml",
    ".github/ISSUE_TEMPLATE/tiangong-sect-recruitment.yml",
    SHARE_FORM,
)

RELEASE_AUTOMATION_ASSETS = (
    QUALITY_WORKFLOW,
    PUBLISH_WORKFLOW,
    "pyproject.toml",
)

PUBLIC_GROWTH_CODE_ASSETS = (
    "tiangong/activation.py",
    "tiangong/artifact_system.py",
    "tiangong/cli.py",
    "tiangong/growth.py",
    "tiangong/launch_assets.py",
    "tiangong/onboarding.py",
    "tiangong/proof_pack.py",
    "tiangong/public_growth.py",
    "tiangong/release_boundary.py",
    "tiangong/season.py",
    "tiangong/mcp_server.py",
    "tiangong/__init__.py",
    "tiangong/__main__.py",
)

PUBLIC_GROWTH_SURFACE_ASSETS = (
    "tiangong/animations.py",
    "tiangong/banner.py",
    "tiangong/ceremony.py",
    "tiangong/cultivator.py",
    "tiangong/ecosystem.py",
    "tiangong/forge.py",
    "tiangong/lineage.py",
    "tiangong/marketplace.py",
    "tiangong/realm.py",
    "tiangong/registry.py",
    "tiangong/review.py",
    "tiangong/search.py",
    "tiangong/sect.py",
    "tiangong/vault.py",
)

PUBLIC_GROWTH_TEST_ASSETS = (
    "tests/test_cli.py",
    "tests/test_activation_funnel.py",
    "tests/test_growth_experience.py",
    "tests/test_growth_flywheel.py",
    "tests/test_issueops_surfaces.py",
    "tests/test_marketplace.py",
    "tests/test_public_growth_report.py",
    "tests/test_quality_gates.py",
    "tests/test_realm.py",
    "tests/test_season.py",
    "tests/test_sect.py",
    "tests/test_start_cultivation.py",
    "tests/verify_mcp.py",
    "test_cinema_anims.py",
)

PUBLIC_GROWTH_RELEASE_DOCS = (
    ".gitignore",
    "README.md",
    "README.zh-CN.md",
    "pyproject.toml",
)

FULL_PUBLIC_GROWTH_RELEASE_ASSETS = (
    *PUBLIC_GROWTH_RELEASE_DOCS,
    *ISSUE_FORM_ASSETS,
    ISSUEOPS_WORKFLOW,
    QUALITY_WORKFLOW,
    PUBLISH_WORKFLOW,
    *PUBLIC_GROWTH_CODE_ASSETS,
    *PUBLIC_GROWTH_SURFACE_ASSETS,
    *PUBLIC_GROWTH_TEST_ASSETS,
)


@dataclass(frozen=True)
class LaunchAssetAudit:
    path: str
    status: str
    validation: str


def _read_text(root: Path, path: str) -> str:
    return (root / path).read_text(encoding="utf-8")


def _yaml_status(root: Path, path: str) -> tuple[str, object | None]:
    full_path = root / path
    if not full_path.exists():
        return "missing", None
    try:
        return "yaml: valid", yaml.safe_load(full_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        return f"yaml: invalid ({exc.__class__.__name__})", None


def _issue_form_audit(root: Path, path: str) -> LaunchAssetAudit:
    yaml_status, parsed = _yaml_status(root, path)
    if yaml_status == "missing":
        return LaunchAssetAudit(path, "missing", "file is absent")
    if parsed is None or not isinstance(parsed, dict):
        return LaunchAssetAudit(path, "blocked", yaml_status)

    required = ("name", "description", "body")
    missing = [key for key in required if key not in parsed]
    body_ready = isinstance(parsed.get("body"), list) and bool(parsed.get("body"))
    label_ready = "labels" in parsed
    if missing or not body_ready or not label_ready:
        problems = []
        if missing:
            problems.append(f"missing {', '.join(missing)}")
        if not body_ready:
            problems.append("body is not a non-empty list")
        if not label_ready:
            problems.append("labels missing")
        return LaunchAssetAudit(path, "blocked", f"{yaml_status}; form schema: blocked ({'; '.join(problems)})")
    return LaunchAssetAudit(path, "ready", f"{yaml_status}; form schema: ready")


def _issue_template_config_audit(root: Path) -> LaunchAssetAudit:
    path = ISSUE_TEMPLATE_CONFIG
    yaml_status, parsed = _yaml_status(root, path)
    if yaml_status == "missing":
        return LaunchAssetAudit(path, "missing", "file is absent")
    if parsed is None or not isinstance(parsed, dict):
        return LaunchAssetAudit(path, "blocked", yaml_status)

    contact_links = parsed.get("contact_links")
    blank_issues_ready = isinstance(parsed.get("blank_issues_enabled"), bool)
    contact_ready = isinstance(contact_links, list)
    blocked = []
    if not blank_issues_ready:
        blocked.append("blank_issues_enabled is not a boolean")
    if not contact_ready:
        blocked.append("contact_links is not a list")
    if blocked:
        return LaunchAssetAudit(path, "blocked", f"{yaml_status}; template config: blocked ({', '.join(blocked)})")
    return LaunchAssetAudit(path, "ready", f"{yaml_status}; template config: ready")


def _issueops_workflow_audit(root: Path) -> LaunchAssetAudit:
    path = ISSUEOPS_WORKFLOW
    yaml_status, parsed = _yaml_status(root, path)
    if yaml_status == "missing":
        return LaunchAssetAudit(path, "missing", "file is absent")
    if parsed is None:
        return LaunchAssetAudit(path, "blocked", yaml_status)

    text = _read_text(root, path)
    checks = {
        "issues: write": "issues: write" in text,
        "no pull_request_target": "pull_request_target" not in text,
        "no checkout": "actions/checkout" not in text,
        "no run steps": "\n        run:" not in text,
        "dedupe marker": "<!-- tiangong:issueops-onboarding:v1 -->" in text,
        "public preflight route": "public_launch_preflight" in text,
    }
    blocked = [name for name, ok in checks.items() if not ok]
    if blocked:
        return LaunchAssetAudit(path, "blocked", f"{yaml_status}; IssueOps workflow safety: blocked ({', '.join(blocked)})")
    return LaunchAssetAudit(path, "ready", f"{yaml_status}; IssueOps workflow safety: ready")


def _quality_workflow_audit(root: Path) -> LaunchAssetAudit:
    path = QUALITY_WORKFLOW
    yaml_status, parsed = _yaml_status(root, path)
    if yaml_status == "missing":
        return LaunchAssetAudit(path, "missing", "file is absent")
    if parsed is None:
        return LaunchAssetAudit(path, "blocked", yaml_status)

    text = _read_text(root, path)
    checks = {
        "read-only contents": "contents: read" in text,
        "no pull_request_target": "pull_request_target" not in text,
        "dev install": 'python -m pip install -e ".[dev]"' in text,
        "lint": "python -m ruff check ." in text,
        "tests": "python -m pytest -q" in text,
        "build": "python -m build" in text,
        "twine": "python -m twine check dist/*" in text,
    }
    blocked = [name for name, ok in checks.items() if not ok]
    if blocked:
        return LaunchAssetAudit(path, "blocked", f"{yaml_status}; Quality workflow: blocked ({', '.join(blocked)})")
    return LaunchAssetAudit(path, "ready", f"{yaml_status}; Quality workflow: ready")


def _publish_workflow_audit(root: Path) -> LaunchAssetAudit:
    path = PUBLISH_WORKFLOW
    yaml_status, parsed = _yaml_status(root, path)
    if yaml_status == "missing":
        return LaunchAssetAudit(path, "missing", "file is absent")
    if parsed is None:
        return LaunchAssetAudit(path, "blocked", yaml_status)

    text = _read_text(root, path)
    checks = {
        "release trigger": "release:" in text and "types: [published]" in text,
        "trusted publisher id-token": "id-token: write" in text,
        "pypi environment": "environment: pypi" in text,
        "publish action": "pypa/gh-action-pypi-publish@release/v1" in text,
        "no token": "PYPI_TOKEN" not in text,
        "no password": "password:" not in text,
        "no username": "username:" not in text,
    }
    blocked = [name for name, ok in checks.items() if not ok]
    if blocked:
        return LaunchAssetAudit(path, "blocked", f"{yaml_status}; Publish workflow: blocked ({', '.join(blocked)})")
    return LaunchAssetAudit(path, "ready", f"{yaml_status}; Publish workflow: ready")


def _pyproject_audit(root: Path) -> LaunchAssetAudit:
    path = "pyproject.toml"
    full_path = root / path
    if not full_path.exists():
        return LaunchAssetAudit(path, "missing", "file is absent")
    text = full_path.read_text(encoding="utf-8")
    checks = {
        "version 0.1.0": 'version = "0.1.0"' in text,
        "cli entrypoint": 'tiangong-mcp = "tiangong.cli:main"' in text,
        "dev extra": "[project.optional-dependencies]" in text and "dev =" in text,
    }
    blocked = [name for name, ok in checks.items() if not ok]
    if blocked:
        return LaunchAssetAudit(path, "blocked", f"package metadata: blocked ({', '.join(blocked)})")
    return LaunchAssetAudit(path, "ready", "package metadata: ready")


def _audit_by_path(root: Path, path: str) -> LaunchAssetAudit:
    if path == ISSUE_TEMPLATE_CONFIG:
        return _issue_template_config_audit(root)
    if path in ISSUE_FORM_ASSETS:
        return _issue_form_audit(root, path)
    if path == ISSUEOPS_WORKFLOW:
        return _issueops_workflow_audit(root)
    if path == QUALITY_WORKFLOW:
        return _quality_workflow_audit(root)
    if path == PUBLISH_WORKFLOW:
        return _publish_workflow_audit(root)
    if path == "pyproject.toml":
        return _pyproject_audit(root)
    return LaunchAssetAudit(path, "unverified", "no audit rule")


def _release_file_audit(root: Path, path: str) -> LaunchAssetAudit:
    full_path = root / path
    if not full_path.exists():
        return LaunchAssetAudit(path, "missing", "required public growth release file is absent")
    if full_path.is_dir():
        return LaunchAssetAudit(path, "blocked", "expected a file, found a directory")
    return LaunchAssetAudit(path, "ready", "release bundle file present")


def _git_add_command(paths: tuple[str, ...]) -> str:
    return "git add " + " ".join(paths)


def _decode_git_status_path(raw: str) -> str:
    if " -> " in raw:
        raw = raw.rsplit(" -> ", 1)[1]
    return raw.strip().strip('"')


def _git_status_paths(root: Path) -> tuple[list[str], str]:
    try:
        result = subprocess.run(
            ["git", "status", "--short", "--untracked-files=all"],
            cwd=root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return [], f"git status unavailable: {exc.__class__.__name__}"

    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip().splitlines()
        return [], f"git status unavailable: {detail[0] if detail else f'exit {result.returncode}'}"

    paths = []
    for line in result.stdout.splitlines():
        if len(line) < 4:
            continue
        paths.append(_decode_git_status_path(line[3:]))
    return paths, ""


def _format_working_tree_coverage(root: Path, release_assets: tuple[str, ...]) -> list[str]:
    changed_paths, error = _git_status_paths(root)
    covered = sorted({path for path in changed_paths if path in release_assets})
    outside = sorted({path for path in changed_paths if path and path not in release_assets})
    lines = [
        "## Working Tree Release Coverage",
        "",
    ]
    if error:
        lines.extend(
            [
                f"> {error}.",
                "> Review `git status --short` manually before running the full release handoff.",
                "",
            ]
        )
        return lines

    if not changed_paths:
        lines.extend(
            [
                "- Working tree is clean; the full release handoff is a static bundle checklist.",
                "",
            ]
        )
        return lines

    lines.extend(
        [
            f"- Changed or untracked files detected: {len(changed_paths)}",
            f"- Covered by full public growth release bundle: {len(covered)}",
            f"- Outside the release bundle and requiring separate review: {len(outside)}",
            "",
            "| Coverage | File |",
            "|---|---|",
        ]
    )
    for path in covered:
        lines.append(f"| included | `{path}` |")
    for path in outside:
        lines.append(f"| review separately | `{path}` |")
    lines.extend(
        [
            "",
            "> Do not assume the full release handoff stages files marked `review separately`.",
            "",
        ]
    )
    return lines


def _format_table(rows: list[LaunchAssetAudit]) -> list[str]:
    lines = [
        "| Asset | Local status | Validation |",
        "|---|---|---|",
    ]
    for row in rows:
        lines.append(f"| `{row.path}` | {row.status} | {row.validation} |")
    return lines


def format_full_public_growth_release_handoff_lines(
    *,
    release_tag: str = "v0.1.0",
    include_audit_instruction: bool = False,
) -> list[str]:
    """Return the complete release handoff commands without executing them."""
    lines = [
        "## Full Public Growth Release Handoff",
        "",
    ]
    if include_audit_instruction:
        lines.extend(
            [
                "Run `tiangong-mcp public-launch-assets` first to verify local asset readiness and working tree release coverage.",
                "",
            ]
        )
    lines.extend(
        [
            "Run this path when the local tests, build, and release boundary are green and you are ready to publish the current growth loop:",
            "",
            "```bash",
            _git_add_command((".gitignore",)),
            _git_add_command(tuple(path for path in PUBLIC_GROWTH_RELEASE_DOCS if path != ".gitignore")),
            _git_add_command((*ISSUE_FORM_ASSETS, ISSUEOPS_WORKFLOW, QUALITY_WORKFLOW, PUBLISH_WORKFLOW)),
            _git_add_command(PUBLIC_GROWTH_CODE_ASSETS),
            _git_add_command(PUBLIC_GROWTH_SURFACE_ASSETS),
            _git_add_command(PUBLIC_GROWTH_TEST_ASSETS),
            'git commit -m "Prepare TianGong public growth launch"',
            "git push origin main",
            f"gh release create {release_tag} --generate-notes",
            "```",
            "",
            "> The release command should trigger `.github/workflows/publish-pypi.yml` through PyPI Trusted Publishing/OIDC.",
            "> Do not use a stored `PYPI_TOKEN`; wait for PyPI to publish the same version, then rerun public preflight.",
            "",
        ]
    )
    return lines


def format_public_launch_assets(root: str | Path | None = None) -> str:
    """Format a local-only launch asset manifest for safe public release staging."""
    project_root = Path(root or Path.cwd()).resolve()
    remote_rows = [_audit_by_path(project_root, path) for path in REMOTE_ACQUISITION_ASSETS]
    form_rows = [_audit_by_path(project_root, path) for path in ISSUE_FORM_ASSETS]
    release_rows = [_audit_by_path(project_root, path) for path in RELEASE_AUTOMATION_ASSETS]
    full_release_rows = [_release_file_audit(project_root, path) for path in FULL_PUBLIC_GROWTH_RELEASE_ASSETS]
    all_rows = remote_rows + release_rows + full_release_rows
    blocked = [row for row in all_rows if row.status != "ready"]
    minimum_add = " ".join(REMOTE_ACQUISITION_ASSETS)
    release_tag = "v0.1.0"

    lines = [
        "# TianGong Public Launch Assets",
        "",
        f"> Project root: `{project_root}`.",
        "> This command does not execute git, publish releases, or claim public traction.",
        "> It only audits local files that must be pushed before the public flywheel can become reviewable.",
        "",
        "## Remote Acquisition Bundle",
        "",
        *_format_table(remote_rows),
        "",
        "## Release Automation Bundle",
        "",
        *_format_table(release_rows),
        "",
        "## Public Issue Form Coverage",
        "",
        *_format_table(form_rows),
        "",
        "## Full Public Growth Release Bundle",
        "",
        "> Use this bundle for the commit that should actually reach the default branch before creating a release.",
        "> The smaller remote-acquisition bundle is not enough for PyPI; it only makes GitHub IssueOps entrypoints visible.",
        "",
        *_format_table(full_release_rows),
        "",
        *_format_working_tree_coverage(project_root, FULL_PUBLIC_GROWTH_RELEASE_ASSETS),
        "## Exact Local Staging Commands",
        "",
        "Run these only after reviewing the files above:",
        "",
        "```bash",
        f"git add {minimum_add}",
        'git commit -m "Add TianGong public launch IssueOps routes"',
        "git push origin main",
        "```",
        "",
        *format_full_public_growth_release_handoff_lines(release_tag=release_tag),
        "## Recheck Commands",
        "",
        "- Local asset audit: `tiangong-mcp public-launch-assets`",
        "- Public preflight: `tiangong-mcp public-launch-preflight --target-contributors 10`",
        "- Public proof report: `tiangong-mcp public-growth-report --record-snapshot --target-contributors 10`",
        "",
    ]
    if blocked:
        lines.extend(
            [
                "## Local Launch Asset Blockers",
                "",
                *[f"- `{row.path}`: {row.validation}" for row in blocked],
                "",
            ]
        )
    else:
        lines.extend(
            [
                "## Local Launch Asset Status",
                "",
                "- Required local launch assets are ready for both the remote-acquisition bundle and the full public growth release handoff above.",
                "- This does not prove remote default-branch presence, GitHub Release creation, PyPI latest version, or first public proof; run public preflight after pushing.",
                "",
            ]
        )
    return "\n".join(lines)
