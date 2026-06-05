"""Candidate Git tag install smoke gate for stale-registry launch paths."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

from .install_bridge import (
    DEFAULT_PACKAGE_NAME,
    git_tag_install_command,
    git_tag_install_requirement,
    local_package_version,
    normalize_release_tag,
)

CommandRunner = Callable[..., subprocess.CompletedProcess[str]]


@dataclass(frozen=True)
class CandidateSmokeResult:
    """Result of installing the current candidate tag in a fresh virtual environment."""

    package_name: str
    repo_owner: str
    repo_name: str
    tag: str
    requirement: str
    install_command: str
    temp_root: Path
    installed_version: str = ""
    console_script_exists: bool = False
    install_surface_contains_tag: bool = False
    proof_pack_contains_tag: bool = False
    proof_pack_contains_external_invite: bool = False
    cleaned: bool = False
    error: str = ""

    @property
    def expected_version(self) -> str:
        return self.tag.removeprefix("v")

    @property
    def ready(self) -> bool:
        return (
            not self.error
            and self.installed_version == self.expected_version
            and self.console_script_exists
            and self.install_surface_contains_tag
            and self.proof_pack_contains_tag
            and self.proof_pack_contains_external_invite
            and self.cleaned
        )


def _safe_positive_int(value: int | str | None, fallback: int = 10) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return fallback
    return number if number > 0 else fallback


def _run_text(
    runner: CommandRunner,
    command: Sequence[str],
    *,
    cwd: Path | None = None,
    timeout_seconds: int = 300,
) -> str:
    completed = runner(
        list(command),
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        check=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout_seconds,
    )
    return "\n".join(part for part in [completed.stdout, completed.stderr] if part)


def _venv_python_path(venv: Path) -> Path:
    return venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def _console_script_path(venv: Path) -> Path:
    return venv / ("Scripts/tiangong-mcp.exe" if os.name == "nt" else "bin/tiangong-mcp")


def _cleanup_temp_root(temp_root: Path, temp_parent: Path) -> bool:
    resolved_root = temp_root.resolve()
    resolved_parent = temp_parent.resolve()
    if not str(resolved_root).lower().startswith(str(resolved_parent).lower()):
        return False
    shutil.rmtree(resolved_root, ignore_errors=False)
    return not resolved_root.exists()


def run_public_candidate_install_smoke(
    *,
    repo_owner: str = "",
    repo_name: str = "",
    version_or_tag: str = "",
    target_contributors: int = 10,
    package_name: str = DEFAULT_PACKAGE_NAME,
    python_executable: str | Path | None = None,
    temp_parent: str | Path | None = None,
    keep_temp: bool = False,
    runner: CommandRunner = subprocess.run,
) -> CandidateSmokeResult:
    """Install the candidate Git tag in a disposable venv and verify the public CLI path."""
    tag = normalize_release_tag(version_or_tag or local_package_version(package_name))
    requirement = git_tag_install_requirement(
        repo_owner=repo_owner,
        repo_name=repo_name,
        version_or_tag=tag,
        package_name=package_name,
    )
    install_command = git_tag_install_command(
        repo_owner=repo_owner,
        repo_name=repo_name,
        version_or_tag=tag,
        package_name=package_name,
    )
    owner = requirement.split("github.com/", 1)[1].split("/", 1)[0] if "github.com/" in requirement else repo_owner
    repo = requirement.split(f"{owner}/", 1)[1].split(".git@", 1)[0] if owner and f"{owner}/" in requirement else repo_name
    target = _safe_positive_int(target_contributors)
    parent = Path(temp_parent) if temp_parent else Path(tempfile.gettempdir()) / "tiangong-candidate-smoke"
    parent.mkdir(parents=True, exist_ok=True)
    temp_root = parent / f"{tag.removeprefix('v').replace('.', '-')}-{int(time.time() * 1000)}"
    venv = temp_root / ".venv"
    base_python = Path(python_executable or sys.executable)

    installed_version = ""
    console_exists = False
    install_surface_contains_tag = False
    proof_pack_contains_tag = False
    proof_pack_contains_external_invite = False
    cleaned = False
    error = ""

    try:
        temp_root.mkdir(parents=True, exist_ok=False)
        _run_text(runner, [str(base_python), "-m", "venv", str(venv)])
        venv_python = _venv_python_path(venv)
        _run_text(runner, [str(venv_python), "-m", "pip", "install", "--upgrade", requirement])
        installed_version = _run_text(
            runner,
            [
                str(venv_python),
                "-c",
                f"import importlib.metadata as m; print(m.version({package_name!r}))",
            ],
        ).strip().splitlines()[0]
        console = _console_script_path(venv)
        console_exists = console.exists()
        install_surface = _run_text(runner, [str(console), "public-install-command"])
        proof_pack = _run_text(runner, [str(console), "public-proof-pack", "--target-contributors", str(target)])
        install_surface_contains_tag = tag in install_surface
        proof_pack_contains_tag = tag in proof_pack
        proof_pack_contains_external_invite = "Copy External Contributor Invite" in proof_pack
        if not keep_temp:
            cleaned = _cleanup_temp_root(temp_root, parent)
    except Exception as exc:  # noqa: BLE001 - report recovery details instead of raising from CLI.
        error = str(exc)

    return CandidateSmokeResult(
        package_name=package_name,
        repo_owner=owner,
        repo_name=repo,
        tag=tag,
        requirement=requirement,
        install_command=install_command,
        temp_root=temp_root,
        installed_version=installed_version,
        console_script_exists=console_exists,
        install_surface_contains_tag=install_surface_contains_tag,
        proof_pack_contains_tag=proof_pack_contains_tag,
        proof_pack_contains_external_invite=proof_pack_contains_external_invite,
        cleaned=cleaned,
        error=error,
    )


def _status(value: bool) -> str:
    return "ready" if value else "blocked"


def _table(rows: list[tuple[str, str, str]]) -> list[str]:
    return [
        "| Gate | Status | Evidence |",
        "|---|---|---|",
        *(f"| {gate} | {status} | {evidence} |" for gate, status, evidence in rows),
    ]


def format_public_candidate_smoke(result: CandidateSmokeResult) -> str:
    """Format a candidate install smoke report for release operators."""
    version_ready = result.installed_version == result.expected_version
    invite_ready = result.proof_pack_contains_tag and result.proof_pack_contains_external_invite
    cleanup_evidence = (
        f"temporary environment cleaned: `{result.temp_root}`"
        if result.cleaned
        else f"temporary environment retained for inspection: `{result.temp_root}`"
    )
    rows = [
        ("Candidate requirement", "ready", f"`{result.requirement}`"),
        (
            "Installed package version",
            _status(version_ready),
            f"`{result.installed_version or '<missing>'}` matches `{result.tag}`" if version_ready else (
                f"`{result.installed_version or '<missing>'}` does not match `{result.tag}`"
            ),
        ),
        (
            "Console script",
            _status(result.console_script_exists),
            "`tiangong-mcp` command is installed"
            if result.console_script_exists
            else "`tiangong-mcp` command was not found in the smoke venv",
        ),
        (
            "Install command surface",
            _status(result.install_surface_contains_tag),
            f"`public-install-command` includes `{result.tag}`"
            if result.install_surface_contains_tag
            else f"`public-install-command` did not include `{result.tag}`",
        ),
        (
            "Proof pack invite",
            _status(invite_ready),
            "proof pack includes the current tag and External Contributor invite"
            if invite_ready
            else "proof pack is missing the current tag or External Contributor invite",
        ),
        ("Temporary environment cleanup", _status(result.cleaned), cleanup_evidence),
    ]
    lines = [
        "# TianGong Public Candidate Install Smoke",
        "",
        "> Purpose: prove the public Git tag candidate install works from a fresh virtual environment while PyPI is stale.",
        "> This command creates a temporary venv, installs from the public Git tag, runs public CLI surfaces, and cleans up on success.",
        "> It does not publish releases, upload distributions, record traction, or claim a closed install loop.",
        "",
        "## Smoke Status",
        "",
        f"- Status: {'ready' if result.ready else 'blocked'}",
        f"- Package: `{result.package_name}`",
        f"- Repository: `{result.repo_owner}/{result.repo_name}`",
        f"- Tag: `{result.tag}`",
        f"- Candidate install: `{result.install_command}`",
        "",
        "## Smoke Gates",
        "",
        *_table(rows),
        "",
    ]
    if result.error:
        lines.extend(
            [
                "## Smoke Error",
                "",
                f"- Error: {result.error}",
                f"- Temp root retained for inspection: `{result.temp_root}`",
                "",
            ]
        )
    lines.extend(
        [
            "## Recheck Commands",
            "",
            "- Candidate smoke: `tiangong-mcp public-candidate-smoke --target-contributors 10`",
            "- Install decision: `tiangong-mcp public-install-command`",
            "- Public proof pack: `tiangong-mcp public-proof-pack --target-contributors 10`",
            "- Public preflight: `tiangong-mcp public-launch-preflight --target-contributors 10`",
            "",
        ]
    )
    return "\n".join(lines)
