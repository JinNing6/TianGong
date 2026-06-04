"""Public GitHub traction proof surfaces for TianGong growth loops."""

from __future__ import annotations

import importlib.metadata as importlib_metadata
import json
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request
from urllib.request import urlopen as _urlopen

from .activation import (
    EVENT_ISSUEOPS_REFERRAL_RECORDED,
    EVENT_SHARE_ATTRIBUTION_RECORDED,
    ActivationEvent,
    build_share_proof_issue_url,
)
from .config import config
from .growth import build_growth_issue_url
from .launch_assets import format_full_public_growth_release_handoff_lines
from .proof_pack import format_public_proof_pack

GITHUB_API_VERSION = "2026-03-10"
GITHUB_API_BASE = "https://api.github.com"
GROWTH_LABEL = "tiangong:growth"
SHARE_LABEL = "tiangong:share"
GROWTH_FORM_PATH = ".github/ISSUE_TEMPLATE/tiangong-growth-flywheel.yml"
SHARE_FORM_PATH = ".github/ISSUE_TEMPLATE/tiangong-share-proof.yml"
ISSUEOPS_WORKFLOW_PATH = ".github/workflows/issueops-onboarding.yml"
PACKAGE_NAME = "tiangong-mcp"
PYPI_JSON_URL = f"https://pypi.org/pypi/{PACKAGE_NAME}/json"
PYPI_PROJECT_URL = f"https://pypi.org/project/{PACKAGE_NAME}/"
PYPI_PROJECT_PUBLISHING_URL = f"https://pypi.org/manage/project/{PACKAGE_NAME}/settings/publishing/"
PYPI_TRUSTED_PUBLISHER_WORKFLOW_FILENAME = "publish-pypi.yml"
PYPI_TRUSTED_PUBLISHER_WORKFLOW_PATH = f".github/workflows/{PYPI_TRUSTED_PUBLISHER_WORKFLOW_FILENAME}"
PYPI_TRUSTED_PUBLISHER_ENVIRONMENT = "pypi"


@dataclass(frozen=True)
class PublicRepoMetrics:
    """Public repository-level signals returned by GitHub's repository endpoint."""

    full_name: str
    html_url: str
    stargazers: int
    forks: int
    watchers: int
    subscribers: int
    open_issues: int
    pushed_at: str
    updated_at: str
    api_url: str


@dataclass(frozen=True)
class PublicIssueRecord:
    """One public issue record used as reviewable growth proof."""

    number: int
    title: str
    state: str
    url: str
    author: str


@dataclass(frozen=True)
class PublicPullRequestRecord:
    """One public pull request record used as reviewable contribution proof."""

    number: int
    title: str
    state: str
    url: str
    author: str


@dataclass(frozen=True)
class PublicGrowthIssueMetrics:
    """Public IssueOps counts for a specific TianGong route label."""

    label: str
    total: int
    open: int
    closed: int
    latest: list[PublicIssueRecord] = field(default_factory=list)
    api_url: str = ""
    truncated: bool = False
    actors: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class PublicPullRequestMetrics:
    """Public pull request counts and authors from the repository PR endpoint."""

    total: int = 0
    open: int = 0
    closed: int = 0
    latest: list[PublicPullRequestRecord] = field(default_factory=list)
    api_url: str = ""
    truncated: bool = False
    actors: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class PublicIssueOpsRemoteFile:
    """One remote file required for a public GitHub IssueOps growth route."""

    route: str = ""
    path: str = ""
    status: str = "not_checked"
    api_url: str = ""
    html_url: str = ""
    reason: str = ""


@dataclass(frozen=True)
class PublicIssueOpsReadiness:
    """Remote default-branch readiness for the public IssueOps acquisition loop."""

    growth_form: PublicIssueOpsRemoteFile = field(
        default_factory=lambda: PublicIssueOpsRemoteFile(
            route="Growth Issue Form",
            path=GROWTH_FORM_PATH,
            status="not_checked",
            reason="remote contents were not checked",
        )
    )
    share_form: PublicIssueOpsRemoteFile = field(
        default_factory=lambda: PublicIssueOpsRemoteFile(
            route="Share Proof Issue Form",
            path=SHARE_FORM_PATH,
            status="not_checked",
            reason="remote contents were not checked",
        )
    )
    workflow: PublicIssueOpsRemoteFile = field(
        default_factory=lambda: PublicIssueOpsRemoteFile(
            route="IssueOps Workflow",
            path=ISSUEOPS_WORKFLOW_PATH,
            status="not_checked",
            reason="remote contents were not checked",
        )
    )

    @property
    def files(self) -> tuple[PublicIssueOpsRemoteFile, ...]:
        return (self.growth_form, self.share_form, self.workflow)

    @property
    def missing_files(self) -> tuple[PublicIssueOpsRemoteFile, ...]:
        return tuple(item for item in self.files if item.status == "missing")

    @property
    def unverified_files(self) -> tuple[PublicIssueOpsRemoteFile, ...]:
        return tuple(item for item in self.files if item.status == "unverified")


@dataclass(frozen=True)
class PublicDistributionReadiness:
    """PyPI distribution readiness for the public install loop."""

    package_name: str = PACKAGE_NAME
    local_version: str = ""
    published_version: str = ""
    status: str = "not_checked"
    api_url: str = PYPI_JSON_URL
    project_url: str = PYPI_PROJECT_URL
    reason: str = "PyPI distribution was not checked"


@dataclass(frozen=True)
class PublicReleaseReadiness:
    """GitHub Release readiness for the release-triggered PyPI publishing loop."""

    local_version: str = ""
    expected_tag: str = ""
    status: str = "not_checked"
    api_url: str = ""
    html_url: str = ""
    reason: str = "GitHub release was not checked"


@dataclass(frozen=True)
class PublicGrowthSnapshot:
    """A public GitHub snapshot that can be compared with the local MCP ledger."""

    repo: PublicRepoMetrics
    growth_issues: PublicGrowthIssueMetrics
    share_issues: PublicGrowthIssueMetrics
    pull_requests: PublicPullRequestMetrics = field(default_factory=PublicPullRequestMetrics)
    issueops_readiness: PublicIssueOpsReadiness = field(default_factory=PublicIssueOpsReadiness)
    release_readiness: PublicReleaseReadiness = field(default_factory=PublicReleaseReadiness)
    distribution_readiness: PublicDistributionReadiness = field(default_factory=PublicDistributionReadiness)


@dataclass(frozen=True)
class PublicGrowthHistoryEntry:
    """One persisted public growth snapshot from real GitHub and local ledger data."""

    timestamp: float
    repo_full_name: str
    repo_url: str
    stargazers: int
    forks: int
    watchers: int
    subscribers: int
    open_issues: int
    growth_issues: int
    share_issues: int
    pull_requests: int
    local_referrals: int
    local_shares: int


class PublicGrowthFetchError(RuntimeError):
    """Raised when the public GitHub snapshot cannot be fetched."""


def _safe_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _github_request_json(
    url: str,
    *,
    token: str = "",
    timeout: float = 10.0,
    urlopen: Callable[..., Any] = _urlopen,
) -> Any:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-github-api-version": GITHUB_API_VERSION,
        "User-Agent": "tiangong-mcp-public-growth",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = Request(url, headers=headers)
    try:
        with urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except HTTPError as exc:
        raise PublicGrowthFetchError(f"GitHub API HTTP {exc.code}: {exc.reason}") from exc
    except URLError as exc:
        raise PublicGrowthFetchError(f"GitHub API connection failed: {exc.reason}") from exc
    except OSError as exc:
        raise PublicGrowthFetchError(f"GitHub API request failed: {exc}") from exc

    try:
        return json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PublicGrowthFetchError(f"GitHub API returned unreadable JSON: {exc}") from exc


def _pypi_request_json(
    url: str,
    *,
    timeout: float = 10.0,
    urlopen: Callable[..., Any] = _urlopen,
) -> Any:
    request = Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "tiangong-mcp-public-growth",
        },
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except HTTPError as exc:
        raise PublicGrowthFetchError(f"PyPI API HTTP {exc.code}: {exc.reason}") from exc
    except URLError as exc:
        raise PublicGrowthFetchError(f"PyPI API connection failed: {exc.reason}") from exc
    except OSError as exc:
        raise PublicGrowthFetchError(f"PyPI API request failed: {exc}") from exc

    try:
        return json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PublicGrowthFetchError(f"PyPI API returned unreadable JSON: {exc}") from exc


def get_local_package_version(package_name: str = PACKAGE_NAME) -> str:
    """Return the installed package version used by the public install loop."""
    try:
        return importlib_metadata.version(package_name)
    except importlib_metadata.PackageNotFoundError:
        return ""


def _repo_url(owner: str, repo: str) -> str:
    return f"{GITHUB_API_BASE}/repos/{owner}/{repo}"


def _issues_url(owner: str, repo: str, label: str, page: int) -> str:
    query = urlencode(
        {
            "state": "all",
            "labels": label,
            "per_page": 100,
            "page": page,
        }
    )
    return f"{GITHUB_API_BASE}/repos/{owner}/{repo}/issues?{query}"


def _pulls_url(owner: str, repo: str, page: int) -> str:
    query = urlencode(
        {
            "state": "all",
            "per_page": 100,
            "page": page,
        }
    )
    return f"{GITHUB_API_BASE}/repos/{owner}/{repo}/pulls?{query}"


def _contents_url(owner: str, repo: str, path: str) -> str:
    return f"{GITHUB_API_BASE}/repos/{owner}/{repo}/contents/{quote(path, safe='/.')}"


def _release_by_tag_url(owner: str, repo: str, tag: str) -> str:
    return f"{GITHUB_API_BASE}/repos/{owner}/{repo}/releases/tags/{quote(tag, safe='')}"


def _expected_release_tag(local_version: str) -> str:
    return f"v{local_version}" if local_version else ""


def _parse_repo_metrics(payload: dict[str, Any], api_url: str) -> PublicRepoMetrics:
    return PublicRepoMetrics(
        full_name=str(payload.get("full_name") or ""),
        html_url=str(payload.get("html_url") or ""),
        stargazers=_safe_int(payload.get("stargazers_count")),
        forks=_safe_int(payload.get("forks_count", payload.get("forks"))),
        watchers=_safe_int(payload.get("watchers_count", payload.get("watchers"))),
        subscribers=_safe_int(payload.get("subscribers_count")),
        open_issues=_safe_int(payload.get("open_issues_count", payload.get("open_issues"))),
        pushed_at=str(payload.get("pushed_at") or ""),
        updated_at=str(payload.get("updated_at") or ""),
        api_url=api_url,
    )


def _parse_issue_record(payload: dict[str, Any]) -> PublicIssueRecord:
    user = payload.get("user")
    author = ""
    if isinstance(user, dict):
        author = str(user.get("login") or "")
    return PublicIssueRecord(
        number=_safe_int(payload.get("number")),
        title=str(payload.get("title") or ""),
        state=str(payload.get("state") or ""),
        url=str(payload.get("html_url") or ""),
        author=author,
    )


def _parse_pull_request_record(payload: dict[str, Any]) -> PublicPullRequestRecord:
    user = payload.get("user")
    author = ""
    if isinstance(user, dict):
        author = str(user.get("login") or "")
    return PublicPullRequestRecord(
        number=_safe_int(payload.get("number")),
        title=str(payload.get("title") or ""),
        state=str(payload.get("state") or ""),
        url=str(payload.get("html_url") or ""),
        author=author,
    )


def _fetch_issue_metrics(
    owner: str,
    repo: str,
    label: str,
    *,
    token: str,
    timeout: float,
    urlopen: Callable[..., Any],
    max_pages: int,
) -> PublicGrowthIssueMetrics:
    total = 0
    open_count = 0
    closed_count = 0
    latest: list[PublicIssueRecord] = []
    actors: set[str] = set()
    truncated = False
    first_url = _issues_url(owner, repo, label, page=1)

    for page in range(1, max_pages + 1):
        page_url = _issues_url(owner, repo, label, page=page)
        payload = _github_request_json(page_url, token=token, timeout=timeout, urlopen=urlopen)
        if not isinstance(payload, list):
            raise PublicGrowthFetchError(f"GitHub issues endpoint returned {type(payload).__name__}, not a list")

        issues = [item for item in payload if isinstance(item, dict) and "pull_request" not in item]
        total += len(issues)
        open_count += sum(1 for item in issues if item.get("state") == "open")
        closed_count += sum(1 for item in issues if item.get("state") == "closed")
        for item in issues:
            user = item.get("user")
            if isinstance(user, dict) and user.get("login"):
                actors.add(str(user["login"]))
            if len(latest) < 5:
                latest.append(_parse_issue_record(item))

        if len(payload) < 100:
            break
    else:
        truncated = True

    return PublicGrowthIssueMetrics(
        label=label,
        total=total,
        open=open_count,
        closed=closed_count,
        latest=latest,
        api_url=first_url,
        truncated=truncated,
        actors=tuple(sorted(actors, key=str.lower)),
    )


def _fetch_pull_request_metrics(
    owner: str,
    repo: str,
    *,
    token: str,
    timeout: float,
    urlopen: Callable[..., Any],
    max_pages: int,
) -> PublicPullRequestMetrics:
    total = 0
    open_count = 0
    closed_count = 0
    latest: list[PublicPullRequestRecord] = []
    actors: set[str] = set()
    truncated = False
    first_url = _pulls_url(owner, repo, page=1)

    for page in range(1, max_pages + 1):
        page_url = _pulls_url(owner, repo, page=page)
        payload = _github_request_json(page_url, token=token, timeout=timeout, urlopen=urlopen)
        if not isinstance(payload, list):
            raise PublicGrowthFetchError(f"GitHub pulls endpoint returned {type(payload).__name__}, not a list")

        pulls = [item for item in payload if isinstance(item, dict)]
        total += len(pulls)
        open_count += sum(1 for item in pulls if item.get("state") == "open")
        closed_count += sum(1 for item in pulls if item.get("state") == "closed")
        for item in pulls:
            user = item.get("user")
            if isinstance(user, dict) and user.get("login"):
                actors.add(str(user["login"]))
            if len(latest) < 5:
                latest.append(_parse_pull_request_record(item))

        if len(payload) < 100:
            break
    else:
        truncated = True

    return PublicPullRequestMetrics(
        total=total,
        open=open_count,
        closed=closed_count,
        latest=latest,
        api_url=first_url,
        truncated=truncated,
        actors=tuple(sorted(actors, key=str.lower)),
    )


def _fetch_issueops_remote_file(
    owner: str,
    repo: str,
    *,
    route: str,
    path: str,
    token: str,
    timeout: float,
    urlopen: Callable[..., Any],
) -> PublicIssueOpsRemoteFile:
    api_url = _contents_url(owner, repo, path)
    try:
        payload = _github_request_json(api_url, token=token, timeout=timeout, urlopen=urlopen)
    except PublicGrowthFetchError as exc:
        message = str(exc)
        if "HTTP 404" in message:
            return PublicIssueOpsRemoteFile(
                route=route,
                path=path,
                status="missing",
                api_url=api_url,
                reason="not found on the repository default branch",
            )
        return PublicIssueOpsRemoteFile(
            route=route,
            path=path,
            status="unverified",
            api_url=api_url,
            reason=message,
        )

    if isinstance(payload, dict) and payload.get("type") == "file":
        return PublicIssueOpsRemoteFile(
            route=route,
            path=path,
            status="live",
            api_url=api_url,
            html_url=str(payload.get("html_url") or ""),
            reason="present on the repository default branch",
        )

    return PublicIssueOpsRemoteFile(
        route=route,
        path=path,
        status="missing",
        api_url=api_url,
        reason=f"GitHub contents endpoint returned {type(payload).__name__}, not a file",
    )


def _fetch_issueops_readiness(
    owner: str,
    repo: str,
    *,
    token: str,
    timeout: float,
    urlopen: Callable[..., Any],
) -> PublicIssueOpsReadiness:
    return PublicIssueOpsReadiness(
        growth_form=_fetch_issueops_remote_file(
            owner,
            repo,
            route="Growth Issue Form",
            path=GROWTH_FORM_PATH,
            token=token,
            timeout=timeout,
            urlopen=urlopen,
        ),
        share_form=_fetch_issueops_remote_file(
            owner,
            repo,
            route="Share Proof Issue Form",
            path=SHARE_FORM_PATH,
            token=token,
            timeout=timeout,
            urlopen=urlopen,
        ),
        workflow=_fetch_issueops_remote_file(
            owner,
            repo,
            route="IssueOps Workflow",
            path=ISSUEOPS_WORKFLOW_PATH,
            token=token,
            timeout=timeout,
            urlopen=urlopen,
        ),
    )


def _fetch_release_readiness(
    owner: str,
    repo: str,
    *,
    token: str,
    timeout: float,
    urlopen: Callable[..., Any],
    local_version: str | None = None,
) -> PublicReleaseReadiness:
    installed_version = get_local_package_version(PACKAGE_NAME) if local_version is None else str(local_version or "")
    expected_tag = _expected_release_tag(installed_version)
    api_url = _release_by_tag_url(owner, repo, expected_tag) if expected_tag else ""
    if not expected_tag:
        return PublicReleaseReadiness(
            local_version=installed_version,
            expected_tag=expected_tag,
            status="unverified",
            api_url=api_url,
            reason="local package metadata is missing, so the expected release tag cannot be derived",
        )

    try:
        payload = _github_request_json(api_url, token=token, timeout=timeout, urlopen=urlopen)
    except PublicGrowthFetchError as exc:
        message = str(exc)
        if "HTTP 404" in message:
            return PublicReleaseReadiness(
                local_version=installed_version,
                expected_tag=expected_tag,
                status="missing",
                api_url=api_url,
                reason="not found on the repository releases API",
            )
        return PublicReleaseReadiness(
            local_version=installed_version,
            expected_tag=expected_tag,
            status="unverified",
            api_url=api_url,
            reason=message,
        )

    if not isinstance(payload, dict):
        return PublicReleaseReadiness(
            local_version=installed_version,
            expected_tag=expected_tag,
            status="unverified",
            api_url=api_url,
            reason=f"GitHub release endpoint returned {type(payload).__name__}, not a release object",
        )

    html_url = str(payload.get("html_url") or "")
    actual_tag = str(payload.get("tag_name") or "")
    if actual_tag != expected_tag:
        return PublicReleaseReadiness(
            local_version=installed_version,
            expected_tag=expected_tag,
            status="mismatch",
            api_url=api_url,
            html_url=html_url,
            reason=f"GitHub release tag is {actual_tag or 'missing'}, not {expected_tag}",
        )
    if payload.get("draft"):
        return PublicReleaseReadiness(
            local_version=installed_version,
            expected_tag=expected_tag,
            status="draft",
            api_url=api_url,
            html_url=html_url,
            reason="release exists but is still a draft",
        )
    if payload.get("prerelease"):
        return PublicReleaseReadiness(
            local_version=installed_version,
            expected_tag=expected_tag,
            status="prerelease",
            api_url=api_url,
            html_url=html_url,
            reason="release exists but is marked as a prerelease",
        )
    if not payload.get("published_at"):
        return PublicReleaseReadiness(
            local_version=installed_version,
            expected_tag=expected_tag,
            status="unverified",
            api_url=api_url,
            html_url=html_url,
            reason="release exists but has no published_at timestamp",
        )

    return PublicReleaseReadiness(
        local_version=installed_version,
        expected_tag=expected_tag,
        status="published",
        api_url=api_url,
        html_url=html_url,
        reason="matching published release exists",
    )


def _fetch_distribution_readiness(
    *,
    package_name: str = PACKAGE_NAME,
    local_version: str | None = None,
    timeout: float,
    urlopen: Callable[..., Any],
) -> PublicDistributionReadiness:
    api_url = f"https://pypi.org/pypi/{package_name}/json"
    project_url = f"https://pypi.org/project/{package_name}/"
    installed_version = get_local_package_version(package_name) if local_version is None else str(local_version or "")
    try:
        payload = _pypi_request_json(api_url, timeout=timeout, urlopen=urlopen)
    except PublicGrowthFetchError as exc:
        return PublicDistributionReadiness(
            package_name=package_name,
            local_version=installed_version,
            status="unverified",
            api_url=api_url,
            project_url=project_url,
            reason=str(exc),
        )

    info = payload.get("info") if isinstance(payload, dict) else None
    if not isinstance(info, dict):
        return PublicDistributionReadiness(
            package_name=package_name,
            local_version=installed_version,
            status="unverified",
            api_url=api_url,
            project_url=project_url,
            reason=f"PyPI JSON endpoint returned {type(payload).__name__}, not project info",
        )

    published_version = str(info.get("version") or "")
    project_url = str(info.get("project_url") or project_url)
    if not published_version or not installed_version:
        return PublicDistributionReadiness(
            package_name=package_name,
            local_version=installed_version,
            published_version=published_version,
            status="unverified",
            api_url=api_url,
            project_url=project_url,
            reason="PyPI latest version or local package metadata is missing",
        )
    if published_version == installed_version:
        return PublicDistributionReadiness(
            package_name=package_name,
            local_version=installed_version,
            published_version=published_version,
            status="current",
            api_url=api_url,
            project_url=project_url,
            reason="PyPI latest version matches the local package metadata",
        )
    return PublicDistributionReadiness(
        package_name=package_name,
        local_version=installed_version,
        published_version=published_version,
        status="stale",
        api_url=api_url,
        project_url=project_url,
        reason="PyPI latest version differs from the local package metadata",
    )


def fetch_public_growth_snapshot(
    *,
    repo_owner: str | None = None,
    repo_name: str | None = None,
    token: str | None = None,
    timeout: float = 10.0,
    urlopen: Callable[..., Any] = _urlopen,
    max_pages: int = 10,
) -> PublicGrowthSnapshot:
    """Fetch current public GitHub repo and IssueOps proof metrics."""
    owner = repo_owner or config.GITHUB_REPO_OWNER
    repo = repo_name or config.GITHUB_REPO_NAME
    auth_token = config.GITHUB_TOKEN if token is None else token
    repo_api_url = _repo_url(owner, repo)
    repo_payload = _github_request_json(repo_api_url, token=auth_token, timeout=timeout, urlopen=urlopen)
    if not isinstance(repo_payload, dict):
        raise PublicGrowthFetchError("GitHub repository endpoint returned non-object JSON")

    local_version = get_local_package_version(PACKAGE_NAME)
    return PublicGrowthSnapshot(
        repo=_parse_repo_metrics(repo_payload, repo_api_url),
        growth_issues=_fetch_issue_metrics(
            owner,
            repo,
            GROWTH_LABEL,
            token=auth_token,
            timeout=timeout,
            urlopen=urlopen,
            max_pages=max_pages,
        ),
        share_issues=_fetch_issue_metrics(
            owner,
            repo,
            SHARE_LABEL,
            token=auth_token,
            timeout=timeout,
            urlopen=urlopen,
            max_pages=max_pages,
        ),
        pull_requests=_fetch_pull_request_metrics(
            owner,
            repo,
            token=auth_token,
            timeout=timeout,
            urlopen=urlopen,
            max_pages=max_pages,
        ),
        issueops_readiness=_fetch_issueops_readiness(
            owner,
            repo,
            token=auth_token,
            timeout=timeout,
            urlopen=urlopen,
        ),
        release_readiness=_fetch_release_readiness(
            owner,
            repo,
            token=auth_token,
            timeout=timeout,
            urlopen=urlopen,
            local_version=local_version,
        ),
        distribution_readiness=_fetch_distribution_readiness(
            local_version=local_version,
            timeout=timeout,
            urlopen=urlopen,
        ),
    )


def get_public_growth_snapshot_path() -> Path:
    """Return the local public-growth snapshot ledger path."""
    return Path(config.CAVE_LOGS_DIR) / "public-growth-snapshots.jsonl"


def _count_events(events: Sequence[ActivationEvent], event_type: str) -> int:
    return sum(1 for event in events if event.event_type == event_type)


def _snapshot_entry_from_dict(data: dict[str, Any]) -> PublicGrowthHistoryEntry | None:
    try:
        return PublicGrowthHistoryEntry(
            timestamp=float(data.get("timestamp", 0.0)),
            repo_full_name=str(data.get("repo_full_name") or ""),
            repo_url=str(data.get("repo_url") or ""),
            stargazers=_safe_int(data.get("stargazers")),
            forks=_safe_int(data.get("forks")),
            watchers=_safe_int(data.get("watchers")),
            subscribers=_safe_int(data.get("subscribers")),
            open_issues=_safe_int(data.get("open_issues")),
            growth_issues=_safe_int(data.get("growth_issues")),
            share_issues=_safe_int(data.get("share_issues")),
            pull_requests=_safe_int(data.get("pull_requests")),
            local_referrals=_safe_int(data.get("local_referrals")),
            local_shares=_safe_int(data.get("local_shares")),
        )
    except (TypeError, ValueError):
        return None


def load_public_growth_snapshots(
    *,
    path: str | Path | None = None,
    max_entries: int = 100,
) -> list[PublicGrowthHistoryEntry]:
    """Load persisted public-growth snapshots from JSONL."""
    history_path = Path(path) if path is not None else get_public_growth_snapshot_path()
    if not history_path.exists():
        return []

    entries: list[PublicGrowthHistoryEntry] = []
    for line in history_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict):
            entry = _snapshot_entry_from_dict(data)
            if entry:
                entries.append(entry)
    return entries[-max_entries:]


def record_public_growth_snapshot(
    snapshot: PublicGrowthSnapshot,
    *,
    activation_events: Sequence[ActivationEvent] | None = None,
    path: str | Path | None = None,
    now: float | None = None,
) -> PublicGrowthHistoryEntry:
    """Append one real public-growth snapshot to the local JSONL ledger."""
    events = list(activation_events or [])
    entry = PublicGrowthHistoryEntry(
        timestamp=time.time() if now is None else float(now),
        repo_full_name=snapshot.repo.full_name,
        repo_url=snapshot.repo.html_url,
        stargazers=snapshot.repo.stargazers,
        forks=snapshot.repo.forks,
        watchers=snapshot.repo.watchers,
        subscribers=snapshot.repo.subscribers,
        open_issues=snapshot.repo.open_issues,
        growth_issues=snapshot.growth_issues.total,
        share_issues=snapshot.share_issues.total,
        pull_requests=snapshot.pull_requests.total,
        local_referrals=_count_events(events, EVENT_ISSUEOPS_REFERRAL_RECORDED),
        local_shares=_count_events(events, EVENT_SHARE_ATTRIBUTION_RECORDED),
    )
    history_path = Path(path) if path is not None else get_public_growth_snapshot_path()
    history_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "timestamp": entry.timestamp,
        "repo_full_name": entry.repo_full_name,
        "repo_url": entry.repo_url,
        "stargazers": entry.stargazers,
        "forks": entry.forks,
        "watchers": entry.watchers,
        "subscribers": entry.subscribers,
        "open_issues": entry.open_issues,
        "growth_issues": entry.growth_issues,
        "share_issues": entry.share_issues,
        "pull_requests": entry.pull_requests,
        "local_referrals": entry.local_referrals,
        "local_shares": entry.local_shares,
    }
    with history_path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")
    return entry


def _format_issue_rows(metrics: PublicGrowthIssueMetrics) -> list[str]:
    if not metrics.latest:
        return [f"- `{metrics.label}`: no public issues fetched for this label."]
    return [
        f"- #{issue.number} `{issue.state}` by @{issue.author or 'unknown'}: {issue.title} {issue.url}"
        for issue in metrics.latest
    ]


def _format_pull_request_rows(metrics: PublicPullRequestMetrics) -> list[str]:
    if not metrics.latest:
        return ["- No public pull requests fetched."]
    return [
        f"- #{pull.number} `{pull.state}` by @{pull.author or 'unknown'}: {pull.title} {pull.url}"
        for pull in metrics.latest
    ]


def _readiness_status_label(file: PublicIssueOpsRemoteFile) -> str:
    if file.status == "live":
        return "live"
    if file.status == "missing":
        return "missing"
    if file.status == "unverified":
        return "unverified"
    return "not checked"


def _format_issueops_readiness_lines(readiness: PublicIssueOpsReadiness) -> list[str]:
    lines = [
        "## IssueOps Route Readiness",
        "",
        "> Remote readiness is checked against GitHub repository contents on the default branch.",
        "> Public `issues/new?...` links are only a live acquisition loop after the required Issue Forms and workflow are present remotely.",
        "",
        "| Route | Required remote file | Status | API source |",
        "|---|---|---|---|",
    ]
    for file in readiness.files:
        source = file.html_url or file.api_url or "not checked"
        reason = f" - {file.reason}" if file.reason and file.status != "live" else ""
        lines.append(f"| {file.route} | `{file.path}` | {_readiness_status_label(file)} | {source}{reason} |")

    missing = readiness.missing_files
    unverified = readiness.unverified_files
    if missing:
        missing_paths = ", ".join(f"`{file.path}`" for file in missing)
        lines.extend(
            [
                "",
                "## Public IssueOps Launch Blocker",
                "",
                "- Remote IssueOps route files are missing from the repository default branch.",
                "- Missing remote files: " + missing_paths,
                "- First action: Commit and push the missing `.github` Issue Forms and workflow to the repository default branch.",
                "- Recheck: `public_growth_report()`",
                "- Do not treat `issues/new?...` links as live proof until the required remote files are live.",
            ]
        )
    elif unverified:
        unverified_paths = ", ".join(f"`{file.path}`" for file in unverified)
        lines.extend(
            [
                "",
                "## Public IssueOps Verification Warning",
                "",
                "- Remote IssueOps route readiness could not be fully verified.",
                "- Unverified remote files: " + unverified_paths,
                "- Recheck: `public_growth_report()`",
                "- Do not claim the IssueOps acquisition loop is proven until the remote files are verified live.",
            ]
        )
    else:
        lines.extend(
            [
                "",
                "- All required remote IssueOps route files are live or this report was built from an unchecked local snapshot.",
            ]
        )
    lines.append("")
    return lines


def _format_release_readiness_lines(release: PublicReleaseReadiness) -> list[str]:
    source = release.html_url or release.api_url or "not checked"
    local_version = release.local_version or "unknown"
    expected_tag = release.expected_tag or "unknown"
    reason = f" - {release.reason}" if release.reason and release.status not in {"published"} else ""
    lines = [
        "## GitHub Release Readiness",
        "",
        "> The PyPI trusted-publishing workflow runs when a matching GitHub Release is published.",
        "> This check uses the GitHub Releases API tag endpoint for the current local package version.",
        "",
        "| Local version | Expected release tag | Status | Source |",
        "|---:|---|---|---|",
        f"| `{local_version}` | `{expected_tag}` | {release.status} | {source}{reason} |",
        "",
    ]

    if release.status in {"missing", "draft", "prerelease", "mismatch"}:
        lines.extend(
            [
                "## GitHub Release Launch Blocker",
                "",
                f"- Create and publish GitHub Release `{expected_tag}` after quality gates pass.",
                "- Release workflow: `.github/workflows/publish-pypi.yml`",
                "- Publishing this Release triggers PyPI Trusted Publishing for the current package version.",
                (
                    f"- If release creation is unavailable but tag `{expected_tag}` already exists, use the protected "
                    f"manual workflow dispatch for `.github/workflows/publish-pypi.yml` with tag `{expected_tag}` to "
                    "publish the install loop while release proof remains open."
                ),
                "- The manual workflow checks out the tag, verifies it is reachable from `origin/main`, and verifies `pyproject.toml` version equals the tag.",
                "- Recheck release proof: `public_growth_report()`",
                "- Do not claim the install loop can refresh until the matching published release exists.",
                "",
            ]
        )
    elif release.status == "unverified":
        lines.extend(
            [
                "## GitHub Release Verification Warning",
                "",
                "- GitHub Release readiness could not be verified from the public Releases API.",
                "- Recheck release proof: `public_growth_report()`",
                "- Do not claim the release-triggered install loop is proven until the matching release is verified.",
                "",
            ]
        )
    else:
        lines.extend(["- Matching GitHub Release is published for the local package version.", ""])
    return lines


def _format_distribution_readiness_lines(distribution: PublicDistributionReadiness) -> list[str]:
    source = distribution.project_url or distribution.api_url or "not checked"
    local_version = distribution.local_version or "unknown"
    published_version = distribution.published_version or "unknown"
    reason = f" - {distribution.reason}" if distribution.reason and distribution.status not in {"current"} else ""
    lines = [
        "## PyPI Distribution Readiness",
        "",
        "> The public install loop depends on the version users receive from `pip install tiangong-mcp`.",
        "> This check compares local package metadata with the real PyPI JSON API latest version.",
        "",
        "| Package | Local version | PyPI latest | Status | Source |",
        "|---|---:|---:|---|---|",
        (
            f"| `{distribution.package_name}` | `{local_version}` | `{published_version}` | "
            f"{distribution.status} | {source}{reason} |"
        ),
        "",
    ]

    if distribution.status == "stale":
        lines.extend(
            [
                "## PyPI Release Launch Blocker",
                "",
                (
                    f"- Publish `{distribution.package_name}=={distribution.local_version}` to PyPI before relying on "
                    f"`pip install {distribution.package_name}` for the public campaign."
                ),
                "- Release workflow: `.github/workflows/publish-pypi.yml`",
                "- Build release artifacts: `python -m build`",
                "- Check release artifacts: `python -m twine check dist/*`",
                "- Create a GitHub Release after PyPI Trusted Publishing is configured; the release workflow will publish without storing a PyPI API token.",
                "- If GitHub Release creation is unavailable, manually dispatch `.github/workflows/publish-pypi.yml` with the existing `v*` tag after quality gates pass.",
                "- Recheck distribution proof: `public_growth_report()`",
                "- Do not claim the install loop reaches current growth tools while PyPI is stale.",
                "",
            ]
        )
    elif distribution.status == "unverified":
        lines.extend(
            [
                "## PyPI Distribution Verification Warning",
                "",
                "- PyPI distribution readiness could not be verified from the public JSON API.",
                "- Recheck distribution proof: `public_growth_report()`",
                "- Do not claim the install loop is proven until PyPI latest version is verified.",
                "",
            ]
        )
    else:
        lines.extend(["- PyPI latest version matches the local package metadata.", ""])
    return lines


def _format_pypi_trusted_publisher_runbook_lines(
    snapshot: PublicGrowthSnapshot,
    *,
    target_contributors: int = 10,
) -> list[str]:
    distribution = snapshot.distribution_readiness
    if distribution.status not in {"stale", "unverified"}:
        return []

    owner, repo = _repo_owner_name(snapshot.repo.full_name)
    release_tag = snapshot.release_readiness.expected_tag or f"v{distribution.local_version or 'current-local-version'}"
    target = _safe_positive_int(target_contributors, fallback=10)
    lines = [
        "## PyPI Trusted Publisher Setup Runbook",
        "",
        "> Use this when PyPI Trusted Publishing fails with `invalid-publisher` after lint, tests, build, `twine check`, and `public-release-boundary` passed.",
        "> PyPI's troubleshooting docs define `invalid-publisher` as a valid OIDC token that does not match any configured publisher claims.",
        "> Do not add a stored `PYPI_TOKEN`; keep the install loop on Trusted Publishing/OIDC.",
        "",
        f"- PyPI project publishing settings: {PYPI_PROJECT_PUBLISHING_URL}",
        f"- GitHub workflow run: `.github/workflows/{PYPI_TRUSTED_PUBLISHER_WORKFLOW_FILENAME}`",
        f"- Re-run release workflow after setup: https://github.com/{owner}/{repo}/actions/workflows/{PYPI_TRUSTED_PUBLISHER_WORKFLOW_FILENAME}",
        "",
        "| PyPI Trusted Publisher field | Value to configure | Evidence / failed-run claim |",
        "|---|---|---|",
        f"| Repository owner | `{owner}` | `repository_owner`: `{owner}` |",
        f"| Repository name | `{repo}` | `repository`: `{owner}/{repo}` |",
        (
            f"| Workflow filename | `{PYPI_TRUSTED_PUBLISHER_WORKFLOW_FILENAME}` | "
            f"`workflow_ref`: `{owner}/{repo}/{PYPI_TRUSTED_PUBLISHER_WORKFLOW_PATH}@refs/tags/{release_tag}` |"
        ),
        (
            f"| Workflow path | `{PYPI_TRUSTED_PUBLISHER_WORKFLOW_PATH}` | GitHub Actions workflow file on default branch |"
        ),
        f"| Environment | `{PYPI_TRUSTED_PUBLISHER_ENVIRONMENT}` | `environment`: `{PYPI_TRUSTED_PUBLISHER_ENVIRONMENT}` and `sub`: `repo:{owner}/{repo}:environment:{PYPI_TRUSTED_PUBLISHER_ENVIRONMENT}` |",
        f"| Package | `{distribution.package_name}` | PyPI latest `{distribution.published_version or 'unknown'}` vs local `{distribution.local_version or 'unknown'}` |",
        "",
        "## After PyPI Setup",
        "",
        "- Re-run failed release job, or manually dispatch the workflow with tag "
        f"`{release_tag}` from the Actions page above.",
        f"- Recheck install loop: `public_growth_report(record_snapshot=True, target_contributors={target})`",
        f"- Expected proof: PyPI JSON latest version becomes `{distribution.local_version or 'current-local-version'}`.",
        "",
    ]
    return lines


def _format_public_launch_closure_checklist_lines(
    snapshot: PublicGrowthSnapshot,
    *,
    local_referrals: int,
    local_shares: int,
    target_contributors: int,
) -> list[str]:
    rows: list[tuple[str, str, str]] = []
    issueops_blockers = [file for file in snapshot.issueops_readiness.files if file.status != "live"]
    if issueops_blockers:
        paths = ", ".join(f"`{file.path}`" for file in issueops_blockers)
        rows.append(
            (
                "Remote IssueOps routes",
                (
                    "`tiangong-mcp public-launch-assets` verifies the local route bundle, then commit and push "
                    f"{paths} to the repository default branch."
                ),
                "`public_growth_report()` shows every IssueOps route as live.",
            )
        )

    release_blocked = snapshot.release_readiness.status in {"missing", "draft", "prerelease", "mismatch", "unverified"}
    distribution_blocked = snapshot.distribution_readiness.status in {"stale", "unverified"}
    if release_blocked or distribution_blocked:
        rows.append(
            (
                "PyPI Trusted Publisher",
                (
                    f"Configure PyPI project `{snapshot.distribution_readiness.package_name}` with repository "
                    f"`{snapshot.repo.full_name}`, workflow filename `{PYPI_TRUSTED_PUBLISHER_WORKFLOW_FILENAME}` "
                    f"(path `{PYPI_TRUSTED_PUBLISHER_WORKFLOW_PATH}`), environment `{PYPI_TRUSTED_PUBLISHER_ENVIRONMENT}`."
                ),
                "PyPI Trusted Publishing settings match the release workflow.",
            )
        )

    if release_blocked:
        tag = snapshot.release_readiness.expected_tag or f"v{snapshot.distribution_readiness.local_version}"
        owner, repo = _repo_owner_name(snapshot.repo.full_name)
        release_draft_url = f"https://github.com/{owner}/{repo}/releases/new"
        rows.append(
            (
                "GitHub Release trigger",
                (
                    f"Run `gh release create {tag} --generate-notes` after quality gates pass; if GitHub CLI is "
                    f"unavailable, open {release_draft_url}, Select existing tag `{tag}`, generate notes, and publish "
                    "the Release. If release creation is unavailable, manually dispatch "
                    f"`.github/workflows/publish-pypi.yml` with tag `{tag}` as an install-loop fallback."
                ),
                f"`public_growth_report()` shows GitHub Release `{tag}` as published.",
            )
        )

    if distribution_blocked:
        package = snapshot.distribution_readiness.package_name
        version = snapshot.distribution_readiness.local_version or "current-local-version"
        rows.append(
            (
                "PyPI latest version",
                f"Wait for `.github/workflows/publish-pypi.yml` to publish `{package}=={version}`.",
                f"`public_growth_report()` shows PyPI latest `{version}`.",
            )
        )

    first_public_proof_missing = (
        snapshot.growth_issues.total <= 0
        or snapshot.share_issues.total <= 0
        or local_referrals <= 0
        or local_shares <= 0
    )
    if first_public_proof_missing:
        target = _safe_positive_int(target_contributors)
        proof_report = (
            f"`public_growth_report(record_snapshot=True, target_contributors={target})`"
            if target
            else "`public_growth_report(record_snapshot=True)`"
        )
        rows.append(
            (
                "First public proof",
                (
                    "Open the Growth Issue Form and Share Proof Issue Form, then run "
                    "`record_growth_referral(...)` and `record_share_attribution(...)` with the created public Issue URLs."
                ),
                f"{proof_report} shows real Growth/Share Issues plus local return/share events.",
            )
        )

    if not rows:
        return []

    lines = [
        "## Public Launch Closure Checklist",
        "",
        "> This is the shortest ordered path from local flywheel mechanics to a reviewable public loop.",
        "> Do not mark the flywheel closed until every row is verified from real public state.",
        "",
        "| Order | Gate | Exact next action | Proof to recheck |",
        "|---:|---|---|---|",
    ]
    for index, (gate, action, proof) in enumerate(rows, start=1):
        lines.append(f"| {index} | {gate} | {action} | {proof} |")
    lines.append("")
    return lines


def _gate_status_label(*, ready: bool, blocked: bool = False) -> str:
    if ready:
        return "ready"
    if blocked:
        return "blocked"
    return "unverified"


def format_public_launch_preflight(
    snapshot: PublicGrowthSnapshot | None,
    *,
    activation_events: Sequence[ActivationEvent] | None = None,
    source_path: str | Path | None = None,
    target_contributors: int = 10,
    fetch_error: str = "",
) -> str:
    """Format a direct release runbook for closing the public growth loop."""
    events = list(activation_events or [])
    local_referrals = _count_events(events, EVENT_ISSUEOPS_REFERRAL_RECORDED)
    local_shares = _count_events(events, EVENT_SHARE_ATTRIBUTION_RECORDED)
    path = Path(source_path) if source_path is not None else Path(config.CAVE_LOGS_DIR) / "activation-events.jsonl"
    target = _safe_positive_int(target_contributors, fallback=10)
    preflight_recheck = f"public_launch_preflight(target_contributors={target})"
    proof_recheck = f"public_growth_report(record_snapshot=True, target_contributors={target})"
    proof_pack_recheck = f"public_proof_pack(target_contributors={target})"
    no_fake_line = "This preflight does not invent downloads, retention, repost counts, referral conversions, or rewards."
    no_side_effect_line = "This preflight does not execute git, publish releases, or claim public traction."

    lines = [
        "# TianGong Public Launch Preflight",
        "",
        "> Purpose: close the gap between local cultivation mechanics and a reviewable public growth loop.",
        f"> Local ledger: `{path}`.",
        f"> {no_side_effect_line}",
        f"> {no_fake_line}",
        "",
    ]

    if snapshot is None:
        local_version = get_local_package_version(PACKAGE_NAME)
        release_tag = f"v{local_version or 'current-local-version'}"
        owner = config.GITHUB_REPO_OWNER
        repo = config.GITHUB_REPO_NAME
        release_draft_url = f"https://github.com/{owner}/{repo}/releases/new"
        publish_workflow_url = f"https://github.com/{owner}/{repo}/actions/workflows/{PYPI_TRUSTED_PUBLISHER_WORKFLOW_FILENAME}"
        release_api_url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/releases"
        release_api_payload = (
            f'{{"tag_name":"{release_tag}","name":"{release_tag}",'
            '"draft":false,"prerelease":false,"generate_release_notes":true}'
        )
        lines.extend(
            [
                "## External Fetch Status",
                "",
                "- Public GitHub/PyPI state could not be fetched.",
                f"- Fetch error: {fetch_error or 'missing public snapshot'}",
                "- Do not create a release or claim a closed flywheel until the public preflight can verify current state.",
                "",
                "## Recovery Commands",
                "",
                "- Audit local launch assets: `tiangong-mcp public-launch-assets`",
                f"- Generate no-network first proof pack: `tiangong-mcp public-proof-pack --target-contributors {target}`",
                f"- Generate MCP first proof pack: `{proof_pack_recheck}`",
                (
                    "- For authenticated verification, set `GITHUB_TOKEN` and retry "
                    f"`tiangong-mcp public-launch-preflight --target-contributors {target}`."
                ),
                f"- Open GitHub web release page: {release_draft_url}",
                f"- Select existing tag `{release_tag}`, generate notes, and publish the Release.",
                (
                    f"- If Release creation is unavailable, open Actions manual workflow page: {publish_workflow_url} "
                    f"and run workflow_dispatch tag `{release_tag}`."
                ),
                "",
                "## Optional GitHub REST Release Command",
                "",
                "> Requires a `GITHUB_TOKEN` with permission to create releases. This command is not run by preflight.",
                "",
                "```bash",
                (
                    'curl -L -X POST -H "Accept: application/vnd.github+json" '
                    '-H "Authorization: Bearer $GITHUB_TOKEN" '
                    f'-H "X-GitHub-Api-Version: {GITHUB_API_VERSION}" '
                    f"{release_api_url} "
                    f"-d '{release_api_payload}'"
                ),
                "```",
                "",
                f"- Retry preflight: `{preflight_recheck}`",
                f"- Retry proof report: `{proof_recheck}`",
                "- Run local quality gates before any release attempt:",
                "  - `python -m ruff check .github tiangong tests`",
                "  - `python -m pytest -q`",
                "  - `python -m build`",
                "  - `python -m twine check dist/*`",
                "",
            ]
        )
        return "\n".join(lines)

    issueops_blocked = any(file.status == "missing" for file in snapshot.issueops_readiness.files)
    issueops_ready = all(file.status == "live" for file in snapshot.issueops_readiness.files)
    release_ready = snapshot.release_readiness.status == "published"
    release_blocked = snapshot.release_readiness.status in {"missing", "draft", "prerelease", "mismatch"}
    distribution_ready = snapshot.distribution_readiness.status == "current"
    distribution_blocked = snapshot.distribution_readiness.status == "stale"
    first_proof_ready = (
        snapshot.growth_issues.total > 0
        and snapshot.share_issues.total > 0
        and local_referrals > 0
        and local_shares > 0
    )
    first_proof_blocked = not first_proof_ready
    release_tag = snapshot.release_readiness.expected_tag or f"v{snapshot.distribution_readiness.local_version}"
    owner, repo = _repo_owner_name(snapshot.repo.full_name)
    release_draft_url = f"https://github.com/{owner}/{repo}/releases/new"
    publish_workflow_url = f"https://github.com/{owner}/{repo}/actions/workflows/{PYPI_TRUSTED_PUBLISHER_WORKFLOW_FILENAME}"
    real_data_context = (
        f"Public launch preflight: {snapshot.growth_issues.total} Growth issues, "
        f"{snapshot.share_issues.total} Share Proof issues, {snapshot.pull_requests.total} pull requests, "
        f"{local_referrals} local return events, {local_shares} local share-attribution events."
    )
    growth_issue_url = build_growth_issue_url(
        bottleneck_label="Public Growth IssueOps Issues",
        campaign_hook="Open the first reviewable TianGong public launch proof",
        real_data_context=real_data_context,
        target_contributors=target,
        repo_owner=owner,
        repo_name=repo,
    )
    share_issue_url = build_share_proof_issue_url(
        contribution="forge",
        public_share_url="",
        artifact_name="first-growth-artifact",
        campaign_hook="Bind the first TianGong public launch share proof",
        repo_owner=owner,
        repo_name=repo,
    )
    growth_proof_url = _issue_proof_placeholder(snapshot.repo.full_name, "growth")
    share_proof_url = _issue_proof_placeholder(snapshot.repo.full_name, "share-proof")

    lines.extend(
        [
            "## Current Public Gate Status",
            "",
            "| Gate | Status | Real evidence |",
            "|---|---|---|",
            (
                "| Remote IssueOps routes | "
                f"{_gate_status_label(ready=issueops_ready, blocked=issueops_blocked)} | "
                f"{', '.join(f'{file.route}: {file.status}' for file in snapshot.issueops_readiness.files)} |"
            ),
            (
                "| GitHub Release trigger | "
                f"{_gate_status_label(ready=release_ready, blocked=release_blocked)} | "
                f"{release_tag or 'unknown'} is {snapshot.release_readiness.status} |"
            ),
            (
                "| PyPI install loop | "
                f"{_gate_status_label(ready=distribution_ready, blocked=distribution_blocked)} | "
                f"{snapshot.distribution_readiness.package_name} PyPI latest "
                f"`{snapshot.distribution_readiness.published_version or 'unknown'}` vs local "
                f"`{snapshot.distribution_readiness.local_version or 'unknown'}` |"
            ),
            (
                "| First public proof | "
                f"{_gate_status_label(ready=first_proof_ready, blocked=first_proof_blocked)} | "
                f"{snapshot.growth_issues.total} Growth issues, {snapshot.share_issues.total} Share issues, "
                f"{local_referrals} local returns, {local_shares} local shares |"
            ),
            "",
            "## Local Quality Gates Before Release",
            "",
            "Run these before creating the GitHub Release trigger:",
            "",
            "```bash",
            "tiangong-mcp public-launch-assets",
            "python -m ruff check .github tiangong tests",
            "python -m pytest -q",
            "python -m compileall tiangong tests -q",
            "python -m build",
            "python -m twine check dist/*",
            "```",
            "",
            *format_full_public_growth_release_handoff_lines(
                release_tag=release_tag,
                include_audit_instruction=True,
            ),
            *_format_public_launch_closure_checklist_lines(
                snapshot,
                local_referrals=local_referrals,
                local_shares=local_shares,
                target_contributors=target,
            ),
            *_format_pypi_trusted_publisher_runbook_lines(snapshot, target_contributors=target),
            "## First Public Proof Entrypoints",
            "",
            "> Use the form URLs only to create public Issues. Use created Issue URLs, not `issues/new?...` form URLs, for ledger commands.",
            "",
            f"- Growth Issue Form: {growth_issue_url}",
            f"- Share Proof Issue Form: {share_issue_url}",
            f"- Created Growth Issue placeholder: {growth_proof_url}",
            f"- Created Share Proof Issue placeholder: {share_proof_url}",
            f"- MCP Proof Pack: `{proof_pack_recheck}`",
            "",
            "## After Submission CLI Ledger Commands",
            "",
            "```bash",
            (
                f'tiangong-mcp record-growth-referral --route growth --source-url "{growth_proof_url}" '
                '--actor "your_github_username"'
            ),
            (
                'tiangong-mcp record-share-attribution --contribution forge '
                f'--share-url "{share_proof_url}" --artifact-name "first-growth-artifact" '
                f'--source-url "{growth_proof_url}" --actor "your_github_username"'
            ),
            "```",
            "",
            "## After Submission MCP Ledger Commands",
            "",
            "```text",
            (
                f"record_growth_referral(route=\"growth\", source_url=\"{growth_proof_url}\", "
                "actor=\"your_github_username\")"
            ),
            (
                "record_share_attribution("
                f"contribution=\"forge\", share_url=\"{share_proof_url}\", artifact_name=\"first-growth-artifact\", "
                f"source_url=\"{growth_proof_url}\", actor=\"your_github_username\")"
            ),
            "```",
            "",
            "## Release Trigger",
            "",
            f"- GitHub CLI release command: `gh release create {release_tag} --generate-notes`",
            (
                f"- GitHub web release page: {release_draft_url} - Select existing tag `{release_tag}`, "
                "generate notes, and publish the Release."
            ),
            (
                f"- Actions manual workflow page: {publish_workflow_url} - run workflow_dispatch tag `{release_tag}` "
                "after the tag is on `origin/main` if Release creation is unavailable."
            ),
            "- PyPI publishing should happen through `.github/workflows/publish-pypi.yml` and PyPI Trusted Publishing/OIDC.",
            "- The publish workflow validates the tag, checks that it is reachable from `origin/main`, and verifies `pyproject.toml` version before upload.",
            "- Do not use a stored `PYPI_TOKEN` for this release path.",
            "",
            "## Recheck Commands",
            "",
            f"- Record and recheck public proof: `{proof_recheck}`",
            f"- Generate first public proof pack: `{proof_pack_recheck}`",
            "- Recheck install loop: `public_growth_report()`",
            "- Recheck local activation: `activation_funnel()`",
            f"- Launch next campaign sprint: `growth_campaign(target_contributors={target})`",
            "",
            "## Copy Launch Operator Note",
            "",
            "```text",
            (
                f"TianGong public launch preflight for {snapshot.repo.full_name}: "
                f"IssueOps={_gate_status_label(ready=issueops_ready, blocked=issueops_blocked)}, "
                f"Release={snapshot.release_readiness.status}, "
                f"PyPI={snapshot.distribution_readiness.status}, "
                f"Growth issues={snapshot.growth_issues.total}, Share issues={snapshot.share_issues.total}. "
                "No downloads, retention, repost counts, referral conversions, or rewards are invented."
            ),
            f"Recheck: {proof_recheck}",
            f"Proof pack: {proof_pack_recheck}",
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def _select_external_bottleneck(
    snapshot: PublicGrowthSnapshot,
    *,
    local_referrals: int,
    local_shares: int,
) -> tuple[str, str]:
    if snapshot.growth_issues.total <= 0:
        return (
            "Public Growth IssueOps Issues",
            "`growth_campaign()` -> open the Growth Issue URL -> `record_growth_referral(...)`",
        )
    if snapshot.share_issues.total <= 0:
        return (
            "Public Share Proof Issues",
            "`record_share_attribution(contribution=\"forge\", share_url=\"https://github.com/owner/repo/issues/2\")`",
        )
    if local_referrals <= 0:
        return (
            "Local IssueOps return ledger",
            "`record_growth_referral(route=\"growth\", source_url=\"https://github.com/owner/repo/issues/1\")`",
        )
    if local_shares <= 0:
        return (
            "Local public share attribution ledger",
            "`record_share_attribution(contribution=\"forge\", share_url=\"https://github.com/owner/repo/issues/2\")`",
        )
    return (
        "Repeat public proof volume",
        "`public_growth_report()` -> `growth_campaign()` -> `leaderboard(type=\"share\")`",
    )


def _repo_owner_name(repo_full_name: str) -> tuple[str, str]:
    if "/" in repo_full_name:
        owner, repo = repo_full_name.split("/", 1)
        if owner and repo:
            return owner, repo
    return config.GITHUB_REPO_OWNER, config.GITHUB_REPO_NAME


def _issue_proof_placeholder(repo_full_name: str, token: str) -> str:
    owner, repo = _repo_owner_name(repo_full_name)
    return f"https://github.com/{owner}/{repo}/issues/<opened-{token}-issue-number>"


def _format_first_public_proof_action_lines(
    snapshot: PublicGrowthSnapshot,
    *,
    local_referrals: int,
    local_shares: int,
    target_contributors: int,
) -> list[str]:
    if (
        snapshot.growth_issues.total > 0
        and snapshot.share_issues.total > 0
        and local_referrals > 0
        and local_shares > 0
    ):
        return []

    owner, repo = _repo_owner_name(snapshot.repo.full_name)
    target = _safe_positive_int(target_contributors)
    real_data_context = (
        f"Public proof snapshot: {snapshot.growth_issues.total} Growth issues, "
        f"{snapshot.share_issues.total} Share Proof issues, {snapshot.pull_requests.total} pull requests, "
        f"{local_referrals} local return events, {local_shares} local share-attribution events."
    )
    growth_issue_url = build_growth_issue_url(
        bottleneck_label="Public Growth IssueOps Issues",
        campaign_hook="Open the first reviewable TianGong public growth proof",
        real_data_context=real_data_context,
        target_contributors=target or None,
        repo_owner=owner,
        repo_name=repo,
    )
    share_issue_url = build_share_proof_issue_url(
        contribution="forge",
        public_share_url="",
        artifact_name="first-growth-artifact",
        campaign_hook="Bind the first TianGong public contribution share proof",
        repo_owner=owner,
        repo_name=repo,
    )
    growth_proof_url = _issue_proof_placeholder(snapshot.repo.full_name, "growth")
    share_proof_url = _issue_proof_placeholder(snapshot.repo.full_name, "share-proof")
    cli_growth_command = (
        f'tiangong-mcp record-growth-referral --route growth --source-url "{growth_proof_url}" '
        '--actor "your_github_username"'
    )
    cli_share_command = (
        'tiangong-mcp record-share-attribution --contribution forge '
        f'--share-url "{share_proof_url}" --artifact-name "first-growth-artifact" '
        f'--source-url "{growth_proof_url}" --actor "your_github_username"'
    )
    mcp_growth_command = (
        f'record_growth_referral(route="growth", source_url="{growth_proof_url}", '
        'actor="your_github_username")'
    )
    mcp_share_command = (
        f'record_share_attribution(contribution="forge", share_url="{share_proof_url}", '
        f'artifact_name="first-growth-artifact", source_url="{growth_proof_url}", '
        'actor="your_github_username")'
    )
    proof_pack_command = (
        f"public_proof_pack(target_contributors={target})" if target else "public_proof_pack()"
    )
    missing_files = snapshot.issueops_readiness.missing_files
    missing_paths = ", ".join(f"`{file.path}`" for file in missing_files)
    readiness_steps = []
    copy_readiness_lines = []
    if missing_files:
        readiness_steps.append(
            f"| 0 | Publish remote IssueOps routes first: commit and push {missing_paths} to the repository default branch. |"
        )
        copy_readiness_lines.append(f"Publish IssueOps routes first: commit and push {missing_paths}.")

    return [
        "## First Public Proof Action",
        "",
        "> Use GitHub `issues/new?...` links only to open the forms. Replace placeholder URLs with the created public Issue URLs before running ledger commands.",
        "> No downloads, retention, repost counts, referral conversions, or rewards are invented.",
        "",
        "| Step | Public action |",
        "|---|---|",
        *readiness_steps,
        f"| 1 | Open Growth Issue Form: {growth_issue_url} |",
        f"| 2 | After submission, record the created Growth Issue: `{mcp_growth_command}` |",
        f"| 3 | Open Share Proof Issue Form: {share_issue_url} |",
        f"| 4 | After submission, record the created Share Proof Issue: `{mcp_share_command}` |",
        f"| 5 | Recreate this no-network proof pack: `{proof_pack_command}` |",
        "",
        "## After Submission CLI Ledger Commands",
        "",
        "```bash",
        cli_growth_command,
        cli_share_command,
        "```",
        "",
        "## After Submission MCP Ledger Commands",
        "",
        "```text",
        mcp_growth_command,
        mcp_share_command,
        "```",
        "",
        "## Copy First Public Proof Post",
        "",
        "```text",
        (
            f"TianGong public proof sprint: {snapshot.repo.full_name} is opening the first reviewable growth loop. "
            f"Real snapshot: {snapshot.growth_issues.total} Growth IssueOps issues, "
            f"{snapshot.share_issues.total} Share Proof issues, {snapshot.pull_requests.total} Pull Requests, "
            f"{local_referrals} local return events, {local_shares} local share-attribution events."
        ),
        "No downloads, retention, repost counts, referral conversions, or rewards are invented.",
        *copy_readiness_lines,
        f"Open Growth proof: {growth_issue_url}",
        f"Open Share proof: {share_issue_url}",
        f"CLI Record Growth return: {cli_growth_command}",
        f"CLI Record Share proof: {cli_share_command}",
        f"Record Growth return: {mcp_growth_command}",
        f"Record Share proof: {mcp_share_command}",
        f"Proof pack: {proof_pack_command}",
        "Install: pip install tiangong-mcp",
        "```",
        "",
    ]


def _safe_positive_int(value: int | str | None, fallback: int = 0) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return fallback
    return number if number > 0 else fallback


def _target_actor_set(
    snapshot: PublicGrowthSnapshot,
    events: Sequence[ActivationEvent],
) -> set[str]:
    actors = {actor for actor in snapshot.growth_issues.actors if actor}
    actors.update(actor for actor in snapshot.share_issues.actors if actor)
    actors.update(actor for actor in snapshot.pull_requests.actors if actor)
    actors.update(
        event.actor
        for event in events
        if event.actor and event.event_type in {EVENT_ISSUEOPS_REFERRAL_RECORDED, EVENT_SHARE_ATTRIBUTION_RECORDED}
    )
    return actors


def _format_percent(value: float) -> str:
    return f"{value * 100:.1f}%"


def _format_campaign_target_lines(
    snapshot: PublicGrowthSnapshot,
    *,
    events: Sequence[ActivationEvent],
    target_contributors: int,
) -> list[str]:
    target = _safe_positive_int(target_contributors)
    if target <= 0:
        return []

    actors = sorted(_target_actor_set(snapshot, events), key=str.lower)
    observed = len(actors)
    missing = max(0, target - observed)
    progress = 1.0 if target <= 0 else min(1.0, observed / target)
    actor_line = ", ".join(f"@{actor}" for actor in actors) if actors else "none yet"
    return [
        "## Campaign Target Progress",
        "",
        "> Contributor source: public Growth/Share Issue authors, public Pull Request authors, and local IssueOps-return/share-attribution actors.",
        "> This target progress does not count stars, forks, watchers, subscribers, downloads, reposts, or retention as contributors.",
        "",
        "| Target signal | Real value |",
        "|---|---:|",
        f"| Target contributors | {target} |",
        f"| Real contributors observed | {observed} |",
        f"| Contributors still needed | {missing} |",
        f"| Target progress | {_format_percent(progress)} |",
        "",
        f"- Observed contributors: {actor_line}",
        f"- Reopen campaign card: `growth_campaign(target_contributors={target})`",
        f"- Record next public snapshot: `public_growth_report(record_snapshot=True, target_contributors={target})`",
        "",
    ]


def _format_campaign_recap_lines(
    snapshot: PublicGrowthSnapshot,
    *,
    events: Sequence[ActivationEvent],
    target_contributors: int,
) -> list[str]:
    target = _safe_positive_int(target_contributors)
    if target <= 0:
        return []

    actors = sorted(_target_actor_set(snapshot, events), key=str.lower)
    observed = len(actors)
    missing = max(0, target - observed)
    reached = observed >= target
    result_label = "Target reached" if reached else "Target shortfall"
    next_target = observed + max(1, target // 2) if reached else target
    actor_line = ", ".join(f"@{actor}" for actor in actors) if actors else "none yet"
    return [
        "## Campaign Recap / Next Sprint",
        "",
        f"- Result: {result_label}",
        f"- Real contributors: {observed}/{target}",
        f"- Contributors still needed: {missing}",
        "- Next-target rule: if reached, next target = observed contributors + max(1, previous target // 2); if shortfall, keep the current target and close the gap.",
        "",
        "| Recap signal | Real value |",
        "|---|---:|",
        f"| Current 72h target | {target} |",
        f"| Real contributors observed | {observed} |",
        f"| Shortfall | {missing} |",
        f"| Next 72h target | {next_target} |",
        "",
        "## Copy campaign recap",
        "",
        "```text",
        (
            f"TianGong campaign recap: {result_label}. Real contributors observed: {observed}/{target}. "
            f"Contributors: {actor_line}. Next 72h target: {next_target}."
        ),
        "No downloads, retention, repost counts, referral conversions, rewards, stars, or forks are invented.",
        f"Next campaign: growth_campaign(target_contributors={next_target})",
        f"Record proof: public_growth_report(record_snapshot=True, target_contributors={next_target})",
        "```",
        "",
        f"- Launch next campaign: `growth_campaign(target_contributors={next_target})`",
        f"- Record next campaign proof: `public_growth_report(record_snapshot=True, target_contributors={next_target})`",
        "",
    ]


def _signed_delta(value: int) -> str:
    return f"+{value}" if value >= 0 else str(value)


def _latest_matching_entry(
    history: Sequence[PublicGrowthHistoryEntry],
    repo_full_name: str,
) -> PublicGrowthHistoryEntry | None:
    for entry in reversed(history):
        if not repo_full_name or entry.repo_full_name == repo_full_name:
            return entry
    return history[-1] if history else None


def _format_velocity_lines(
    snapshot: PublicGrowthSnapshot,
    *,
    history: Sequence[PublicGrowthHistoryEntry] | None,
    history_path: Path,
    local_referrals: int,
    local_shares: int,
) -> list[str]:
    previous = _latest_matching_entry(list(history or []), snapshot.repo.full_name)
    lines = [
        "## Public Growth Velocity",
        "",
        f"- Snapshot ledger: `{history_path}`",
    ]
    if previous is None:
        lines.extend(
            [
                "- Previous public snapshot: none recorded yet.",
                "- Record the first real public snapshot: `public_growth_report(record_snapshot=True)`",
                "",
            ]
        )
        return lines

    lines.extend(
        [
            f"- Previous public snapshot: `{previous.repo_full_name}` at `{previous.timestamp}`.",
            "| Velocity signal | Delta since previous snapshot |",
            "|---|---:|",
            f"| Stars delta | {_signed_delta(snapshot.repo.stargazers - previous.stargazers)} |",
            f"| Forks delta | {_signed_delta(snapshot.repo.forks - previous.forks)} |",
            f"| Watchers delta | {_signed_delta(snapshot.repo.watchers - previous.watchers)} |",
            f"| Subscribers delta | {_signed_delta(snapshot.repo.subscribers - previous.subscribers)} |",
            f"| Growth IssueOps delta | {_signed_delta(snapshot.growth_issues.total - previous.growth_issues)} |",
            f"| Share Proof Issue delta | {_signed_delta(snapshot.share_issues.total - previous.share_issues)} |",
            f"| Pull Request delta | {_signed_delta(snapshot.pull_requests.total - previous.pull_requests)} |",
            f"| Local return event delta | {_signed_delta(local_referrals - previous.local_referrals)} |",
            f"| Local share attribution delta | {_signed_delta(local_shares - previous.local_shares)} |",
            "",
            "- Record the next real public snapshot: `public_growth_report(record_snapshot=True)`",
            "",
        ]
    )
    return lines


def format_public_growth_report(
    snapshot: PublicGrowthSnapshot | None,
    *,
    activation_events: Sequence[ActivationEvent] | None = None,
    source_path: str | Path | None = None,
    history: Sequence[PublicGrowthHistoryEntry] | None = None,
    history_path: str | Path | None = None,
    snapshot_recorded: bool = False,
    target_contributors: int = 0,
    fetch_error: str = "",
) -> str:
    """Format a public traction proof report without inventing external growth."""
    events = list(activation_events or [])
    local_referrals = _count_events(events, EVENT_ISSUEOPS_REFERRAL_RECORDED)
    local_shares = _count_events(events, EVENT_SHARE_ATTRIBUTION_RECORDED)
    path = Path(source_path) if source_path is not None else Path(config.CAVE_LOGS_DIR) / "activation-events.jsonl"
    public_history_path = (
        Path(history_path) if history_path is not None else get_public_growth_snapshot_path()
    )
    no_fake_line = "This report does not invent downloads, retention, repost counts, referral conversions, or rewards."

    lines = [
        "# TianGong Public Growth Proof",
        "",
        "> Data source: GitHub REST API public repository and issue endpoints + pull request endpoints + contents endpoints + release endpoints + PyPI JSON API + local MCP activation ledger.",
        f"> Local ledger: `{path}`.",
        f"> Public snapshot ledger: `{public_history_path}`.",
        f"> Snapshot recorded: {'yes' if snapshot_recorded else 'no'}.",
        f"> {no_fake_line}",
        "",
    ]

    if snapshot is None:
        recovery_target = _safe_positive_int(target_contributors, fallback=10)
        preflight_recheck = f"public_launch_preflight(target_contributors={recovery_target})"
        proof_pack_recheck = f"public_proof_pack(target_contributors={recovery_target})"
        proof_recheck = f"public_growth_report(record_snapshot=True, target_contributors={recovery_target})"
        campaign_recheck = f"growth_campaign(target_contributors={recovery_target})"
        lines.extend(
            [
                "## External Fetch Status",
                "",
                "- External GitHub metrics were not fetched.",
                f"- Fetch error: {fetch_error or 'missing public GitHub snapshot'}",
                "- Current proof status: external traction is unproven until the public GitHub API snapshot is available.",
                "",
                "## Recovery Commands",
                "",
                f"- Run launch preflight: `{preflight_recheck}`",
                f"- Generate no-network first proof pack: `tiangong-mcp public-proof-pack --target-contributors {recovery_target}`",
                f"- Generate MCP first proof pack: `{proof_pack_recheck}`",
                f"- Retry public proof: `{proof_recheck}`",
                f"- Launch a 72h campaign: `{campaign_recheck}`",
                "- Inspect local activation: `activation_funnel()`",
                "- Inspect public share proof: `share_attribution_report()`",
                "",
                "```text",
                "TianGong public growth proof is currently blocked on a real GitHub API snapshot. "
                "No downloads, retention, reposts, referrals, or rewards were invented.",
                f"Preflight: {preflight_recheck}",
                f"Proof pack: tiangong-mcp public-proof-pack --target-contributors {recovery_target}",
                f"MCP proof pack: {proof_pack_recheck}",
                f"Retry: {proof_recheck}",
                "```",
                "",
                "## No-Network First Proof Pack",
                "",
                *format_public_proof_pack(target_contributors=recovery_target).splitlines(),
            ]
        )
        return "\n".join(lines)

    bottleneck, next_action = _select_external_bottleneck(
        snapshot,
        local_referrals=local_referrals,
        local_shares=local_shares,
    )

    lines.extend(
        [
            "## Public Repository Signals",
            "",
            f"- Repository: [{snapshot.repo.full_name}]({snapshot.repo.html_url})",
            f"- GitHub API: {snapshot.repo.api_url}",
            "",
            "| Signal | Real value |",
            "|---|---:|",
            f"| Stars | {snapshot.repo.stargazers} |",
            f"| Forks | {snapshot.repo.forks} |",
            f"| Watchers | {snapshot.repo.watchers} |",
            f"| Subscribers | {snapshot.repo.subscribers} |",
            f"| Open GitHub issues | {snapshot.repo.open_issues} |",
            f"| Public Growth IssueOps issues | {snapshot.growth_issues.total} |",
            f"| Public Share Proof issues | {snapshot.share_issues.total} |",
            f"| Public Pull Requests | {snapshot.pull_requests.total} |",
            f"| Local IssueOps return events | {local_referrals} |",
            f"| Local public share attribution events | {local_shares} |",
            "",
            *_format_issueops_readiness_lines(snapshot.issueops_readiness),
            *_format_release_readiness_lines(snapshot.release_readiness),
            *_format_distribution_readiness_lines(snapshot.distribution_readiness),
            *_format_pypi_trusted_publisher_runbook_lines(snapshot, target_contributors=target_contributors),
            *_format_public_launch_closure_checklist_lines(
                snapshot,
                local_referrals=local_referrals,
                local_shares=local_shares,
                target_contributors=target_contributors,
            ),
            *_format_campaign_target_lines(
                snapshot,
                events=events,
                target_contributors=target_contributors,
            ),
            *_format_campaign_recap_lines(
                snapshot,
                events=events,
                target_contributors=target_contributors,
            ),
            *_format_velocity_lines(
                snapshot,
                history=history,
                history_path=public_history_path,
                local_referrals=local_referrals,
                local_shares=local_shares,
            ),
            "## Public IssueOps Proof",
            "",
            "| Route | Label | Total | Open | Closed | API source |",
            "|---|---|---:|---:|---:|---|",
            (
                f"| Growth | `{snapshot.growth_issues.label}` | {snapshot.growth_issues.total} | "
                f"{snapshot.growth_issues.open} | {snapshot.growth_issues.closed} | {snapshot.growth_issues.api_url} |"
            ),
            (
                f"| Share Proof | `{snapshot.share_issues.label}` | {snapshot.share_issues.total} | "
                f"{snapshot.share_issues.open} | {snapshot.share_issues.closed} | {snapshot.share_issues.api_url} |"
            ),
            (
                f"| Pull Requests | `public:pulls` | {snapshot.pull_requests.total} | "
                f"{snapshot.pull_requests.open} | {snapshot.pull_requests.closed} | {snapshot.pull_requests.api_url} |"
            ),
            "",
            "## Latest Public Proof URLs",
            "",
            "### Growth Issues",
            *_format_issue_rows(snapshot.growth_issues),
            "",
            "### Share Proof Issues",
            *_format_issue_rows(snapshot.share_issues),
            "",
            "### Pull Requests",
            *_format_pull_request_rows(snapshot.pull_requests),
            "",
            "## Current External Proof Bottleneck",
            "",
            f"- Weakest external proof: {bottleneck}",
            f"- First executable action: {next_action}",
            "",
            *_format_first_public_proof_action_lines(
                snapshot,
                local_referrals=local_referrals,
                local_shares=local_shares,
                target_contributors=target_contributors,
            ),
            "## Recovery / Amplification Commands",
            "",
            "- Run launch preflight: `public_launch_preflight()`",
            "- Retry this public proof: `public_growth_report()`",
            "- Generate first public proof pack: `public_proof_pack()`",
            "- Recheck local activation: `activation_funnel()`",
            "- Recheck product flywheel: `growth_flywheel()`",
            "- Launch the next 72h campaign: `growth_campaign()`",
            "- Inspect contribution-share proof: `share_attribution_report()`",
            "- Refresh share leaderboard: `leaderboard(type=\"share\")`",
            "",
            "## Copy Public Proof Recap",
            "",
            "```text",
            (
                f"TianGong public growth proof: {snapshot.repo.stargazers} stars, {snapshot.repo.forks} forks, "
                f"{snapshot.growth_issues.total} Growth IssueOps issues, "
                f"{snapshot.share_issues.total} Share Proof issues, {local_referrals} local return events, "
                f"{local_shares} local share-attribution events. Weakest proof: {bottleneck}."
            ),
            "No downloads, retention, repost counts, referral conversions, or rewards are invented.",
            "Preflight: public_launch_preflight()",
            "Retry: public_growth_report()",
            "Proof pack: public_proof_pack()",
            "Launch: growth_campaign()",
            "```",
        ]
    )
    return "\n".join(lines)
