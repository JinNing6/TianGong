"""Command-line contracts for TianGong launch operations."""

from __future__ import annotations

import tarfile
import zipfile
from io import BytesIO, StringIO, TextIOWrapper
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10 compatibility
    import tomli as tomllib


ROOT = Path(__file__).resolve().parents[1]


def _cold_launch_snapshot():
    from tiangong.public_growth import (
        PublicDistributionReadiness,
        PublicGrowthIssueMetrics,
        PublicGrowthSnapshot,
        PublicIssueOpsReadiness,
        PublicIssueOpsRemoteFile,
        PublicReleaseReadiness,
        PublicRepoMetrics,
    )

    return PublicGrowthSnapshot(
        repo=PublicRepoMetrics(
            full_name="octo-org/octo-repo",
            html_url="https://github.com/octo-org/octo-repo",
            stargazers=4,
            forks=0,
            watchers=4,
            subscribers=0,
            open_issues=0,
            pushed_at="2026-06-01T00:00:00Z",
            updated_at="2026-06-02T00:00:00Z",
            api_url="https://api.github.com/repos/octo-org/octo-repo",
        ),
        growth_issues=PublicGrowthIssueMetrics("tiangong:growth", 0, 0, 0),
        share_issues=PublicGrowthIssueMetrics("tiangong:share", 0, 0, 0),
        issueops_readiness=PublicIssueOpsReadiness(
            growth_form=PublicIssueOpsRemoteFile(
                route="Growth Issue Form",
                path=".github/ISSUE_TEMPLATE/tiangong-growth-flywheel.yml",
                status="missing",
            ),
            share_form=PublicIssueOpsRemoteFile(
                route="Share Proof Issue Form",
                path=".github/ISSUE_TEMPLATE/tiangong-share-proof.yml",
                status="missing",
            ),
            workflow=PublicIssueOpsRemoteFile(
                route="IssueOps Workflow",
                path=".github/workflows/issueops-onboarding.yml",
                status="missing",
            ),
        ),
        release_readiness=PublicReleaseReadiness(
            local_version="0.1.13",
            expected_tag="v0.1.13",
            status="missing",
        ),
        distribution_readiness=PublicDistributionReadiness(
            package_name="tiangong-mcp",
            local_version="0.1.13",
            published_version="0.0.1",
            status="stale",
        ),
    )


def _write_release_boundary_fixture(
    root: Path,
    *,
    include_terminal_ledger_commands: bool = True,
    include_mcp_public_proof_pack: bool = True,
    include_candidate_smoke: bool = True,
    include_stale_bare_install: bool = False,
    include_publish_tag_commit_guard: bool = True,
    candidate_tag: str = "v0.1.0",
) -> tuple[Path, Path]:
    project_root = root / "project"
    dist_dir = project_root / "dist"
    workflow_dir = project_root / ".github" / "workflows"
    dist_dir.mkdir(parents=True)
    workflow_dir.mkdir(parents=True)
    (project_root / "pyproject.toml").write_text(
        '\n'.join(
            [
                "[project]",
                'name = "tiangong-mcp"',
                'version = "0.1.0"',
                "",
                "[project.scripts]",
                'tiangong-mcp = "tiangong.cli:main"',
                "",
            ]
        ),
        encoding="utf-8",
    )
    readme_lines = [
        f'python -m pip install --upgrade "tiangong-mcp @ git+https://github.com/JinNing6/TianGong.git@{candidate_tag}"',
        "tiangong-mcp public-launch-assets",
        "tiangong-mcp public-install-command",
        "tiangong-mcp public-candidate-smoke --target-contributors 10",
        "tiangong-mcp public-launch-preflight --target-contributors 10",
        "tiangong-mcp public-growth-report --record-snapshot --target-contributors 10",
        "tiangong-mcp public-proof-pack --target-contributors 10",
        "tiangong-mcp public-release-boundary",
    ]
    if include_terminal_ledger_commands:
        readme_lines.extend(
            [
                "tiangong-mcp record-growth-referral --route growth --source-url https://github.com/owner/repo/issues/1",
                "tiangong-mcp record-share-attribution --contribution forge --share-url https://github.com/owner/repo/issues/2",
            ]
        )
    readme_text = "\n".join(readme_lines)
    (project_root / "README.md").write_text(readme_text, encoding="utf-8")
    (project_root / "README.zh-CN.md").write_text(readme_text, encoding="utf-8")
    workflow_text = "\n".join(
        [
            "permissions:",
            "  contents: read",
            "steps:",
            '  - run: tiangong-mcp public-launch-assets',
            '  - run: python -m build',
            '  - run: python -m twine check dist/*',
            '  - run: tiangong-mcp public-release-boundary',
            "",
        ]
    )
    (workflow_dir / "quality-gates.yml").write_text(workflow_text, encoding="utf-8")
    issueops_workflow_text = "\n".join(
        [
            "permissions:",
            "  issues: write",
            "steps:",
            "  - uses: actions/github-script@v8",
            "    with:",
            "      script: |",
            "        const lines = [",
            f"          'Current candidate install: `python -m pip install --upgrade \"tiangong-mcp @ git+https://github.com/JinNing6/TianGong.git@{candidate_tag}\"`',",
            "          'Install decision after installation: `tiangong-mcp public-install-command`'",
            "        ]",
            "",
        ]
    )
    (workflow_dir / "issueops-onboarding.yml").write_text(issueops_workflow_text, encoding="utf-8")
    verify_release_lines = [
        "          git fetch --force origin main:refs/remotes/origin/main --tags",
    ]
    if include_publish_tag_commit_guard:
        verify_release_lines.extend(
            [
                "          tag_commit=\"$(git rev-list -n 1 \"$RELEASE_TAG\")\"",
                "          head_commit=\"$(git rev-parse HEAD)\"",
                "          if [[ \"$tag_commit\" != \"$head_commit\" ]]; then",
                "            echo \"Checked-out commit $head_commit does not match $RELEASE_TAG commit $tag_commit\" >&2",
                "            exit 1",
                "          fi",
            ]
        )
    verify_release_lines.extend(
        [
            "          git merge-base --is-ancestor HEAD origin/main",
            "          echo 'pyproject.toml version'",
        ]
    )
    publish_workflow_text = "\n".join(
        [
            "on:",
            "  release:",
            "    types: [published]",
            "  push:",
            "    tags:",
            "      - \"v*\"",
            "  workflow_dispatch:",
            "    inputs:",
            "      tag:",
            "        description: Existing v* tag to publish, for example v0.1.0",
            "permissions:",
            "  contents: read",
            "concurrency:",
            "  group: tiangong-pypi-publish-${{ github.event.release.tag_name || github.ref_name || inputs.tag }}",
            "jobs:",
            "  publish:",
            "    environment: pypi",
            "    permissions:",
            "      contents: read",
            "      id-token: write",
            "    steps:",
            "      - name: Resolve release tag",
            "        env:",
            "          GITHUB_REF_NAME: ${{ github.ref_name }}",
            "        run: |",
            "          if [[ \"${{ github.event_name }}\" == \"release\" ]]; then",
            "            tag=\"${{ github.event.release.tag_name }}\"",
            "          elif [[ \"${{ github.event_name }}\" == \"push\" ]]; then",
            "            tag=\"${GITHUB_REF_NAME}\"",
            "          else",
            "            tag=\"${{ inputs.tag }}\"",
            "          fi",
            "          echo 'Release tag must look like v0.1.0'",
            "      - uses: actions/checkout@v6",
            "        with:",
            "          ref: ${{ steps.release.outputs.tag }}",
            "          fetch-depth: 0",
            "      - name: Verify release tag and package version",
            "        run: |",
            *verify_release_lines,
            "      - run: tiangong-mcp public-launch-assets",
            "      - run: python -m build",
            "      - run: python -m twine check dist/*",
            "      - run: tiangong-mcp public-release-boundary",
            "      - uses: pypa/gh-action-pypi-publish@release/v1",
            "",
        ]
    )
    (workflow_dir / "publish-pypi.yml").write_text(publish_workflow_text, encoding="utf-8")

    wheel = dist_dir / "tiangong_mcp-0.1.0-py3-none-any.whl"
    required_modules = [
        "tiangong/activation.py",
        "tiangong/cli.py",
        "tiangong/growth.py",
        "tiangong/install_bridge.py",
        "tiangong/candidate_smoke.py",
        "tiangong/launch_assets.py",
        "tiangong/onboarding.py",
        "tiangong/proof_pack.py",
        "tiangong/public_growth.py",
        "tiangong/release_boundary.py",
        "tiangong/season.py",
        "tiangong/mcp_server.py",
    ]
    with zipfile.ZipFile(wheel, "w") as archive:
        for module in required_modules:
            if module == "tiangong/cli.py" and include_terminal_ledger_commands:
                archive.writestr(
                    module,
                    'subparsers.add_parser("record-growth-referral")\n'
                    'subparsers.add_parser("record-share-attribution")\n'
                    + ('subparsers.add_parser("public-candidate-smoke")\n' if include_candidate_smoke else ""),
                )
            elif module == "tiangong/proof_pack.py" and include_terminal_ledger_commands:
                archive.writestr(
                    module,
                    "tiangong-mcp record-growth-referral\ntiangong-mcp record-share-attribution\n",
                )
            elif module == "tiangong/mcp_server.py" and include_mcp_public_proof_pack:
                archive.writestr(
                    module,
                    "\n".join(
                        [
                            "@mcp.tool()",
                            "async def public_proof_pack():",
                            "    return format_public_proof_pack()",
                            "@mcp.tool()",
                            "async def public_install_command():",
                            "    return format_public_install_command()",
                        ]
                    ),
                )
            elif module == "tiangong/candidate_smoke.py" and include_candidate_smoke:
                archive.writestr(
                    module,
                    "run_public_candidate_install_smoke\nformat_public_candidate_smoke\n",
                )
            elif module == "tiangong/season.py" and include_stale_bare_install:
                archive.writestr(module, '"加入修炼: pip install tiangong-mcp"\n')
            else:
                archive.writestr(module, "# packaged\n")
        archive.writestr(
            "tiangong_mcp-0.1.0.dist-info/METADATA",
            "\n".join(
                [
                    "Metadata-Version: 2.1",
                    "Name: tiangong-mcp",
                    "Version: 0.1.0",
                    "Description-Content-Type: text/markdown",
                    "",
                    f'Current candidate install: python -m pip install --upgrade "tiangong-mcp @ git+https://github.com/JinNing6/TianGong.git@{candidate_tag}"',
                    "",
                ]
            ),
        )
        archive.writestr(
            "tiangong_mcp-0.1.0.dist-info/entry_points.txt",
            "[console_scripts]\ntiangong-mcp = tiangong.cli:main\n",
        )

    sdist = dist_dir / "tiangong_mcp-0.1.0.tar.gz"
    with tarfile.open(sdist, "w:gz") as archive:
        for relative in ["pyproject.toml", "README.md", *required_modules]:
            source = project_root / relative
            source.parent.mkdir(parents=True, exist_ok=True)
            if not source.exists():
                if relative == "tiangong/cli.py" and include_terminal_ledger_commands:
                    source.write_text(
                        'subparsers.add_parser("record-growth-referral")\n'
                        'subparsers.add_parser("record-share-attribution")\n',
                        encoding="utf-8",
                    )
                    if include_candidate_smoke:
                        source.write_text(
                            source.read_text(encoding="utf-8")
                            + 'subparsers.add_parser("public-candidate-smoke")\n',
                            encoding="utf-8",
                        )
                elif relative == "tiangong/proof_pack.py" and include_terminal_ledger_commands:
                    source.write_text(
                        "tiangong-mcp record-growth-referral\ntiangong-mcp record-share-attribution\n",
                        encoding="utf-8",
                    )
                elif relative == "tiangong/mcp_server.py" and include_mcp_public_proof_pack:
                    source.write_text(
                        "\n".join(
                            [
                                "@mcp.tool()",
                                "async def public_proof_pack():",
                                "    return format_public_proof_pack()",
                                "@mcp.tool()",
                                "async def public_install_command():",
                                "    return format_public_install_command()",
                            ]
                        ),
                        encoding="utf-8",
                    )
                elif relative == "tiangong/candidate_smoke.py" and include_candidate_smoke:
                    source.write_text(
                        "run_public_candidate_install_smoke\nformat_public_candidate_smoke\n",
                        encoding="utf-8",
                    )
                elif relative == "tiangong/season.py" and include_stale_bare_install:
                    source.write_text('"加入修炼: pip install tiangong-mcp"\n', encoding="utf-8")
                else:
                    source.write_text("# source\n", encoding="utf-8")
            archive.add(source, arcname=f"tiangong_mcp-0.1.0/{relative}")

    return project_root, dist_dir


def test_console_script_points_to_cli_dispatcher():
    """The installed command should expose CLI launch gates while preserving MCP startup."""
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    assert pyproject["project"]["scripts"]["tiangong-mcp"] == "tiangong.cli:main"


def test_cli_without_args_starts_existing_mcp_server(monkeypatch):
    """Existing MCP clients call tiangong-mcp without args, so that path must stay intact."""
    from tiangong import cli

    called = []
    monkeypatch.setattr(cli, "_run_mcp_server", lambda: called.append("server"))

    assert cli.main([], stdout=StringIO()) == 0
    assert called == ["server"]


def test_cli_public_launch_preflight_prints_ordered_release_runbook(monkeypatch, tmp_path):
    """Maintainers should be able to run the public launch gate outside an MCP client."""
    from tiangong import cli

    event_path = tmp_path / "activation-events.jsonl"
    monkeypatch.setattr(cli, "get_activation_event_path", lambda: event_path)
    monkeypatch.setattr(cli, "fetch_public_growth_snapshot", _cold_launch_snapshot)

    stdout = StringIO()
    assert cli.main(["public-launch-preflight", "--target-contributors", "10"], stdout=stdout) == 0

    output = stdout.getvalue()
    assert "TianGong Public Launch Preflight" in output
    assert "Public Launch Closure Checklist" in output
    assert "First Public Proof Entrypoints" in output
    assert "template=tiangong-growth-flywheel.yml" in output
    assert "template=tiangong-share-proof.yml" in output
    assert "gh release create v0.1.13 --generate-notes" in output
    assert "https://github.com/octo-org/octo-repo/releases/new" in output
    assert "Select existing tag `v0.1.13`" in output
    assert "https://github.com/octo-org/octo-repo/actions/workflows/publish-pypi.yml" in output
    assert "public_growth_report(record_snapshot=True, target_contributors=10)" in output
    assert "After Submission CLI Ledger Commands" in output
    assert "tiangong-mcp record-growth-referral --route growth" in output
    assert "tiangong-mcp record-share-attribution --contribution forge" in output
    assert "does not invent downloads, retention, repost counts, referral conversions, or rewards" in output


def test_cli_public_launch_preflight_inlines_full_release_handoff(monkeypatch, tmp_path):
    """The main preflight should not hide the complete public growth release path in another command."""
    from tiangong import cli

    event_path = tmp_path / "activation-events.jsonl"
    monkeypatch.setattr(cli, "get_activation_event_path", lambda: event_path)
    monkeypatch.setattr(cli, "fetch_public_growth_snapshot", _cold_launch_snapshot)

    stdout = StringIO()
    assert cli.main(["public-launch-preflight", "--target-contributors", "10"], stdout=stdout) == 0

    output = stdout.getvalue()
    assert "Full Public Growth Release Handoff" in output
    assert "This preflight does not execute git, publish releases, or claim public traction." in output
    assert "tiangong-mcp public-launch-assets" in output
    assert "git add README.md README.zh-CN.md pyproject.toml" in output
    assert "git add tiangong/activation.py" in output
    assert "git add tests/test_cli.py" in output
    assert 'git commit -m "Prepare TianGong public growth launch"' in output
    assert "gh release create v0.1.13 --generate-notes" in output
    assert "git push origin v0.1.13" in output


def test_cli_public_launch_assets_prints_local_push_manifest():
    """The release operator should see exactly which local launch assets are ready to push."""
    from tiangong import cli

    stdout = StringIO()
    assert cli.main(["public-launch-assets"], stdout=stdout) == 0

    output = stdout.getvalue()
    assert "TianGong Public Launch Assets" in output
    assert "This command does not execute git, publish releases, or claim public traction." in output
    assert ".github/ISSUE_TEMPLATE/tiangong-growth-flywheel.yml" in output
    assert ".github/ISSUE_TEMPLATE/tiangong-share-proof.yml" in output
    assert ".github/workflows/issueops-onboarding.yml" in output
    assert "IssueOps workflow safety: ready" in output
    assert "Publish workflow: ready" in output
    assert "Quality workflow: ready" in output
    assert "git add .github/ISSUE_TEMPLATE/tiangong-growth-flywheel.yml" in output
    assert "Full Public Growth Release Bundle" in output
    assert "git add README.md README.zh-CN.md pyproject.toml" in output
    assert "git add .gitignore" in output
    assert ".github/ISSUE_TEMPLATE/config.yml" in output
    assert ".github/workflows/issueops-onboarding.yml .github/workflows/quality-gates.yml" in output
    assert "template config: ready" in output
    assert "git add tiangong/activation.py" in output
    assert "tiangong/candidate_smoke.py" in output
    assert "tiangong/artifact_system.py" in output
    assert "tiangong/install_bridge.py" in output
    assert "git add tests/test_cli.py" in output
    assert "\ngit add .\n" not in output
    assert "\ngit add . " not in output
    assert "Working Tree Release Coverage" in output
    assert "| review separately | `.github/` |" not in output
    assert "| review separately | `.github/workflows/issueops-onboarding.yml` |" not in output
    assert "| review separately | `tiangong/install_bridge.py` |" not in output
    assert 'git commit -m "Prepare TianGong public growth launch"' in output
    assert "gh release create v0.1.13 --generate-notes" in output
    assert "git push origin v0.1.13" in output
    assert "tiangong-mcp public-candidate-smoke --target-contributors 10" in output
    assert "tiangong-mcp public-launch-preflight --target-contributors 10" in output


def test_cli_public_launch_assets_preserves_campaign_target():
    """The local asset audit should not reset an active launch campaign target."""
    from tiangong import cli

    stdout = StringIO()
    assert cli.main(["public-launch-assets", "--target-contributors", "25"], stdout=stdout) == 0

    output = stdout.getvalue()
    assert "tiangong-mcp public-launch-assets --target-contributors 25" in output
    assert "tiangong-mcp public-install-command" in output
    assert "tiangong-mcp public-candidate-smoke --target-contributors 25" in output
    assert "tiangong-mcp public-launch-preflight --target-contributors 25" in output
    assert "tiangong-mcp public-growth-report --record-snapshot --target-contributors 25" in output
    assert "--target-contributors 10" not in output


def test_cli_public_install_command_prints_current_candidate_bridge(monkeypatch):
    """Release operators need one short command to share the correct install path."""
    from tiangong import cli
    from tiangong.public_growth import PublicDistributionReadiness

    monkeypatch.setattr(
        cli,
        "fetch_public_distribution_readiness",
        lambda: PublicDistributionReadiness(
            package_name="tiangong-mcp",
            local_version="0.1.13",
            published_version="0.0.1",
            status="stale",
            api_url="https://pypi.org/pypi/tiangong-mcp/json",
            project_url="https://pypi.org/project/tiangong-mcp/",
            reason="PyPI latest version differs from the local package metadata",
        ),
    )

    stdout = StringIO()
    assert cli.main(["public-install-command"], stdout=stdout) == 0

    output = stdout.getvalue()
    assert "TianGong Public Install Command" in output
    assert 'python -m pip install --upgrade "tiangong-mcp @ git+https://github.com/JinNing6/TianGong.git@v0.1.13"' in output
    assert "Canonical install after PyPI latest is current: `pip install -U tiangong-mcp`" in output
    assert "tiangong-mcp public-candidate-smoke --target-contributors 10" in output
    assert 'start_cultivation(username="your_github_username")' in output
    assert "does not close the PyPI install loop" in output


def test_cli_public_candidate_smoke_formats_real_install_gate(monkeypatch, tmp_path):
    """Release operators should have an explicit smoke gate for the current Git tag bridge."""
    from tiangong import cli
    from tiangong.candidate_smoke import CandidateSmokeResult

    calls = []

    def fake_smoke(**kwargs):
        calls.append(kwargs)
        return CandidateSmokeResult(
            package_name="tiangong-mcp",
            repo_owner="octo-org",
            repo_name="octo-repo",
            tag="v0.1.13",
            requirement="tiangong-mcp @ git+https://github.com/octo-org/octo-repo.git@v0.1.13",
            install_command='python -m pip install --upgrade "tiangong-mcp @ git+https://github.com/octo-org/octo-repo.git@v0.1.13"',
            temp_root=tmp_path / "smoke",
            installed_version="0.1.13",
            console_script_exists=True,
            install_surface_contains_tag=True,
            proof_pack_contains_tag=True,
            proof_pack_contains_external_invite=True,
            cleaned=True,
        )

    monkeypatch.setattr(cli, "run_public_candidate_install_smoke", fake_smoke)

    stdout = StringIO()
    assert (
        cli.main(
            [
                "public-candidate-smoke",
                "--repo-owner",
                "octo-org",
                "--repo-name",
                "octo-repo",
                "--tag",
                "v0.1.13",
                "--target-contributors",
                "25",
            ],
            stdout=stdout,
        )
        == 0
    )

    output = stdout.getvalue()
    assert calls[0]["repo_owner"] == "octo-org"
    assert calls[0]["repo_name"] == "octo-repo"
    assert calls[0]["version_or_tag"] == "v0.1.13"
    assert calls[0]["target_contributors"] == 25
    assert "# TianGong Public Candidate Install Smoke" in output
    assert "- Status: ready" in output
    assert "| Installed package version | ready | `0.1.13` matches `v0.1.13` |" in output
    assert "| Console script | ready | `tiangong-mcp` command is installed |" in output
    assert "| Proof pack invite | ready | proof pack includes the current tag and External Contributor invite |" in output
    assert "does not publish releases, upload distributions, record traction, or claim a closed install loop" in output


def test_candidate_smoke_runner_captures_subprocess_output_as_utf8(tmp_path):
    """Windows smoke runs should not let GBK console defaults corrupt UTF-8 launch output."""
    import subprocess

    from tiangong.candidate_smoke import run_public_candidate_install_smoke

    calls = []

    def fake_runner(command, **kwargs):
        calls.append((command, kwargs))
        assert kwargs["encoding"] == "utf-8"
        assert kwargs["errors"] == "replace"
        text_command = " ".join(command)
        if "-m venv" in text_command:
            venv = Path(command[-1])
            scripts = venv / "Scripts"
            scripts.mkdir(parents=True)
            (scripts / "python.exe").write_text("", encoding="utf-8")
            (scripts / "tiangong-mcp.exe").write_text("", encoding="utf-8")
            return subprocess.CompletedProcess(command, 0, "", "")
        if "importlib.metadata" in text_command:
            return subprocess.CompletedProcess(command, 0, "0.1.13\n", "")
        if "public-install-command" in text_command:
            return subprocess.CompletedProcess(command, 0, "candidate v0.1.13 天工\n", "")
        if "public-proof-pack" in text_command:
            return subprocess.CompletedProcess(command, 0, "v0.1.13\nCopy External Contributor Invite\n", "")
        return subprocess.CompletedProcess(command, 0, "", "")

    result = run_public_candidate_install_smoke(
        repo_owner="octo-org",
        repo_name="octo-repo",
        version_or_tag="v0.1.13",
        target_contributors=25,
        temp_parent=tmp_path,
        runner=fake_runner,
    )

    assert result.ready
    assert calls


def test_cli_public_proof_pack_prints_no_network_first_proof_runbook():
    """The first public proof pack should work even when public APIs are rate-limited."""
    from tiangong import cli

    stdout = StringIO()
    assert (
        cli.main(
            [
                "public-proof-pack",
                "--repo-owner",
                "octo-org",
                "--repo-name",
                "octo-repo",
                "--target-contributors",
                "10",
                "--actor",
                "maintainer",
                "--artifact-name",
                "first-growth-artifact",
            ],
            stdout=stdout,
        )
        == 0
    )

    output = stdout.getvalue()
    assert "TianGong First Public Proof Pack" in output
    assert "This command does not fetch GitHub or PyPI state" in output
    assert "https://github.com/octo-org/octo-repo/issues/new?" in output
    assert "template=tiangong-growth-flywheel.yml" in output
    assert "template=tiangong-share-proof.yml" in output
    assert "https://github.com/octo-org/octo-repo/issues/<opened-growth-issue-number>" in output
    assert "https://github.com/octo-org/octo-repo/issues/<opened-share-proof-issue-number>" in output
    assert 'record_growth_referral(route="growth"' in output
    assert 'record_share_attribution(contribution="forge"' in output
    assert "tiangong-mcp record-growth-referral" in output
    assert "tiangong-mcp record-share-attribution" in output
    assert "actor=\"maintainer\"" in output
    assert "Use created Issue URLs, not `issues/new?...` form URLs" in output
    assert "tiangong-mcp public-launch-assets" in output
    assert "tiangong-mcp public-release-boundary" in output
    assert "tiangong-mcp public-install-command" in output
    assert "tiangong-mcp public-candidate-smoke --target-contributors 10" in output
    assert "tiangong-mcp public-launch-preflight --target-contributors 10" in output
    assert "First External Contributor Path" in output
    assert "Share the candidate install first while PyPI is stale or unverified." in output
    assert "Install decision: tiangong-mcp public-install-command" in output
    assert "PyPI-current install after registry readiness: pip install -U tiangong-mcp" in output
    assert "Git Tag Candidate Install Bridge" in output
    assert 'python -m pip install --upgrade "tiangong-mcp @ git+https://github.com/octo-org/octo-repo.git@v0.1.13"' in output
    assert output.index("Current candidate install:") < output.index("Install decision:")
    invite = output.split("## Copy External Contributor Invite", 1)[1]
    assert invite.index("Current tag candidate install:") < invite.index(
        "PyPI-current install after registry readiness:"
    )
    assert "Use this only when public preflight reports PyPI latest is stale or unverified." in output
    assert 'start_cultivation(username="your_github_username")' in output
    assert 'forge_agent(name="first-growth-artifact"' in output
    assert "Only public Growth/Share Issue authors, public PR authors, and local ledger actors count" in output
    assert "Copy External Contributor Invite" in output
    assert "I want to be counted in the TianGong 72h launch" in output
    assert "does not invent downloads, retention, repost counts, referral conversions, or rewards" in output


def test_cli_record_growth_referral_writes_public_proof_to_local_ledger(monkeypatch, tmp_path):
    """Terminal release operators should be able to record created Growth Issues without an MCP client."""
    from tiangong import cli
    from tiangong.activation import EVENT_ISSUEOPS_REFERRAL_RECORDED, load_activation_events

    event_path = tmp_path / "activation-events.jsonl"
    monkeypatch.setattr(cli, "get_activation_event_path", lambda: event_path)

    stdout = StringIO()
    assert (
        cli.main(
            [
                "record-growth-referral",
                "--route",
                "growth",
                "--source-url",
                "https://github.com/octo-org/octo-repo/issues/7",
                "--actor",
                "maintainer",
                "--issue-number",
                "7",
                "--campaign-hook",
                "first public proof",
            ],
            stdout=stdout,
        )
        == 0
    )

    output = stdout.getvalue()
    events = load_activation_events(path=event_path)
    assert "CLI Growth Referral Recorded" in output
    assert "https://github.com/octo-org/octo-repo/issues/7" in output
    assert "activation_funnel()" in output
    assert "growth_flywheel()" in output
    assert "tiangong-mcp public-growth-report --record-snapshot --target-contributors 10" in output
    assert "tiangong-mcp public-proof-pack --target-contributors 10" in output
    assert events[0].event_type == EVENT_ISSUEOPS_REFERRAL_RECORDED
    assert events[0].actor == "maintainer"
    assert events[0].metadata["route"] == "growth"
    assert events[0].metadata["source_url"] == "https://github.com/octo-org/octo-repo/issues/7"
    assert events[0].metadata["issue_number"] == 7
    assert events[0].metadata["source_tool"] == "tiangong-mcp record-growth-referral"


def test_cli_record_growth_referral_rejects_form_entrypoint_and_placeholder(monkeypatch, tmp_path):
    """CLI referral recording should require the created public proof URL."""
    from tiangong import cli

    event_path = tmp_path / "activation-events.jsonl"
    monkeypatch.setattr(cli, "get_activation_event_path", lambda: event_path)

    for bad_url in [
        "https://github.com/octo-org/octo-repo/issues/new?template=tiangong-growth-flywheel.yml",
        "https://github.com/octo-org/octo-repo/issues/<opened-growth-issue-number>",
    ]:
        stdout = StringIO()
        assert (
            cli.main(
                [
                    "record-growth-referral",
                    "--source-url",
                    bad_url,
                    "--actor",
                    "maintainer",
                ],
                stdout=stdout,
            )
            == 0
        )

        output = stdout.getvalue()
        assert "CLI Growth Referral Not Written" in output
        assert "created public post/Issue/PR/Discussion URL" in output
        assert "tiangong-mcp record-growth-referral" in output

    assert not event_path.exists()


def test_cli_record_share_attribution_writes_public_share_to_local_ledger(monkeypatch, tmp_path):
    """Terminal release operators should be able to record Share Proof Issues without an MCP client."""
    from tiangong import cli
    from tiangong.activation import EVENT_SHARE_ATTRIBUTION_RECORDED, load_activation_events

    event_path = tmp_path / "activation-events.jsonl"
    monkeypatch.setattr(cli, "get_activation_event_path", lambda: event_path)

    stdout = StringIO()
    assert (
        cli.main(
            [
                "record-share-attribution",
                "--contribution",
                "forge",
                "--share-url",
                "https://github.com/octo-org/octo-repo/issues/8",
                "--source-url",
                "https://github.com/octo-org/octo-repo/issues/7",
                "--actor",
                "maintainer",
                "--artifact-name",
                "dragon-forge",
                "--issue-number",
                "8",
                "--campaign-hook",
                "first public proof",
            ],
            stdout=stdout,
        )
        == 0
    )

    output = stdout.getvalue()
    events = load_activation_events(path=event_path)
    assert "CLI Share Attribution Recorded" in output
    assert "https://github.com/octo-org/octo-repo/issues/8" in output
    assert "share_attribution_report()" in output
    assert "leaderboard(type=\"share\")" in output
    assert "activation_funnel()" in output
    assert "tiangong-mcp public-proof-pack --target-contributors 10" in output
    assert events[0].event_type == EVENT_SHARE_ATTRIBUTION_RECORDED
    assert events[0].actor == "maintainer"
    assert events[0].artifact_name == "dragon-forge"
    assert events[0].metadata["contribution"] == "forge"
    assert events[0].metadata["share_url"] == "https://github.com/octo-org/octo-repo/issues/8"
    assert events[0].metadata["source_url"] == "https://github.com/octo-org/octo-repo/issues/7"
    assert events[0].metadata["issue_number"] == 8
    assert events[0].metadata["source_tool"] == "tiangong-mcp record-share-attribution"


def test_cli_record_share_attribution_rejects_form_entrypoint_and_placeholder(monkeypatch, tmp_path):
    """CLI share attribution should reject Issue Form URLs and placeholders for both proof fields."""
    from tiangong import cli

    event_path = tmp_path / "activation-events.jsonl"
    monkeypatch.setattr(cli, "get_activation_event_path", lambda: event_path)

    invalid_args = [
        [
            "--share-url",
            "https://github.com/octo-org/octo-repo/issues/new?template=tiangong-share-proof.yml",
        ],
        [
            "--share-url",
            "https://github.com/octo-org/octo-repo/issues/<opened-share-proof-issue-number>",
        ],
        [
            "--share-url",
            "https://github.com/octo-org/octo-repo/issues/8",
            "--source-url",
            "https://github.com/octo-org/octo-repo/issues/new?template=tiangong-growth-flywheel.yml",
        ],
    ]
    for extra_args in invalid_args:
        stdout = StringIO()
        assert (
            cli.main(
                [
                    "record-share-attribution",
                    "--contribution",
                    "forge",
                    "--actor",
                    "maintainer",
                    "--artifact-name",
                    "dragon-forge",
                    *extra_args,
                ],
                stdout=stdout,
            )
            == 0
        )

        output = stdout.getvalue()
        assert "CLI Share Attribution Not Written" in output
        assert "created public post/Issue/PR/Discussion URL" in output
        assert "tiangong-mcp record-share-attribution" in output

    assert not event_path.exists()


def test_cli_public_release_boundary_prints_package_boundary(tmp_path):
    """Release operators should verify the built package still contains the public growth loop."""
    from tiangong import cli

    project_root, dist_dir = _write_release_boundary_fixture(tmp_path)

    stdout = StringIO()
    assert cli.main(["public-release-boundary", "--root", str(project_root), "--dist", str(dist_dir)], stdout=stdout) == 0

    output = stdout.getvalue()
    assert "TianGong Public Release Boundary" in output
    assert "This command does not upload distributions, create releases, or claim public traction." in output
    assert "Wheel entry point | ready" in output
    assert "Growth modules in wheel | ready" in output
    assert "Proof ledger CLI routes | ready" in output
    assert "Candidate install smoke route | ready" in output
    assert "Public recovery MCP routes | ready" in output
    assert "Public install copy in package | ready" in output
    assert "Candidate install tag version | ready" in output
    assert "Source distribution | ready" in output
    assert "Documentation commands | ready" in output
    assert "Workflow release-boundary steps | ready" in output
    assert "tag commit must match checkout HEAD" in output
    assert "tag push" in output
    assert "tiangong-mcp public-install-command" in output
    assert "tiangong-mcp public-candidate-smoke --target-contributors 10" in output
    assert "tiangong-mcp public-release-boundary" in output
    assert "Local Release Boundary Status" in output
    assert "blocked" not in output


def test_cli_public_release_boundary_prefers_current_version_artifacts(tmp_path):
    """A stale dist file should not hide the current package artifact after a version bump."""
    from tiangong import cli

    project_root, dist_dir = _write_release_boundary_fixture(tmp_path)
    (project_root / "pyproject.toml").write_text(
        "\n".join(
            [
                "[project]",
                'name = "tiangong-mcp"',
                'version = "0.1.13"',
                "",
                "[project.scripts]",
                'tiangong-mcp = "tiangong.cli:main"',
                "",
            ]
        ),
        encoding="utf-8",
    )
    for relative in ["README.md", "README.zh-CN.md", ".github/workflows/issueops-onboarding.yml"]:
        path = project_root / relative
        path.write_text(path.read_text(encoding="utf-8").replace("@v0.1.0", "@v0.1.13"), encoding="utf-8")

    stale_wheel = dist_dir / "tiangong_mcp-0.1.0-py3-none-any.whl"
    current_wheel = dist_dir / "tiangong_mcp-0.1.13-py3-none-any.whl"
    with zipfile.ZipFile(stale_wheel) as source, zipfile.ZipFile(current_wheel, "w") as target:
        for name in source.namelist():
            if ".dist-info/" not in name:
                target.writestr(name, source.read(name))
        target.writestr(
            "tiangong_mcp-0.1.13.dist-info/METADATA",
            "\n".join(
                [
                    "Metadata-Version: 2.1",
                    "Name: tiangong-mcp",
                    "Version: 0.1.13",
                    "Description-Content-Type: text/markdown",
                    "",
                    'Current candidate install: python -m pip install --upgrade "tiangong-mcp @ git+https://github.com/JinNing6/TianGong.git@v0.1.13"',
                    "",
                ]
            ),
        )
        target.writestr(
            "tiangong_mcp-0.1.13.dist-info/entry_points.txt",
            "[console_scripts]\ntiangong-mcp = tiangong.cli:main\n",
        )

    stale_sdist = dist_dir / "tiangong_mcp-0.1.0.tar.gz"
    current_sdist = dist_dir / "tiangong_mcp-0.1.13.tar.gz"
    with tarfile.open(stale_sdist, "r:gz") as source, tarfile.open(current_sdist, "w:gz") as target:
        for member in source.getmembers():
            extracted = source.extractfile(member)
            if extracted is None:
                continue
            member.name = member.name.replace("tiangong_mcp-0.1.0/", "tiangong_mcp-0.1.13/", 1)
            if member.name.endswith("/README.md"):
                data = source.extractfile(member)
                if data is None:
                    continue
                readme_text = data.read().decode("utf-8").replace("@v0.1.0", "@v0.1.13")
                encoded = readme_text.encode("utf-8")
                member.size = len(encoded)
                target.addfile(member, BytesIO(encoded))
            else:
                target.addfile(member, extracted)

    stdout = StringIO()
    assert cli.main(["public-release-boundary", "--root", str(project_root), "--dist", str(dist_dir)], stdout=stdout) == 0

    output = stdout.getvalue()
    assert "Wheel distribution | ready" in output
    assert "tiangong_mcp-0.1.13-py3-none-any.whl" in output
    assert "tiangong_mcp-0.1.0-py3-none-any.whl` version `0.1.0` vs local `0.1.13" not in output
    assert "Local Release Boundary Status" in output


def test_cli_public_release_boundary_blocks_missing_terminal_ledger_commands(tmp_path):
    """Release boundary should fail if a build drops terminal proof-ledger routes."""
    from tiangong import cli

    project_root, dist_dir = _write_release_boundary_fixture(tmp_path, include_terminal_ledger_commands=False)

    stdout = StringIO()
    assert cli.main(["public-release-boundary", "--root", str(project_root), "--dist", str(dist_dir)], stdout=stdout) == 0

    output = stdout.getvalue()
    assert "Proof ledger CLI routes | blocked" in output
    assert "Documentation commands | blocked" in output
    assert "tiangong-mcp record-growth-referral" in output
    assert "tiangong-mcp record-share-attribution" in output
    assert "Local Release Boundary Blockers" in output


def test_cli_public_release_boundary_blocks_missing_mcp_public_recovery_routes(tmp_path):
    """Release boundary should fail if a package drops MCP public recovery routes."""
    from tiangong import cli

    project_root, dist_dir = _write_release_boundary_fixture(tmp_path, include_mcp_public_proof_pack=False)

    stdout = StringIO()
    assert cli.main(["public-release-boundary", "--root", str(project_root), "--dist", str(dist_dir)], stdout=stdout) == 0

    output = stdout.getvalue()
    assert "Public recovery MCP routes | blocked" in output
    assert "public_proof_pack" in output
    assert "public_install_command" in output
    assert "Local Release Boundary Blockers" in output


def test_cli_public_release_boundary_blocks_missing_candidate_smoke_route(tmp_path):
    """Release boundary should fail if the package drops the candidate install smoke gate."""
    from tiangong import cli

    project_root, dist_dir = _write_release_boundary_fixture(tmp_path, include_candidate_smoke=False)

    stdout = StringIO()
    assert cli.main(["public-release-boundary", "--root", str(project_root), "--dist", str(dist_dir)], stdout=stdout) == 0

    output = stdout.getvalue()
    assert "Candidate install smoke route | blocked" in output
    assert "candidate_smoke.py" in output
    assert "public-candidate-smoke" in output
    assert "Local Release Boundary Blockers" in output


def test_cli_public_release_boundary_blocks_stale_public_install_copy(tmp_path):
    """Release boundary should fail if built packages leak the stale PyPI install path."""
    from tiangong import cli

    project_root, dist_dir = _write_release_boundary_fixture(tmp_path, include_stale_bare_install=True)

    stdout = StringIO()
    assert cli.main(["public-release-boundary", "--root", str(project_root), "--dist", str(dist_dir)], stdout=stdout) == 0

    output = stdout.getvalue()
    assert "Public install copy in package | blocked" in output
    assert "pip install tiangong-mcp" in output
    assert "tiangong/season.py" in output
    assert "Local Release Boundary Blockers" in output


def test_cli_public_release_boundary_blocks_stale_candidate_install_tag(tmp_path):
    """Release boundary should fail if public install bridges point at an older tag."""
    from tiangong import cli

    project_root, dist_dir = _write_release_boundary_fixture(tmp_path, candidate_tag="v0.0.9")

    stdout = StringIO()
    assert cli.main(["public-release-boundary", "--root", str(project_root), "--dist", str(dist_dir)], stdout=stdout) == 0

    output = stdout.getvalue()
    assert "Candidate install tag version | blocked" in output
    assert "v0.0.9" in output
    assert "v0.1.0" in output
    assert "README.md" in output
    assert "issueops-onboarding.yml" in output
    assert "wheel METADATA" in output
    assert "sdist README.md" in output
    assert "Local Release Boundary Blockers" in output


def test_cli_public_release_boundary_blocks_publish_workflow_without_tag_commit_guard(tmp_path):
    """Release boundary should fail if PyPI publishing can build a commit different from the release tag."""
    from tiangong import cli

    project_root, dist_dir = _write_release_boundary_fixture(tmp_path, include_publish_tag_commit_guard=False)

    stdout = StringIO()
    assert cli.main(["public-release-boundary", "--root", str(project_root), "--dist", str(dist_dir)], stdout=stdout) == 0

    output = stdout.getvalue()
    assert "Workflow release-boundary steps | blocked" in output
    assert 'git rev-list -n 1 "$RELEASE_TAG"' in output
    assert "git rev-parse HEAD" in output
    assert "Checked-out commit" in output
    assert "Local Release Boundary Blockers" in output


def test_cli_reconfigures_text_streams_for_unicode_launch_output(monkeypatch, tmp_path):
    """Windows consoles may default to GBK; the CLI should still print brand output."""
    from tiangong import cli

    event_path = tmp_path / "activation-events.jsonl"
    monkeypatch.setattr(cli, "get_activation_event_path", lambda: event_path)
    monkeypatch.setattr(cli, "fetch_public_growth_snapshot", _cold_launch_snapshot)
    raw_output = BytesIO()
    stdout = TextIOWrapper(raw_output, encoding="gbk")

    assert cli.main(["public-launch-preflight"], stdout=stdout) == 0
    stdout.flush()

    output = raw_output.getvalue().decode("utf-8")
    assert "TianGong Public Launch Preflight" in output
    assert "⚒" in output


def test_readmes_document_terminal_public_launch_gate():
    """Public launch gates should be visible outside MCP-only tool tables."""
    for filename in ["README.md", "README.zh-CN.md"]:
        text = (ROOT / filename).read_text(encoding="utf-8")

        assert "tiangong-mcp public-launch-assets" in text
        assert "tiangong-mcp public-install-command" in text
        assert "tiangong-mcp public-candidate-smoke --target-contributors 10" in text
        assert "tiangong-mcp public-launch-preflight --target-contributors 10" in text
        assert "tiangong-mcp public-growth-report --record-snapshot --target-contributors 10" in text
        assert "tiangong-mcp public-proof-pack --target-contributors 10" in text
        assert "tiangong-mcp public-release-boundary" in text
        assert "tiangong-mcp record-growth-referral" in text
        assert "tiangong-mcp record-share-attribution" in text
        assert "public growth release handoff" in text or "完整公开增长 release handoff" in text
        assert "tiangong-mcp` without arguments" in text or "tiangong-mcp` 不带参数" in text
