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
    "tiangong/candidate_smoke.py",
    "tiangong/install_bridge.py",
    "tiangong/launch_assets.py",
    "tiangong/onboarding.py",
    "tiangong/proof_pack.py",
    "tiangong/public_growth.py",
    "tiangong/release_boundary.py",
    "tiangong/season.py",
    "tiangong/mcp_server.py",
)

REQUIRED_DOC_COMMANDS = (
    "tiangong-mcp public-launch-assets",
    "tiangong-mcp public-install-command",
    "tiangong-mcp public-candidate-smoke --target-contributors 10",
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

REQUIRED_PUBLISH_WORKFLOW_FEATURES = (
    "release:",
    "types: [published]",
    "push:",
    "tags:",
    '"v*"',
    "workflow_dispatch:",
    "github.event.release.tag_name || github.ref_name || inputs.tag",
    "Resolve release tag",
    'github.event_name }}" == "push"',
    'tag="${GITHUB_REF_NAME}"',
    "Release tag must look like v0.1.0",
    "ref: ${{ steps.release.outputs.tag }}",
    "fetch-depth: 0",
    "Verify release tag and package version",
    "git fetch --force origin main:refs/remotes/origin/main --tags",
    "git merge-base --is-ancestor",
    "pyproject.toml version",
    "id-token: write",
    "pypa/gh-action-pypi-publish@release/v1",
)

REQUIRED_PROOF_LEDGER_ROUTES = (
    ("record-growth-referral", "tiangong-mcp record-growth-referral"),
    ("record-share-attribution", "tiangong-mcp record-share-attribution"),
)

REQUIRED_MCP_PUBLIC_ROUTES = (
    "public_proof_pack",
    "format_public_proof_pack",
    "public_install_command",
    "format_public_install_command",
)

REQUIRED_CANDIDATE_SMOKE_MARKERS = (
    "public-candidate-smoke",
    "run_public_candidate_install_smoke",
    "format_public_candidate_smoke",
)

STALE_PUBLIC_INSTALL_MARKER = "pip install " "tiangong-mcp"


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


def _find_one(path: Path, pattern: str, expected_version: str = "") -> Path | None:
    matches = sorted(path.glob(pattern))
    if expected_version:
        matching_version = [candidate for candidate in matches if f"-{expected_version}" in candidate.name]
        if matching_version:
            return matching_version[0]
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


def _public_copy_member_name(name: str) -> str:
    normalized = name.replace("\\", "/")
    marker = "/tiangong/"
    if marker in f"/{normalized}":
        return normalized[normalized.index("tiangong/"):]
    return normalized.rsplit("/", 1)[-1]


def _should_scan_public_copy_member(name: str) -> bool:
    normalized = name.replace("\\", "/")
    if not normalized.endswith((".py", ".md", ".yml", ".yaml", ".txt")):
        return False
    public_name = _public_copy_member_name(normalized)
    return (
        public_name.startswith("tiangong/")
        or public_name in {"README.md", "README.zh-CN.md"}
        or "/.github/workflows/" in f"/{normalized}"
    )


def _stale_public_install_copy_checks(dist: Path, expected_version: str) -> list[ReleaseBoundaryCheck]:
    """Verify built public copy does not route cold users to the stale PyPI command."""
    offenders: list[str] = []
    wheel = _find_one(dist, "tiangong_mcp-*.whl", expected_version)
    if wheel is None:
        offenders.append("wheel distribution")
    else:
        with zipfile.ZipFile(wheel) as archive:
            for name in archive.namelist():
                if not _should_scan_public_copy_member(name):
                    continue
                text = archive.read(name).decode("utf-8", errors="replace")
                if STALE_PUBLIC_INSTALL_MARKER in text:
                    offenders.append(f"wheel {_public_copy_member_name(name)} contains `{STALE_PUBLIC_INSTALL_MARKER}`")

    sdist = _find_one(dist, "tiangong_mcp-*.tar.gz", expected_version)
    if sdist is None:
        offenders.append("source distribution")
    else:
        with tarfile.open(sdist, "r:gz") as archive:
            for member in archive.getmembers():
                if not member.isfile() or not _should_scan_public_copy_member(member.name):
                    continue
                handle = archive.extractfile(member)
                if handle is None:
                    continue
                with handle:
                    text = handle.read().decode("utf-8", errors="replace")
                if STALE_PUBLIC_INSTALL_MARKER in text:
                    offenders.append(f"sdist {_public_copy_member_name(member.name)} contains `{STALE_PUBLIC_INSTALL_MARKER}`")

    return [
        ReleaseBoundaryCheck(
            "Public install copy in package",
            "ready" if not offenders else "blocked",
            (
                "wheel and sdist route public install copy through the candidate bridge or PyPI-current command"
                if not offenders
                else f"stale public install copy: {', '.join(offenders)}"
            ),
        )
    ]


def _proof_ledger_missing(*, cli_text: str, proof_pack_text: str, archive_label: str) -> list[str]:
    missing: list[str] = []
    for parser_route, proof_command in REQUIRED_PROOF_LEDGER_ROUTES:
        if parser_route not in cli_text:
            missing.append(f"{archive_label} cli route `{parser_route}`")
        if proof_command not in proof_pack_text:
            missing.append(f"{archive_label} proof pack command `{proof_command}`")
    return missing


def _wheel_checks(dist: Path, expected_version: str) -> list[ReleaseBoundaryCheck]:
    wheel = _find_one(dist, "tiangong_mcp-*.whl", expected_version)
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


def _proof_ledger_cli_checks(dist: Path, expected_version: str) -> list[ReleaseBoundaryCheck]:
    """Verify built artifacts expose terminal commands for recording public proof URLs."""
    missing: list[str] = []
    wheel = _find_one(dist, "tiangong_mcp-*.whl", expected_version)
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

    sdist = _find_one(dist, "tiangong_mcp-*.tar.gz", expected_version)
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


def _candidate_smoke_checks(dist: Path, expected_version: str) -> list[ReleaseBoundaryCheck]:
    """Verify built artifacts expose the candidate Git tag install smoke gate."""
    missing: list[str] = []
    wheel = _find_one(dist, "tiangong_mcp-*.whl", expected_version)
    if wheel is None:
        missing.append("wheel distribution")
    else:
        with zipfile.ZipFile(wheel) as archive:
            cli_text = _zip_member_text(archive, "tiangong/cli.py")
            smoke_text = _zip_member_text(archive, "tiangong/candidate_smoke.py")
        for marker in REQUIRED_CANDIDATE_SMOKE_MARKERS:
            source = cli_text if marker == "public-candidate-smoke" else smoke_text
            if marker not in source:
                missing.append(f"wheel candidate_smoke.py marker `{marker}`")

    sdist = _find_one(dist, "tiangong_mcp-*.tar.gz", expected_version)
    if sdist is None:
        missing.append("source distribution")
    else:
        with tarfile.open(sdist, "r:gz") as archive:
            cli_text = _tar_member_text(archive, "tiangong/cli.py")
            smoke_text = _tar_member_text(archive, "tiangong/candidate_smoke.py")
        for marker in REQUIRED_CANDIDATE_SMOKE_MARKERS:
            source = cli_text if marker == "public-candidate-smoke" else smoke_text
            if marker not in source:
                missing.append(f"sdist candidate_smoke.py marker `{marker}`")

    return [
        ReleaseBoundaryCheck(
            "Candidate install smoke route",
            "ready" if not missing else "blocked",
            (
                "wheel and sdist expose `public-candidate-smoke` for the Git tag install bridge"
                if not missing
                else f"missing {', '.join(missing)}"
            ),
        )
    ]


def _mcp_public_route_checks(dist: Path, expected_version: str) -> list[ReleaseBoundaryCheck]:
    """Verify built artifacts expose MCP launch recovery routes for client-side users."""
    missing: list[str] = []
    wheel = _find_one(dist, "tiangong_mcp-*.whl", expected_version)
    if wheel is None:
        missing.append("wheel distribution")
    else:
        with zipfile.ZipFile(wheel) as archive:
            mcp_text = _zip_member_text(archive, "tiangong/mcp_server.py")
        for marker in REQUIRED_MCP_PUBLIC_ROUTES:
            if marker not in mcp_text:
                missing.append(f"wheel mcp route marker `{marker}`")

    sdist = _find_one(dist, "tiangong_mcp-*.tar.gz", expected_version)
    if sdist is None:
        missing.append("source distribution")
    else:
        with tarfile.open(sdist, "r:gz") as archive:
            mcp_text = _tar_member_text(archive, "tiangong/mcp_server.py")
        for marker in REQUIRED_MCP_PUBLIC_ROUTES:
            if marker not in mcp_text:
                missing.append(f"sdist mcp route marker `{marker}`")

    return [
        ReleaseBoundaryCheck(
            "Public recovery MCP routes",
            "ready" if not missing else "blocked",
            (
                "wheel and sdist expose `public_proof_pack` and `public_install_command` for MCP clients"
                if not missing
                else f"missing {', '.join(missing)}"
            ),
        )
    ]


def _sdist_checks(dist: Path, expected_version: str) -> list[ReleaseBoundaryCheck]:
    sdist = _find_one(dist, "tiangong_mcp-*.tar.gz", expected_version)
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
    publish_workflow = _read_text(root / ".github" / "workflows" / "publish-pypi.yml")
    missing_publish_features = [
        feature for feature in REQUIRED_PUBLISH_WORKFLOW_FEATURES if feature not in publish_workflow
    ]
    missing = [*missing_commands, *missing_publish_features]
    return [
        ReleaseBoundaryCheck(
            "Workflow release-boundary steps",
            "ready" if not missing else "blocked",
            (
                "quality and publish workflows run launch assets plus release boundary; "
                "publish workflow verifies release tags and supports protected tag push plus manual tag dispatch"
            )
            if not missing
            else f"missing {', '.join(missing)}",
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
        *_sdist_checks(dist_dir, version),
        *_proof_ledger_cli_checks(dist_dir, version),
        *_candidate_smoke_checks(dist_dir, version),
        *_mcp_public_route_checks(dist_dir, version),
        *_stale_public_install_copy_checks(dist_dir, version),
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
        "tiangong-mcp public-install-command",
        "tiangong-mcp public-candidate-smoke --target-contributors 10",
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
