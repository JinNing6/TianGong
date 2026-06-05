"""Install bridge helpers for public launch paths blocked by stale PyPI state."""

from __future__ import annotations

import importlib.metadata as importlib_metadata

from .config import config

DEFAULT_PACKAGE_NAME = "tiangong-mcp"


def clean_install_arg(value: str, fallback: str) -> str:
    """Normalize a public install command argument without trusting arbitrary whitespace."""
    text = " ".join(str(value or "").split())[:160]
    return text or fallback


def normalize_release_tag(version_or_tag: str) -> str:
    """Return a v-prefixed tag from a version or an existing Git ref."""
    value = clean_install_arg(version_or_tag, "current-local-version")
    if value.startswith("refs/tags/"):
        value = value.removeprefix("refs/tags/")
    return value if value.startswith("v") else f"v{value}"


def local_package_version(package_name: str = DEFAULT_PACKAGE_NAME) -> str:
    """Read the installed project version for no-network proof pack output."""
    try:
        return importlib_metadata.version(package_name)
    except importlib_metadata.PackageNotFoundError:
        return "current-local-version"


def git_tag_install_requirement(
    *,
    repo_owner: str,
    repo_name: str,
    version_or_tag: str,
    package_name: str = DEFAULT_PACKAGE_NAME,
) -> str:
    """Build a pip direct URL requirement for the current public Git tag."""
    owner = clean_install_arg(repo_owner, config.GITHUB_REPO_OWNER)
    repo = clean_install_arg(repo_name, config.GITHUB_REPO_NAME)
    package = clean_install_arg(package_name, DEFAULT_PACKAGE_NAME)
    tag = normalize_release_tag(version_or_tag)
    return f"{package} @ git+https://github.com/{owner}/{repo}.git@{tag}"


def git_tag_install_command(
    *,
    repo_owner: str,
    repo_name: str,
    version_or_tag: str,
    package_name: str = DEFAULT_PACKAGE_NAME,
) -> str:
    """Build the contributor command that upgrades from a current Git tag."""
    requirement = git_tag_install_requirement(
        repo_owner=repo_owner,
        repo_name=repo_name,
        version_or_tag=version_or_tag,
        package_name=package_name,
    )
    return f'python -m pip install --upgrade "{requirement}"'


def current_candidate_install_command(package_name: str = DEFAULT_PACKAGE_NAME) -> str:
    """Build the current local-version Git tag install command for public share cards."""
    package = clean_install_arg(package_name, DEFAULT_PACKAGE_NAME)
    return git_tag_install_command(
        repo_owner="",
        repo_name="",
        version_or_tag=local_package_version(package),
        package_name=package,
    )


def format_candidate_join_lines(
    package_name: str = DEFAULT_PACKAGE_NAME,
    *,
    join_label: str = "加入修炼",
) -> list[str]:
    """Return plain-text install lines for compact public share blocks."""
    package = clean_install_arg(package_name, DEFAULT_PACKAGE_NAME)
    label = clean_install_arg(join_label, "加入修炼")
    return [
        f"{label}: {current_candidate_install_command(package)}",
        f"安装后复查: {package} public-install-command",
        f"PyPI 追平后安装: pip install -U {package}",
    ]


def format_candidate_join_text(
    package_name: str = DEFAULT_PACKAGE_NAME,
    *,
    join_label: str = "加入修炼",
) -> str:
    """Return newline-joined install lines for paste-ready code blocks."""
    return "\n".join(format_candidate_join_lines(package_name, join_label=join_label))


def format_candidate_install_markdown_lines(package_name: str = DEFAULT_PACKAGE_NAME) -> list[str]:
    """Return Markdown bullet install lines for Discussion/PR recovery surfaces."""
    package = clean_install_arg(package_name, DEFAULT_PACKAGE_NAME)
    return [
        f"- 当前候选安装: `{current_candidate_install_command(package)}`",
        f"- 安装后复查: `{package} public-install-command`",
        f"- PyPI 追平后安装: `pip install -U {package}`",
    ]


def format_candidate_install_markdown_text(package_name: str = DEFAULT_PACKAGE_NAME) -> str:
    """Return newline-joined Markdown install bullets for generated public posts."""
    return "\n".join(format_candidate_install_markdown_lines(package_name))


def format_current_candidate_install_bridge_lines(
    *,
    repo_owner: str,
    repo_name: str,
    version_or_tag: str,
    package_name: str = DEFAULT_PACKAGE_NAME,
) -> list[str]:
    """Format report lines for a candidate install bridge while PyPI is stale."""
    package = clean_install_arg(package_name, DEFAULT_PACKAGE_NAME)
    command = git_tag_install_command(
        repo_owner=repo_owner,
        repo_name=repo_name,
        version_or_tag=version_or_tag,
        package_name=package,
    )
    return [
        "## Current Candidate Git Tag Install Bridge",
        "",
        "> This bridge keeps contributors on the current tag while PyPI is stale or unverified; it does not close the PyPI install loop.",
        f"- Candidate install: `{command}`",
        f"- Canonical install after PyPI latest is current: `pip install -U {package}`",
        "- Recheck distribution proof with `public_growth_report()` before calling the install loop closed.",
        "",
    ]
