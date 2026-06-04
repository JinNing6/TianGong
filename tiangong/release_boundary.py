"""Release-boundary audit for TianGong public growth packages."""

from __future__ import annotations

import re
import tarfile
import zipfile
from dataclasses import dataclass
from pathlib import Path

REQUIRED_WHEEL_MODULES = (
    "tiangong/activation.py",
    "tiangong/cli.py",
    "tiangong/growth.py",
    "tiangong/launch_assets.py",
    "tiangong/onboarding.py",
    "tiangong/proof_pack.py",
    "tiangong/public_growth.py",
    "tiangong/release_boundary.py",
    "tiangong/season.py",
)

REQUIRED_DOC_COMMANDS = (
    "tiangong-mcp public-launch-assets",
    "tiangong-mcp public-launch-preflight --target-contributors 10",
    "tiangong-mcp public-growth-report --record-snapshot --target-contributors 10",
    "tiangong-mcp public-proof-pack --target-contributors 10",
    "tiangong-mcp public-release-boundary",
    "tiangong-mcp record-growth-referral",
    "tiangong-mcp record-share-attribution",
)

REQUIRED_WORKFLOW_COMMANDS = (
    "tiangong-mcp public-launch-assets",
    "tiangong-mcp public-release-boundary",
)

REQUIRED_PROOF_LEDGER_ROUTES = (
    ("record-growth-referral", "tiangong-mcp record-growth-referral"),
    ("record-share-attribution", "tiangong-mcp record-share-attribution"),
)


@dataclass(frozen=True)
class ReleaseBoundaryCheck:
    gate: str
    status: str
    evidence: str


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _project_version(root: Path) -> str:
    pyproject = root / "pyproject.toml"
    if not pyproject.exists():
        return ""
    match = re.search(r'(?m)^version\s*=\s*"([^"]+)"', _read_text(pyproject))
    return match.group(1) if match else ""


def _find_one(path: Path, pattern: str) -> Path | None:
    matches = sorted(path.glob(pattern))
    return matches[0] if matches else None


def _zip_member_text(archive: zipfile.ZipFile, suffix: str) -> str:
    member = next((name for name in archive.namelist() if name.endswith(suffix)), "")
    return archive.read(member).decode("utf-8", errors="replace") if member else ""


def _tar_member_text(archive: tarfile.TarFile, suffix: str) -> str:
    member = next((item for item in archive.getmembers() if item.name.endswith(suffix)), None)
    if member is None:
        return ""
    handle = archive.extractfile(member)
    if handle is None:
        return ""
    with handle:
        return handle.read().decode("utf-8", errors="replace")


def _proof_ledger_missing(*, cli_text: str, proof_pack_text: str, archive_label: str) -> list[str]:
    missing: list[str] = []
    for parser_route, proof_command in REQUIRED_PROOF_LEDGER_ROUTES:
        if parser_route not in cli_text:
            missing.append(f"{archive_label} cli route `{parser_route}`")
        if proof_command not in proof_pack_text:
            missing.append(f"{archive_label} proof pack command `{proof_command}`")
    return missing


def _wheel_checks(dist: Path, expected_version: str) -> list[ReleaseBoundaryCheck]:
    wheel = _find_one(dist, "tiangong_mcp-*.whl")
    if wheel is None:
        return [
            ReleaseBoundaryCheck("Wheel distribution", "missing", f"no `tiangong_mcp-*.whl` found in `{dist}`"),
            ReleaseBoundaryCheck("Wheel entry point", "missing", "wheel is missing"),
            ReleaseBoundaryCheck("Growth modules in wheel", "missing", "wheel is missing"),
        ]

    with zipfile.ZipFile(wheel) as archive:
        names = set(archive.namelist())
        entrypoint_name = next((name for name in names if name.endswith(".dist-info/entry_points.txt")), "")
        metadata_name = next((name for name in names if name.endswith(".dist-info/METADATA")), "")
        entrypoints = archive.read(entrypoint_name).decode("utf-8") if entrypoint_name else ""
        metadata = archive.read(metadata_name).decode("utf-8") if metadata_name else ""

    missing_modules = [module for module in REQUIRED_WHEEL_MODULES if module not in names]
    version_match = re.search(r"(?m)^Version:\s*(.+)$", metadata)
    package_version = version_match.group(1).strip() if version_match else ""
    version_ready = not expected_version or package_version == expected_version
    entry_ready = "tiangong-mcp = tiangong.cli:main" in entrypoints

    return [
        ReleaseBoundaryCheck(
            "Wheel distribution",
            "ready" if version_ready else "blocked",
            f"`{wheel.name}` version `{package_version or 'unknown'}` vs local `{expected_version or 'unknown'}`",
        ),
        ReleaseBoundaryCheck(
            "Wheel entry point",
            "ready" if entry_ready else "blocked",
            "`tiangong-mcp = tiangong.cli:main`" if entry_ready else "console script does not point to CLI dispatcher",
        ),
        ReleaseBoundaryCheck(
            "Growth modules in wheel",
            "ready" if not missing_modules else "blocked",
            "all public growth modules packaged" if not missing_modules else f"missing {', '.join(missing_modules)}",
        ),
    ]


def _proof_ledger_cli_checks(dist: Path) -> list[ReleaseBoundaryCheck]:
    """Verify built artifacts expose terminal commands for recording public proof URLs."""
    missing: list[str] = []
    wheel = _find_one(dist, "tiangong_mcp-*.whl")
    if wheel is None:
        missing.append("wheel distribution")
    else:
        with zipfile.ZipFile(wheel) as archive:
            missing.extend(
                _proof_ledger_missing(
                    cli_text=_zip_member_text(archive, "tiangong/cli.py"),
                    proof_pack_text=_zip_member_text(archive, "tiangong/proof_pack.py"),
                    archive_label="wheel",
                )
            )

    sdist = _find_one(dist, "tiangong_mcp-*.tar.gz")
    if sdist is None:
        missing.append("source distribution")
    else:
        with tarfile.open(sdist, "r:gz") as archive:
            missing.extend(
                _proof_ledger_missing(
                    cli_text=_tar_member_text(archive, "tiangong/cli.py"),
                    proof_pack_text=_tar_member_text(archive, "tiangong/proof_pack.py"),
                    archive_label="sdist",
                )
            )

    return [
        ReleaseBoundaryCheck(
            "Proof ledger CLI routes",
            "ready" if not missing else "blocked",
            (
                "wheel and sdist expose terminal proof-ledger recording commands"
                if not missing
                else f"missing {', '.join(missing)}"
            ),
        )
    ]


def _sdist_checks(dist: Path) -> list[ReleaseBoundaryCheck]:
    sdist = _find_one(dist, "tiangong_mcp-*.tar.gz")
    if sdist is None:
        return [ReleaseBoundaryCheck("Source distribution", "missing", f"no `tiangong_mcp-*.tar.gz` found in `{dist}`")]

    with tarfile.open(sdist, "r:gz") as archive:
        names = set(archive.getnames())
    required_suffixes = ("pyproject.toml", "README.md", *REQUIRED_WHEEL_MODULES)
    missing = [suffix for suffix in required_suffixes if not any(name.endswith(suffix) for name in names)]
    return [
        ReleaseBoundaryCheck(
            "Source distribution",
            "ready" if not missing else "blocked",
            f"`{sdist.name}` includes source launch surface" if not missing else f"missing {', '.join(missing)}",
        )
    ]


def _documentation_checks(root: Path) -> list[ReleaseBoundaryCheck]:
    files = [root / "README.md", root / "README.zh-CN.md"]
    missing_files = [path.name for path in files if not path.exists()]
    if missing_files:
        return [ReleaseBoundaryCheck("Documentation commands", "missing", f"missing {', '.join(missing_files)}")]
    missing_commands = [
        command
        for command in REQUIRED_DOC_COMMANDS
        if not all(command in _read_text(path) for path in files)
    ]
    return [
        ReleaseBoundaryCheck(
            "Documentation commands",
            "ready" if not missing_commands else "blocked",
            "README launch commands are synchronized" if not missing_commands else f"missing {', '.join(missing_commands)}",
        )
    ]


def _workflow_checks(root: Path) -> list[ReleaseBoundaryCheck]:
    workflows = [
        root / ".github" / "workflows" / "quality-gates.yml",
        root / ".github" / "workflows" / "publish-pypi.yml",
    ]
    missing_files = [path.as_posix() for path in workflows if not path.exists()]
    if missing_files:
        return [ReleaseBoundaryCheck("Workflow release-boundary steps", "missing", f"missing {', '.join(missing_files)}")]
    missing_commands = [
        command
        for command in REQUIRED_WORKFLOW_COMMANDS
        if not all(command in _read_text(path) for path in workflows)
    ]
    return [
        ReleaseBoundaryCheck(
            "Workflow release-boundary steps",
            "ready" if not missing_commands else "blocked",
            "quality and publish workflows run launch assets plus release boundary"
            if not missing_commands
            else f"missing {', '.join(missing_commands)}",
        )
    ]


def _format_table(checks: list[ReleaseBoundaryCheck]) -> list[str]:
    lines = [
        "| Gate | Status | Evidence |",
        "|---|---|---|",
    ]
    for check in checks:
        lines.append(f"| {check.gate} | {check.status} | {check.evidence} |")
    return lines


def format_public_release_boundary(root: str | Path | None = None, dist: str | Path | None = None) -> str:
    """Format a local release-boundary report for the built TianGong package."""
    project_root = Path(root or Path.cwd()).resolve()
    dist_dir = Path(dist).resolve() if dist is not None else project_root / "dist"
    version = _project_version(project_root)
    checks = [
        *_wheel_checks(dist_dir, version),
        *_sdist_checks(dist_dir),
        *_proof_ledger_cli_checks(dist_dir),
        *_documentation_checks(project_root),
        *_workflow_checks(project_root),
    ]
    failing = [check for check in checks if check.status != "ready"]

    lines = [
        "# TianGong Public Release Boundary",
        "",
        f"> Project root: `{project_root}`.",
        f"> Distribution directory: `{dist_dir}`.",
        "> This command does not upload distributions, create releases, or claim public traction.",
        "> It proves the local build artifact still contains the public growth loop before release.",
        "",
        "## Release Boundary Gates",
        "",
        *_format_table(checks),
        "",
        "## Required Local Gate Commands",
        "",
        "```bash",
        "tiangong-mcp public-launch-assets",
        "python -m build",
        "python -m twine check dist/*",
        "tiangong-mcp public-release-boundary",
        "tiangong-mcp public-launch-preflight --target-contributors 10",
        "```",
        "",
    ]
    if failing:
        lines.extend(
            [
                "## Local Release Boundary Blockers",
                "",
                *[f"- {check.gate}: {check.evidence}" for check in failing],
                "",
            ]
        )
    else:
        lines.extend(
            [
                "## Local Release Boundary Status",
                "",
                "- Built package, documentation, and workflows preserve the public growth loop.",
                "- This does not prove GitHub Release, PyPI latest version, or first public proof; run public preflight next.",
                "",
            ]
        )
    return "\n".join(lines)
