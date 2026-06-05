"""Public GitHub traction proof tests for TianGong's growth loop."""

from __future__ import annotations

import json

import pytest


class _FakeResponse:
    def __init__(self, payload, headers=None):
        self._payload = payload
        self.headers = headers or {}

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        return json.dumps(self._payload).encode("utf-8")


def test_fetch_public_growth_snapshot_uses_github_public_endpoints_and_excludes_prs():
    """GitHub public metrics should come from repo/issues endpoints and not count PRs as Issues."""
    from tiangong.public_growth import fetch_public_growth_snapshot

    calls = []
    responses = {
        "https://api.github.com/repos/octo-org/octo-repo": {
            "full_name": "octo-org/octo-repo",
            "html_url": "https://github.com/octo-org/octo-repo",
            "stargazers_count": 7,
            "forks_count": 2,
            "watchers_count": 7,
            "subscribers_count": 3,
            "open_issues_count": 5,
            "pushed_at": "2026-06-01T00:00:00Z",
            "updated_at": "2026-06-02T00:00:00Z",
        },
        (
            "https://api.github.com/repos/octo-org/octo-repo/issues?"
            "state=all&labels=tiangong%3Agrowth&per_page=100&page=1"
        ): [
            {
                "number": 11,
                "state": "open",
                "title": "Launch public growth route",
                "html_url": "https://github.com/octo-org/octo-repo/issues/11",
                "user": {"login": "newbie"},
                "labels": [{"name": "tiangong:growth"}],
            },
            {
                "number": 12,
                "state": "closed",
                "title": "PR should not count",
                "html_url": "https://github.com/octo-org/octo-repo/pull/12",
                "pull_request": {"html_url": "https://github.com/octo-org/octo-repo/pull/12"},
                "labels": [{"name": "tiangong:growth"}],
            },
        ],
        (
            "https://api.github.com/repos/octo-org/octo-repo/issues?"
            "state=all&labels=tiangong%3Ashare&per_page=100&page=1"
        ): [
            {
                "number": 13,
                "state": "closed",
                "title": "Bind share proof",
                "html_url": "https://github.com/octo-org/octo-repo/issues/13",
                "user": {"login": "sharer"},
                "labels": [{"name": "tiangong:share"}],
                }
            ],
        (
            "https://api.github.com/repos/octo-org/octo-repo/pulls?"
            "state=all&per_page=100&page=1"
        ): [
            {
                "number": 14,
                "state": "open",
                "title": "Add public forge proof",
                "html_url": "https://github.com/octo-org/octo-repo/pull/14",
                "user": {"login": "pr-author"},
            },
            {
                "number": 15,
                "state": "closed",
                "title": "Improve growth docs",
                "html_url": "https://github.com/octo-org/octo-repo/pull/15",
                "user": {"login": "mentor"},
            },
        ],
        "https://api.github.com/repos/octo-org/octo-repo/contents/.github/ISSUE_TEMPLATE/tiangong-growth-flywheel.yml": {
            "type": "file",
            "path": ".github/ISSUE_TEMPLATE/tiangong-growth-flywheel.yml",
            "html_url": "https://github.com/octo-org/octo-repo/blob/main/.github/ISSUE_TEMPLATE/tiangong-growth-flywheel.yml",
        },
        "https://api.github.com/repos/octo-org/octo-repo/contents/.github/ISSUE_TEMPLATE/tiangong-share-proof.yml": {
            "type": "file",
            "path": ".github/ISSUE_TEMPLATE/tiangong-share-proof.yml",
            "html_url": "https://github.com/octo-org/octo-repo/blob/main/.github/ISSUE_TEMPLATE/tiangong-share-proof.yml",
        },
        "https://api.github.com/repos/octo-org/octo-repo/contents/.github/workflows/issueops-onboarding.yml": {
            "type": "file",
            "path": ".github/workflows/issueops-onboarding.yml",
            "html_url": "https://github.com/octo-org/octo-repo/blob/main/.github/workflows/issueops-onboarding.yml",
        },
        "https://api.github.com/repos/octo-org/octo-repo/releases/tags/v0.1.4": {
            "tag_name": "v0.1.4",
            "name": "TianGong 0.1.4",
            "html_url": "https://github.com/octo-org/octo-repo/releases/tag/v0.1.4",
            "draft": False,
            "prerelease": False,
            "published_at": "2026-06-03T00:00:00Z",
        },
        "https://pypi.org/pypi/tiangong-mcp/json": {
            "info": {
                "name": "tiangong-mcp",
                "version": "0.1.4",
                "project_url": "https://pypi.org/project/tiangong-mcp/",
            }
        },
        }

    def fake_urlopen(request, timeout=0):
        calls.append((request.full_url, request.get_header("Accept"), request.get_header("X-github-api-version")))
        return _FakeResponse(responses[request.full_url])

    snapshot = fetch_public_growth_snapshot(
        repo_owner="octo-org",
        repo_name="octo-repo",
        urlopen=fake_urlopen,
    )

    assert snapshot.repo.full_name == "octo-org/octo-repo"
    assert snapshot.repo.stargazers == 7
    assert snapshot.repo.forks == 2
    assert snapshot.repo.watchers == 7
    assert snapshot.repo.subscribers == 3
    assert snapshot.growth_issues.total == 1
    assert snapshot.growth_issues.open == 1
    assert snapshot.growth_issues.closed == 0
    assert snapshot.growth_issues.latest[0].title == "Launch public growth route"
    assert snapshot.share_issues.total == 1
    assert snapshot.share_issues.closed == 1
    assert snapshot.growth_issues.actors == ("newbie",)
    assert snapshot.share_issues.actors == ("sharer",)
    assert snapshot.pull_requests.total == 2
    assert snapshot.pull_requests.open == 1
    assert snapshot.pull_requests.closed == 1
    assert snapshot.pull_requests.actors == ("mentor", "pr-author")
    assert snapshot.issueops_readiness.growth_form.status == "live"
    assert snapshot.issueops_readiness.share_form.status == "live"
    assert snapshot.issueops_readiness.workflow.status == "live"
    assert snapshot.release_readiness.local_version == "0.1.4"
    assert snapshot.release_readiness.expected_tag == "v0.1.4"
    assert snapshot.release_readiness.status == "published"
    assert snapshot.release_readiness.html_url == "https://github.com/octo-org/octo-repo/releases/tag/v0.1.4"
    assert snapshot.distribution_readiness.package_name == "tiangong-mcp"
    assert snapshot.distribution_readiness.local_version == "0.1.4"
    assert snapshot.distribution_readiness.published_version == "0.1.4"
    assert snapshot.distribution_readiness.status == "current"
    assert calls[0][0] == "https://api.github.com/repos/octo-org/octo-repo"
    assert any("labels=tiangong%3Agrowth" in call[0] for call in calls)
    assert any("labels=tiangong%3Ashare" in call[0] for call in calls)
    assert any("/pulls?state=all" in call[0] for call in calls)
    assert any("/contents/.github/ISSUE_TEMPLATE/tiangong-growth-flywheel.yml" in call[0] for call in calls)
    assert any("/contents/.github/ISSUE_TEMPLATE/tiangong-share-proof.yml" in call[0] for call in calls)
    assert any("/contents/.github/workflows/issueops-onboarding.yml" in call[0] for call in calls)
    assert any(call[0] == "https://api.github.com/repos/octo-org/octo-repo/releases/tags/v0.1.4" for call in calls)
    assert any(call[0] == "https://pypi.org/pypi/tiangong-mcp/json" for call in calls)
    github_calls = [call for call in calls if call[0].startswith("https://api.github.com/")]
    assert all(call[1] == "application/vnd.github+json" for call in github_calls)
    assert all(call[2] == "2026-03-10" for call in github_calls)


def test_public_growth_report_combines_github_metrics_and_local_ledger_without_fake_traction(tmp_path):
    """The report should prove external traction with real sources and expose the weakest bridge."""
    from tiangong.activation import (
        EVENT_ISSUEOPS_REFERRAL_RECORDED,
        load_activation_events,
        record_activation_event,
    )
    from tiangong.public_growth import (
        PublicGrowthIssueMetrics,
        PublicGrowthSnapshot,
        PublicIssueRecord,
        PublicRepoMetrics,
        format_public_growth_report,
    )

    event_path = tmp_path / "activation-events.jsonl"
    record_activation_event(
        EVENT_ISSUEOPS_REFERRAL_RECORDED,
        actor="newbie",
        metadata={"source_url": "https://github.com/octo-org/octo-repo/issues/11"},
        path=event_path,
    )
    snapshot = PublicGrowthSnapshot(
        repo=PublicRepoMetrics(
            full_name="octo-org/octo-repo",
            html_url="https://github.com/octo-org/octo-repo",
            stargazers=7,
            forks=2,
            watchers=7,
            subscribers=3,
            open_issues=5,
            pushed_at="2026-06-01T00:00:00Z",
            updated_at="2026-06-02T00:00:00Z",
            api_url="https://api.github.com/repos/octo-org/octo-repo",
        ),
        growth_issues=PublicGrowthIssueMetrics(
            label="tiangong:growth",
            total=2,
            open=1,
            closed=1,
            latest=[
                PublicIssueRecord(
                    number=11,
                    title="Launch public growth route",
                    state="open",
                    url="https://github.com/octo-org/octo-repo/issues/11",
                    author="newbie",
                )
            ],
            api_url="https://api.github.com/repos/octo-org/octo-repo/issues?labels=tiangong%3Agrowth",
        ),
        share_issues=PublicGrowthIssueMetrics(
            label="tiangong:share",
            total=0,
            open=0,
            closed=0,
            latest=[],
            api_url="https://api.github.com/repos/octo-org/octo-repo/issues?labels=tiangong%3Ashare",
        ),
    )

    result = format_public_growth_report(
        snapshot,
        activation_events=load_activation_events(path=event_path),
        source_path=event_path,
    )

    assert "# TianGong Public Growth Proof" in result
    assert "GitHub REST API public repository and issue endpoints" in result
    assert "| Stars | 7 |" in result
    assert "| Forks | 2 |" in result
    assert "| Public Growth IssueOps issues | 2 |" in result
    assert "| Public Share Proof issues | 0 |" in result
    assert "| Local IssueOps return events | 1 |" in result
    assert "| Local public share attribution events | 0 |" in result
    assert "Weakest external proof: Public Share Proof Issues" in result
    assert "https://github.com/octo-org/octo-repo/issues/11" in result
    assert "record_share_attribution(" in result
    assert "`public_growth_report()`" in result
    assert "`public_launch_preflight()`" in result
    assert "`public_proof_pack()`" in result
    assert "`growth_campaign()`" in result
    assert "does not invent downloads, retention, repost counts, referral conversions, or rewards" in result


def test_public_growth_report_prints_not_closed_flywheel_verdict(tmp_path):
    """A report with stale distribution or unmet campaign target must not claim a closed flywheel."""
    from tiangong.activation import (
        EVENT_ISSUEOPS_REFERRAL_RECORDED,
        EVENT_SHARE_ATTRIBUTION_RECORDED,
        load_activation_events,
        record_activation_event,
    )
    from tiangong.public_growth import (
        PublicDistributionReadiness,
        PublicGrowthIssueMetrics,
        PublicGrowthSnapshot,
        PublicIssueOpsReadiness,
        PublicIssueOpsRemoteFile,
        PublicReleaseReadiness,
        PublicRepoMetrics,
        format_public_growth_report,
    )

    event_path = tmp_path / "activation-events.jsonl"
    record_activation_event(
        EVENT_ISSUEOPS_REFERRAL_RECORDED,
        actor="JinNing6",
        metadata={"source_url": "https://github.com/octo-org/octo-repo/issues/1"},
        path=event_path,
    )
    record_activation_event(
        EVENT_SHARE_ATTRIBUTION_RECORDED,
        actor="JinNing6",
        metadata={"share_url": "https://github.com/octo-org/octo-repo/issues/2"},
        path=event_path,
    )
    snapshot = PublicGrowthSnapshot(
        repo=PublicRepoMetrics(
            full_name="octo-org/octo-repo",
            html_url="https://github.com/octo-org/octo-repo",
            stargazers=4,
            forks=1,
            watchers=4,
            subscribers=0,
            open_issues=2,
            pushed_at="2026-06-01T00:00:00Z",
            updated_at="2026-06-02T00:00:00Z",
            api_url="https://api.github.com/repos/octo-org/octo-repo",
        ),
        growth_issues=PublicGrowthIssueMetrics(
            "tiangong:growth",
            1,
            1,
            0,
            actors=("JinNing6",),
        ),
        share_issues=PublicGrowthIssueMetrics(
            "tiangong:share",
            1,
            1,
            0,
            actors=("JinNing6",),
        ),
        issueops_readiness=PublicIssueOpsReadiness(
            growth_form=PublicIssueOpsRemoteFile("Growth Issue Form", ".github/ISSUE_TEMPLATE/tiangong-growth-flywheel.yml", "live"),
            share_form=PublicIssueOpsRemoteFile("Share Proof Issue Form", ".github/ISSUE_TEMPLATE/tiangong-share-proof.yml", "live"),
            workflow=PublicIssueOpsRemoteFile("IssueOps Workflow", ".github/workflows/issueops-onboarding.yml", "live"),
        ),
        release_readiness=PublicReleaseReadiness(
            local_version="0.1.4",
            expected_tag="v0.1.4",
            status="missing",
        ),
        distribution_readiness=PublicDistributionReadiness(
            package_name="tiangong-mcp",
            local_version="0.1.4",
            published_version="0.0.1",
            status="stale",
        ),
    )

    result = format_public_growth_report(
        snapshot,
        activation_events=load_activation_events(path=event_path),
        source_path=event_path,
        target_contributors=25,
    )

    assert "## Public Flywheel Closure Verdict" in result
    assert "Verdict: not closed" in result
    assert "| Remote IssueOps routes | ready | all required IssueOps routes are live" in result
    assert "| GitHub Release trigger | blocked | `v0.1.4` is missing" in result
    assert "| PyPI install loop | blocked | PyPI latest `0.0.1` vs local `0.1.4`" in result
    assert "| First public proof | ready | 1 Growth issues, 1 Share issues, 1 local returns, 1 local shares" in result
    assert "| Campaign contributor target | blocked | 1/25 real contributors observed; shortfall 24" in result
    assert "Do not claim a closed public flywheel until every closure gate is ready." in result
    assert "Next decisive action:" in result
    assert "public_growth_report(record_snapshot=True, target_contributors=25)" in result


def test_public_growth_report_prints_closed_flywheel_verdict_only_when_all_gates_ready(tmp_path):
    """A closed verdict requires live routes, published release, current PyPI, first proof, and target reach."""
    from tiangong.activation import (
        EVENT_ISSUEOPS_REFERRAL_RECORDED,
        EVENT_SHARE_ATTRIBUTION_RECORDED,
        load_activation_events,
        record_activation_event,
    )
    from tiangong.public_growth import (
        PublicDistributionReadiness,
        PublicGrowthIssueMetrics,
        PublicGrowthSnapshot,
        PublicIssueOpsReadiness,
        PublicIssueOpsRemoteFile,
        PublicPullRequestMetrics,
        PublicReleaseReadiness,
        PublicRepoMetrics,
        format_public_growth_report,
    )

    event_path = tmp_path / "activation-events.jsonl"
    record_activation_event(
        EVENT_ISSUEOPS_REFERRAL_RECORDED,
        actor="newbie",
        metadata={"source_url": "https://github.com/octo-org/octo-repo/issues/11"},
        path=event_path,
    )
    record_activation_event(
        EVENT_SHARE_ATTRIBUTION_RECORDED,
        actor="sharer",
        metadata={"share_url": "https://github.com/octo-org/octo-repo/issues/13"},
        path=event_path,
    )
    snapshot = PublicGrowthSnapshot(
        repo=PublicRepoMetrics(
            full_name="octo-org/octo-repo",
            html_url="https://github.com/octo-org/octo-repo",
            stargazers=20,
            forks=5,
            watchers=20,
            subscribers=6,
            open_issues=7,
            pushed_at="2026-06-03T00:00:00Z",
            updated_at="2026-06-03T01:00:00Z",
            api_url="https://api.github.com/repos/octo-org/octo-repo",
        ),
        growth_issues=PublicGrowthIssueMetrics(
            "tiangong:growth",
            2,
            1,
            1,
            actors=("newbie", "mentor"),
        ),
        share_issues=PublicGrowthIssueMetrics(
            "tiangong:share",
            1,
            1,
            0,
            actors=("sharer",),
        ),
        pull_requests=PublicPullRequestMetrics(total=1, open=1, closed=0, actors=("pr-author",)),
        issueops_readiness=PublicIssueOpsReadiness(
            growth_form=PublicIssueOpsRemoteFile("Growth Issue Form", ".github/ISSUE_TEMPLATE/tiangong-growth-flywheel.yml", "live"),
            share_form=PublicIssueOpsRemoteFile("Share Proof Issue Form", ".github/ISSUE_TEMPLATE/tiangong-share-proof.yml", "live"),
            workflow=PublicIssueOpsRemoteFile("IssueOps Workflow", ".github/workflows/issueops-onboarding.yml", "live"),
        ),
        release_readiness=PublicReleaseReadiness(
            local_version="0.1.4",
            expected_tag="v0.1.4",
            status="published",
        ),
        distribution_readiness=PublicDistributionReadiness(
            package_name="tiangong-mcp",
            local_version="0.1.4",
            published_version="0.1.4",
            status="current",
        ),
    )

    result = format_public_growth_report(
        snapshot,
        activation_events=load_activation_events(path=event_path),
        source_path=event_path,
        target_contributors=4,
    )

    assert "## Public Flywheel Closure Verdict" in result
    assert "Verdict: closed" in result
    assert "| Remote IssueOps routes | ready |" in result
    assert "| GitHub Release trigger | ready |" in result
    assert "| PyPI install loop | ready |" in result
    assert "| First public proof | ready |" in result
    assert "| Campaign contributor target | ready | 4/4 real contributors observed; shortfall 0" in result
    assert "Next decisive action: keep recording real public snapshots and raise the next contributor target." in result


def test_public_growth_report_gives_first_public_proof_action_for_cold_start(tmp_path):
    """A zero-proof public report should directly launch the first reviewable IssueOps proof path."""
    from tiangong.public_growth import (
        PublicGrowthIssueMetrics,
        PublicGrowthSnapshot,
        PublicRepoMetrics,
        format_public_growth_report,
    )

    event_path = tmp_path / "activation-events.jsonl"
    snapshot = PublicGrowthSnapshot(
        repo=PublicRepoMetrics(
            full_name="octo-org/octo-repo",
            html_url="https://github.com/octo-org/octo-repo",
            stargazers=0,
            forks=0,
            watchers=0,
            subscribers=0,
            open_issues=0,
            pushed_at="2026-06-01T00:00:00Z",
            updated_at="2026-06-02T00:00:00Z",
            api_url="https://api.github.com/repos/octo-org/octo-repo",
        ),
        growth_issues=PublicGrowthIssueMetrics(
            label="tiangong:growth",
            total=0,
            open=0,
            closed=0,
            api_url="https://api.github.com/repos/octo-org/octo-repo/issues?labels=tiangong%3Agrowth",
        ),
        share_issues=PublicGrowthIssueMetrics(
            label="tiangong:share",
            total=0,
            open=0,
            closed=0,
            api_url="https://api.github.com/repos/octo-org/octo-repo/issues?labels=tiangong%3Ashare",
        ),
    )

    result = format_public_growth_report(
        snapshot,
        activation_events=[],
        source_path=event_path,
        target_contributors=10,
    )

    assert "## First Public Proof Action" in result
    assert "template=tiangong-growth-flywheel.yml" in result
    assert "target_contributors=10" in result
    assert "template=tiangong-share-proof.yml" in result
    assert "https://github.com/octo-org/octo-repo/issues/<opened-growth-issue-number>" in result
    assert "https://github.com/octo-org/octo-repo/issues/<opened-share-proof-issue-number>" in result
    assert "## After Submission CLI Ledger Commands" in result
    assert (
        'tiangong-mcp record-growth-referral --route growth --source-url "https://github.com/octo-org/octo-repo/issues/<opened-growth-issue-number>"'
        in result
    )
    assert (
        'tiangong-mcp record-share-attribution --contribution forge --share-url "https://github.com/octo-org/octo-repo/issues/<opened-share-proof-issue-number>"'
        in result
    )
    assert "## After Submission MCP Ledger Commands" in result
    assert (
        'record_growth_referral(route="growth", source_url="https://github.com/octo-org/octo-repo/issues/<opened-growth-issue-number>"'
        in result
    )
    assert (
        'record_share_attribution(contribution="forge", share_url="https://github.com/octo-org/octo-repo/issues/<opened-share-proof-issue-number>"'
        in result
    )
    assert "Replace placeholder URLs with the created public Issue URLs before running ledger commands." in result
    assert "## Copy First Public Proof Post" in result
    assert "`public_proof_pack(target_contributors=10)`" in result
    assert "TianGong public proof sprint" in result
    assert "0 Growth IssueOps issues, 0 Share Proof issues, 0 Pull Requests" in result
    assert "Open Growth proof:" in result
    assert "Open Share proof:" in result
    assert "Record Growth return:" in result
    assert "Record Share proof:" in result
    assert "No downloads, retention, repost counts, referral conversions, or rewards are invented." in result


def test_public_growth_report_flags_missing_remote_issueops_routes(tmp_path):
    """A public proof report should not treat local-only IssueOps files as a live acquisition loop."""
    from tiangong.public_growth import (
        PublicGrowthIssueMetrics,
        PublicGrowthSnapshot,
        PublicIssueOpsReadiness,
        PublicIssueOpsRemoteFile,
        PublicRepoMetrics,
        format_public_growth_report,
    )

    event_path = tmp_path / "activation-events.jsonl"
    snapshot = PublicGrowthSnapshot(
        repo=PublicRepoMetrics(
            full_name="octo-org/octo-repo",
            html_url="https://github.com/octo-org/octo-repo",
            stargazers=0,
            forks=0,
            watchers=0,
            subscribers=0,
            open_issues=0,
            pushed_at="2026-06-01T00:00:00Z",
            updated_at="2026-06-02T00:00:00Z",
            api_url="https://api.github.com/repos/octo-org/octo-repo",
        ),
        growth_issues=PublicGrowthIssueMetrics(
            label="tiangong:growth",
            total=0,
            open=0,
            closed=0,
            api_url="https://api.github.com/repos/octo-org/octo-repo/issues?labels=tiangong%3Agrowth",
        ),
        share_issues=PublicGrowthIssueMetrics(
            label="tiangong:share",
            total=0,
            open=0,
            closed=0,
            api_url="https://api.github.com/repos/octo-org/octo-repo/issues?labels=tiangong%3Ashare",
        ),
        issueops_readiness=PublicIssueOpsReadiness(
            growth_form=PublicIssueOpsRemoteFile(
                route="Growth Issue Form",
                path=".github/ISSUE_TEMPLATE/tiangong-growth-flywheel.yml",
                status="missing",
                api_url=(
                    "https://api.github.com/repos/octo-org/octo-repo/contents/"
                    ".github/ISSUE_TEMPLATE/tiangong-growth-flywheel.yml"
                ),
                reason="not found on the repository default branch",
            ),
            share_form=PublicIssueOpsRemoteFile(
                route="Share Proof Issue Form",
                path=".github/ISSUE_TEMPLATE/tiangong-share-proof.yml",
                status="missing",
                api_url=(
                    "https://api.github.com/repos/octo-org/octo-repo/contents/"
                    ".github/ISSUE_TEMPLATE/tiangong-share-proof.yml"
                ),
                reason="not found on the repository default branch",
            ),
            workflow=PublicIssueOpsRemoteFile(
                route="IssueOps Workflow",
                path=".github/workflows/issueops-onboarding.yml",
                status="missing",
                api_url=(
                    "https://api.github.com/repos/octo-org/octo-repo/contents/"
                    ".github/workflows/issueops-onboarding.yml"
                ),
                reason="not found on the repository default branch",
            ),
        ),
    )

    result = format_public_growth_report(snapshot, activation_events=[], source_path=event_path)

    assert "## IssueOps Route Readiness" in result
    assert "| Growth Issue Form | `.github/ISSUE_TEMPLATE/tiangong-growth-flywheel.yml` | missing |" in result
    assert "| Share Proof Issue Form | `.github/ISSUE_TEMPLATE/tiangong-share-proof.yml` | missing |" in result
    assert "| IssueOps Workflow | `.github/workflows/issueops-onboarding.yml` | missing |" in result
    assert "## Public IssueOps Launch Blocker" in result
    assert "Commit and push the missing `.github` Issue Forms and workflow to the repository default branch." in result
    assert "Do not treat `issues/new?...` links as live proof until the required remote files are live." in result
    assert "Publish remote IssueOps routes first" in result
    assert "commit and push `.github/ISSUE_TEMPLATE/tiangong-growth-flywheel.yml`" in result
    assert "public_growth_report()" in result
    assert "public_proof_pack()" in result


def test_public_growth_report_flags_stale_pypi_distribution(tmp_path):
    """The public proof report should show when pip installs cannot reach current growth tools."""
    from tiangong.public_growth import (
        PublicDistributionReadiness,
        PublicGrowthIssueMetrics,
        PublicGrowthSnapshot,
        PublicRepoMetrics,
        format_public_growth_report,
    )

    event_path = tmp_path / "activation-events.jsonl"
    snapshot = PublicGrowthSnapshot(
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
        distribution_readiness=PublicDistributionReadiness(
            package_name="tiangong-mcp",
            local_version="0.1.0",
            published_version="0.0.1",
            status="stale",
            api_url="https://pypi.org/pypi/tiangong-mcp/json",
            project_url="https://pypi.org/project/tiangong-mcp/",
            reason="PyPI latest version differs from the local package metadata",
        ),
    )

    result = format_public_growth_report(snapshot, activation_events=[], source_path=event_path)

    assert "## PyPI Distribution Readiness" in result
    assert "| Package | Local version | PyPI latest | Status | Source |" in result
    assert "| `tiangong-mcp` | `0.1.0` | `0.0.1` | stale |" in result
    assert "## PyPI Release Launch Blocker" in result
    assert "Publish `tiangong-mcp==0.1.0` to PyPI before relying on `pip install tiangong-mcp` for the public campaign." in result
    assert "Do not claim the install loop reaches current growth tools while PyPI is stale." in result
    assert ".github/workflows/publish-pypi.yml" in result
    assert "Create a GitHub Release after PyPI Trusted Publishing is configured" in result
    assert "push the verified `v*` tag to trigger the same workflow" in result
    assert "manually dispatch `.github/workflows/publish-pypi.yml` with the existing `v*` tag" in result
    assert "## Current Candidate Git Tag Install Bridge" in result
    assert 'python -m pip install --upgrade "tiangong-mcp @ git+https://github.com/octo-org/octo-repo.git@v0.1.0"' in result
    assert "This bridge keeps contributors on the current tag while PyPI is stale or unverified; it does not close the PyPI install loop." in result
    assert "## PyPI Trusted Publisher Setup Runbook" in result
    assert "https://pypi.org/manage/project/tiangong-mcp/settings/publishing/" in result
    assert "| Repository owner | `octo-org` | `repository_owner`: `octo-org` |" in result
    assert "| Repository name | `octo-repo` | `repository`: `octo-org/octo-repo` |" in result
    assert "| Workflow filename | `publish-pypi.yml` |" in result
    assert "| Workflow path | `.github/workflows/publish-pypi.yml` |" in result
    assert "| Environment | `pypi` | `environment`: `pypi`" in result
    assert "Do not add a stored `PYPI_TOKEN`" in result
    assert "python -m build" in result
    assert "python -m twine check dist/*" in result


def test_public_growth_report_bridges_unverified_pypi_distribution(tmp_path):
    """When PyPI cannot be verified, contributors still need a bounded current-tag install bridge."""
    from tiangong.public_growth import (
        PublicDistributionReadiness,
        PublicGrowthIssueMetrics,
        PublicGrowthSnapshot,
        PublicReleaseReadiness,
        PublicRepoMetrics,
        format_public_growth_report,
    )

    event_path = tmp_path / "activation-events.jsonl"
    snapshot = PublicGrowthSnapshot(
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
        release_readiness=PublicReleaseReadiness(local_version="0.1.0", expected_tag="v0.1.0"),
        distribution_readiness=PublicDistributionReadiness(
            package_name="tiangong-mcp",
            local_version="0.1.0",
            published_version="",
            status="unverified",
            api_url="https://pypi.org/pypi/tiangong-mcp/json",
            project_url="https://pypi.org/project/tiangong-mcp/",
            reason="PyPI JSON API could not be reached",
        ),
    )

    result = format_public_growth_report(snapshot, activation_events=[], source_path=event_path)

    assert "## PyPI Distribution Verification Warning" in result
    assert "## Current Candidate Git Tag Install Bridge" in result
    assert 'python -m pip install --upgrade "tiangong-mcp @ git+https://github.com/octo-org/octo-repo.git@v0.1.0"' in result
    assert "This bridge keeps contributors on the current tag while PyPI is stale or unverified; it does not close the PyPI install loop." in result


def test_public_install_command_bridges_stale_pypi_distribution():
    """The shortest install surface should keep contributors off stale PyPI builds."""
    from tiangong.public_growth import PublicDistributionReadiness, format_public_install_command

    result = format_public_install_command(
        PublicDistributionReadiness(
            package_name="tiangong-mcp",
            local_version="0.1.4",
            published_version="0.0.1",
            status="stale",
            api_url="https://pypi.org/pypi/tiangong-mcp/json",
            project_url="https://pypi.org/project/tiangong-mcp/",
            reason="PyPI latest version differs from the local package metadata",
        ),
        repo_owner="octo-org",
        repo_name="octo-repo",
    )

    assert "# TianGong Public Install Command" in result
    assert "| `tiangong-mcp` | `0.1.4` | `0.0.1` | stale |" in result
    assert "## Current Candidate Git Tag Install Bridge" in result
    assert 'python -m pip install --upgrade "tiangong-mcp @ git+https://github.com/octo-org/octo-repo.git@v0.1.4"' in result
    assert "Canonical install after PyPI latest is current: `pip install -U tiangong-mcp`" in result
    assert 'start_cultivation(username="your_github_username")' in result
    assert 'forge_agent(name="first-growth-artifact"' in result
    assert "does not close the PyPI install loop" in result


def test_public_install_command_uses_pypi_when_distribution_is_current():
    """Once PyPI latest matches local metadata, the short install surface should prefer PyPI."""
    from tiangong.public_growth import PublicDistributionReadiness, format_public_install_command

    result = format_public_install_command(
        PublicDistributionReadiness(
            package_name="tiangong-mcp",
            local_version="0.1.4",
            published_version="0.1.4",
            status="current",
            api_url="https://pypi.org/pypi/tiangong-mcp/json",
            project_url="https://pypi.org/project/tiangong-mcp/",
            reason="PyPI latest version matches the local package metadata",
        ),
        repo_owner="octo-org",
        repo_name="octo-repo",
    )

    assert "# TianGong Public Install Command" in result
    assert "## Recommended Public Install" in result
    assert "`pip install -U tiangong-mcp`" in result
    assert "Git Tag Install Bridge" not in result
    assert 'start_cultivation(username="your_github_username")' in result


def test_public_growth_report_flags_missing_release_trigger(tmp_path):
    """A stale install loop should also prove whether the release-triggered PyPI workflow can run."""
    from tiangong.public_growth import (
        PublicDistributionReadiness,
        PublicGrowthIssueMetrics,
        PublicGrowthSnapshot,
        PublicReleaseReadiness,
        PublicRepoMetrics,
        format_public_growth_report,
    )

    event_path = tmp_path / "activation-events.jsonl"
    snapshot = PublicGrowthSnapshot(
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
        release_readiness=PublicReleaseReadiness(
            local_version="0.1.0",
            expected_tag="v0.1.0",
            status="missing",
            api_url="https://api.github.com/repos/octo-org/octo-repo/releases/tags/v0.1.0",
            reason="not found on the repository releases API",
        ),
        distribution_readiness=PublicDistributionReadiness(
            package_name="tiangong-mcp",
            local_version="0.1.0",
            published_version="0.0.1",
            status="stale",
            api_url="https://pypi.org/pypi/tiangong-mcp/json",
            project_url="https://pypi.org/project/tiangong-mcp/",
            reason="PyPI latest version differs from the local package metadata",
        ),
    )

    result = format_public_growth_report(snapshot, activation_events=[], source_path=event_path)

    assert "## GitHub Release Readiness" in result
    assert "| Local version | Expected release tag | Status | Source |" in result
    assert "| `0.1.0` | `v0.1.0` | missing |" in result
    assert "## GitHub Release Launch Blocker" in result
    assert "Create and publish GitHub Release `v0.1.0` after quality gates pass." in result
    assert "push tag `v0.1.0` to trigger `.github/workflows/publish-pypi.yml`" in result
    assert "protected manual workflow dispatch for `.github/workflows/publish-pypi.yml` with tag `v0.1.0`" in result
    assert "verifies it is reachable from `origin/main`" in result
    assert "verifies `pyproject.toml` version equals the tag" in result
    assert ".github/workflows/publish-pypi.yml" in result
    assert "PyPI Trusted Publishing" in result
    assert "public_growth_report()" in result


def test_public_growth_report_outputs_public_launch_closure_checklist(tmp_path):
    """Cold public proof should collapse launch blockers into one ordered execution checklist."""
    from tiangong.public_growth import (
        PublicDistributionReadiness,
        PublicGrowthIssueMetrics,
        PublicGrowthSnapshot,
        PublicIssueOpsReadiness,
        PublicIssueOpsRemoteFile,
        PublicReleaseReadiness,
        PublicRepoMetrics,
        format_public_growth_report,
    )

    event_path = tmp_path / "activation-events.jsonl"
    snapshot = PublicGrowthSnapshot(
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
                reason="not found on the repository default branch",
            ),
            share_form=PublicIssueOpsRemoteFile(
                route="Share Proof Issue Form",
                path=".github/ISSUE_TEMPLATE/tiangong-share-proof.yml",
                status="missing",
                reason="not found on the repository default branch",
            ),
            workflow=PublicIssueOpsRemoteFile(
                route="IssueOps Workflow",
                path=".github/workflows/issueops-onboarding.yml",
                status="missing",
                reason="not found on the repository default branch",
            ),
        ),
        release_readiness=PublicReleaseReadiness(
            local_version="0.1.0",
            expected_tag="v0.1.0",
            status="missing",
            api_url="https://api.github.com/repos/octo-org/octo-repo/releases/tags/v0.1.0",
            reason="not found on the repository releases API",
        ),
        distribution_readiness=PublicDistributionReadiness(
            package_name="tiangong-mcp",
            local_version="0.1.0",
            published_version="0.0.1",
            status="stale",
            api_url="https://pypi.org/pypi/tiangong-mcp/json",
            project_url="https://pypi.org/project/tiangong-mcp/",
            reason="PyPI latest version differs from the local package metadata",
        ),
    )

    result = format_public_growth_report(snapshot, activation_events=[], source_path=event_path)

    assert "## Public Launch Closure Checklist" in result
    assert "| Order | Gate | Exact next action | Proof to recheck |" in result
    assert "| 1 | Remote IssueOps routes | `tiangong-mcp public-launch-assets` verifies" in result
    assert ".github/ISSUE_TEMPLATE/tiangong-growth-flywheel.yml" in result
    assert "| 2 | PyPI Trusted Publisher | Configure PyPI project `tiangong-mcp`" in result
    assert "workflow filename `publish-pypi.yml`" in result
    assert "path `.github/workflows/publish-pypi.yml`" in result
    assert "environment `pypi`" in result
    assert "| 3 | GitHub Release trigger | Run `gh release create v0.1.0 --generate-notes`" in result
    assert "push tag `v0.1.0` to trigger the publish workflow" in result
    assert "manually dispatch `.github/workflows/publish-pypi.yml` with tag `v0.1.0`" in result
    assert "| 4 | PyPI latest version | Wait for `.github/workflows/publish-pypi.yml`" in result
    assert "| 5 | First public proof | Open the Growth Issue Form and Share Proof Issue Form" in result
    assert "record_growth_referral(" in result
    assert "record_share_attribution(" in result
    assert "Do not mark the flywheel closed until every row is verified from real public state." in result


def test_public_growth_report_tracks_target_contributor_progress_from_real_actors(tmp_path):
    """Campaign target progress should count real public Issue authors and local ledger actors only."""
    from tiangong.activation import (
        EVENT_ISSUEOPS_REFERRAL_RECORDED,
        EVENT_SHARE_ATTRIBUTION_RECORDED,
        load_activation_events,
        record_activation_event,
    )
    from tiangong.public_growth import (
        PublicGrowthIssueMetrics,
        PublicGrowthSnapshot,
        PublicPullRequestMetrics,
        PublicRepoMetrics,
        format_public_growth_report,
    )

    event_path = tmp_path / "activation-events.jsonl"
    record_activation_event(
        EVENT_ISSUEOPS_REFERRAL_RECORDED,
        actor="newbie",
        metadata={"source_url": "https://github.com/octo-org/octo-repo/issues/11"},
        path=event_path,
    )
    record_activation_event(
        EVENT_SHARE_ATTRIBUTION_RECORDED,
        actor="local-only",
        metadata={"share_url": "https://github.com/octo-org/octo-repo/issues/13"},
        path=event_path,
    )
    snapshot = PublicGrowthSnapshot(
        repo=PublicRepoMetrics(
            full_name="octo-org/octo-repo",
            html_url="https://github.com/octo-org/octo-repo",
            stargazers=20,
            forks=5,
            watchers=20,
            subscribers=6,
            open_issues=7,
            pushed_at="2026-06-03T00:00:00Z",
            updated_at="2026-06-03T01:00:00Z",
            api_url="https://api.github.com/repos/octo-org/octo-repo",
        ),
        growth_issues=PublicGrowthIssueMetrics(
            "tiangong:growth",
            2,
            1,
            1,
            [],
            "",
            False,
            ("newbie", "mentor"),
        ),
        share_issues=PublicGrowthIssueMetrics(
            "tiangong:share",
            1,
            1,
            0,
            [],
            "",
            False,
            ("sharer",),
        ),
        pull_requests=PublicPullRequestMetrics(
            total=1,
            open=1,
            closed=0,
            actors=("pr-author",),
            latest=[],
            api_url="https://api.github.com/repos/octo-org/octo-repo/pulls?state=all",
        ),
    )

    result = format_public_growth_report(
        snapshot,
        activation_events=load_activation_events(path=event_path),
        source_path=event_path,
        target_contributors=6,
    )

    assert "## Campaign Target Progress" in result
    assert "| Target contributors | 6 |" in result
    assert "| Real contributors observed | 5 |" in result
    assert "| Contributors still needed | 1 |" in result
    assert "| Target progress | 83.3% |" in result
    assert "@local-only" in result
    assert "@mentor" in result
    assert "@newbie" in result
    assert "@pr-author" in result
    assert "@sharer" in result
    assert "| Public Pull Requests | 1 |" in result
    assert "does not count stars, forks, watchers, subscribers, downloads, reposts, or retention as contributors" in result
    assert "`growth_campaign(target_contributors=6)`" in result
    assert "`public_growth_report(record_snapshot=True, target_contributors=6)`" in result
    assert "## Campaign Recap / Next Sprint" in result
    assert "Target shortfall" in result
    assert "| Next 72h target | 6 |" in result
    assert "Copy campaign recap" in result


def test_public_growth_report_increases_next_target_after_real_target_is_reached(tmp_path):
    """A reached target should produce a real-data next sprint without inventing extra contributors."""
    from tiangong.activation import (
        EVENT_ISSUEOPS_REFERRAL_RECORDED,
        load_activation_events,
        record_activation_event,
    )
    from tiangong.public_growth import (
        PublicGrowthIssueMetrics,
        PublicGrowthSnapshot,
        PublicPullRequestMetrics,
        PublicRepoMetrics,
        format_public_growth_report,
    )

    event_path = tmp_path / "activation-events.jsonl"
    record_activation_event(EVENT_ISSUEOPS_REFERRAL_RECORDED, actor="local", path=event_path)
    snapshot = PublicGrowthSnapshot(
        repo=PublicRepoMetrics(
            full_name="octo-org/octo-repo",
            html_url="https://github.com/octo-org/octo-repo",
            stargazers=20,
            forks=5,
            watchers=20,
            subscribers=6,
            open_issues=7,
            pushed_at="2026-06-03T00:00:00Z",
            updated_at="2026-06-03T01:00:00Z",
            api_url="https://api.github.com/repos/octo-org/octo-repo",
        ),
        growth_issues=PublicGrowthIssueMetrics(
            "tiangong:growth",
            3,
            1,
            2,
            [],
            "",
            False,
            ("alpha", "beta"),
        ),
        share_issues=PublicGrowthIssueMetrics(
            "tiangong:share",
            1,
            1,
            0,
            [],
            "",
            False,
            ("gamma",),
        ),
        pull_requests=PublicPullRequestMetrics(
            total=1,
            open=0,
            closed=1,
            actors=("pr-author",),
            latest=[],
            api_url="https://api.github.com/repos/octo-org/octo-repo/pulls?state=all",
        ),
    )

    result = format_public_growth_report(
        snapshot,
        activation_events=load_activation_events(path=event_path),
        source_path=event_path,
        target_contributors=3,
    )

    assert "| Real contributors observed | 5 |" in result
    assert "| Target progress | 100.0% |" in result
    assert "Target reached" in result
    assert "@pr-author" in result
    assert "| Next 72h target | 6 |" in result
    assert "`growth_campaign(target_contributors=6)`" in result
    assert "`public_growth_report(record_snapshot=True, target_contributors=6)`" in result
    assert "No downloads, retention, repost counts, referral conversions, rewards, stars, or forks are invented." in result


def test_public_growth_report_fetch_failure_is_recovery_surface(tmp_path):
    """A network/API failure should not become fake traction."""
    from tiangong.public_growth import format_public_growth_report

    event_path = tmp_path / "activation-events.jsonl"
    result = format_public_growth_report(
        None,
        activation_events=[],
        source_path=event_path,
        fetch_error="HTTP 403: rate limited",
    )

    assert "# TianGong Public Growth Proof" in result
    assert "## Public Flywheel Closure Verdict" in result
    assert "Verdict: not closed" in result
    assert "| External public snapshot | unverified | public GitHub/PyPI state was not fetched |" in result
    assert "Do not claim a closed public flywheel until the public snapshot is verified." in result
    assert "External GitHub metrics were not fetched" in result
    assert "HTTP 403: rate limited" in result
    assert "does not invent downloads, retention, repost counts, referral conversions, or rewards" in result
    assert "`growth_campaign(target_contributors=10)`" in result
    assert "`share_attribution_report()`" in result
    assert "`public_growth_report(record_snapshot=True, target_contributors=10)`" in result
    assert "`public_launch_preflight(target_contributors=10)`" in result
    assert "`public_proof_pack(target_contributors=10)`" in result
    assert "`tiangong-mcp public-proof-pack --target-contributors 10`" in result
    assert "## No-Network First Proof Pack" in result
    assert "TianGong First Public Proof Pack" in result
    assert "template=tiangong-growth-flywheel.yml" in result
    assert "template=tiangong-share-proof.yml" in result
    assert "After Submission CLI Ledger Commands" in result
    assert "tiangong-mcp record-growth-referral --route growth" in result
    assert "tiangong-mcp record-share-attribution --contribution" in result
    assert "First External Contributor Path" in result


def test_public_growth_report_fetch_failure_shows_local_recorded_proof(tmp_path):
    """API rate limits should not hide proof URLs already written to the local ledger."""
    from tiangong.activation import (
        EVENT_ISSUEOPS_REFERRAL_RECORDED,
        EVENT_SHARE_ATTRIBUTION_RECORDED,
        ActivationEvent,
    )
    from tiangong.public_growth import format_public_growth_report

    event_path = tmp_path / "activation-events.jsonl"
    events = [
        ActivationEvent(
            schema_version=1,
            event_type=EVENT_ISSUEOPS_REFERRAL_RECORDED,
            actor="JinNing6",
            timestamp=1.0,
            metadata={
                "route": "growth",
                "source_url": "https://github.com/JinNing6/TianGong/issues/1",
                "issue_number": 1,
            },
        ),
        ActivationEvent(
            schema_version=1,
            event_type=EVENT_SHARE_ATTRIBUTION_RECORDED,
            actor="JinNing6",
            artifact_name="tiangong-mcp-v0.1.0",
            timestamp=2.0,
            metadata={
                "contribution": "publish",
                "share_url": "https://github.com/JinNing6/TianGong/issues/2",
                "source_url": "https://github.com/JinNing6/TianGong/issues/1",
                "issue_number": 2,
            },
        ),
    ]

    result = format_public_growth_report(
        None,
        activation_events=events,
        source_path=event_path,
        target_contributors=25,
        fetch_error="GitHub API HTTP 403: rate limit exceeded",
    )

    assert "## Local Proof Already Recorded" in result
    assert "local activation ledger" in result
    assert "https://github.com/JinNing6/TianGong/issues/1" in result
    assert "https://github.com/JinNing6/TianGong/issues/2" in result
    assert "tiangong-mcp-v0.1.0" in result
    assert "Do not open duplicate first-proof Issues" in result
    assert "public_growth_report(record_snapshot=True, target_contributors=25)" in result


def test_public_growth_report_fetch_failure_reuses_campaign_target(tmp_path):
    """Rate-limit recovery should keep the active 72h target instead of resetting the proof pack."""
    from tiangong.public_growth import format_public_growth_report

    event_path = tmp_path / "activation-events.jsonl"
    result = format_public_growth_report(
        None,
        activation_events=[],
        source_path=event_path,
        target_contributors=6,
        fetch_error="HTTP 403: rate limited",
    )

    assert "tiangong-mcp public-proof-pack --target-contributors 6" in result
    assert "public_launch_preflight(target_contributors=6)" in result
    assert "public_proof_pack(target_contributors=6)" in result
    assert "public_growth_report(record_snapshot=True, target_contributors=6)" in result
    assert "target_contributors=6" in result
    assert "target_contributors=10" not in result


def test_public_launch_preflight_fetch_failure_includes_release_fallbacks(tmp_path):
    """API rate limits should not hide the no-network release and publish paths."""
    from tiangong.public_growth import format_public_launch_preflight

    event_path = tmp_path / "activation-events.jsonl"
    result = format_public_launch_preflight(
        None,
        activation_events=[],
        source_path=event_path,
        target_contributors=10,
        fetch_error="GitHub API HTTP 403: rate limit exceeded",
    )

    assert "External Fetch Status" in result
    assert "GitHub API HTTP 403: rate limit exceeded" in result
    assert "https://github.com/JinNing6/TianGong/releases/new" in result
    assert "Select existing tag `v0.1.4`" in result
    assert "https://github.com/JinNing6/TianGong/actions/workflows/publish-pypi.yml" in result
    assert "workflow_dispatch tag `v0.1.4`" in result
    assert "GITHUB_TOKEN" in result
    assert "https://api.github.com/repos/JinNing6/TianGong/releases" in result
    assert '"tag_name":"v0.1.4"' in result
    assert '"generate_release_notes":true' in result
    assert "## PyPI Trusted Publisher Setup Runbook" in result
    assert "invalid-publisher" in result
    assert "https://pypi.org/manage/project/tiangong-mcp/settings/publishing/" in result
    assert "| Repository owner | `JinNing6` | `repository_owner`: `JinNing6` |" in result
    assert "| Repository name | `TianGong` | `repository`: `JinNing6/TianGong` |" in result
    assert (
        "| Workflow filename | `publish-pypi.yml` | `workflow_ref`: "
        "`JinNing6/TianGong/.github/workflows/publish-pypi.yml@refs/tags/v0.1.4` |"
    ) in result
    assert (
        "| Environment | `pypi` | `environment`: `pypi` and "
        "`sub`: `repo:JinNing6/TianGong:environment:pypi` |"
    ) in result
    assert "Recheck install loop: `public_growth_report(record_snapshot=True, target_contributors=10)`" in result
    assert "tiangong-mcp public-proof-pack --target-contributors 10" in result
    assert "## Current Candidate Git Tag Install Bridge" in result
    assert 'python -m pip install --upgrade "tiangong-mcp @ git+https://github.com/JinNing6/TianGong.git@v0.1.4"' in result
    assert "Canonical install after PyPI latest is current: `pip install -U tiangong-mcp`" in result
    assert "does not close the PyPI install loop" in result


def test_public_launch_preflight_fetch_failure_reuses_campaign_target(tmp_path):
    """Rate-limit release recovery should not reset the active contributor target."""
    from tiangong.public_growth import format_public_launch_preflight

    event_path = tmp_path / "activation-events.jsonl"
    result = format_public_launch_preflight(
        None,
        activation_events=[],
        source_path=event_path,
        target_contributors=25,
        fetch_error="GitHub API HTTP 403: rate limit exceeded",
    )

    assert "tiangong-mcp public-proof-pack --target-contributors 25" in result
    assert "tiangong-mcp public-launch-preflight --target-contributors 25" in result
    assert "public_proof_pack(target_contributors=25)" in result
    assert "public_launch_preflight(target_contributors=25)" in result
    assert "public_growth_report(record_snapshot=True, target_contributors=25)" in result
    assert "target_contributors=10" not in result
    assert "--target-contributors 10" not in result


def test_public_launch_preflight_pypi_runbook_reuses_campaign_target(tmp_path):
    """Trusted Publisher recovery should preserve the active launch target."""
    from tiangong.public_growth import (
        PublicDistributionReadiness,
        PublicGrowthIssueMetrics,
        PublicGrowthSnapshot,
        PublicReleaseReadiness,
        PublicRepoMetrics,
        format_public_launch_preflight,
    )

    event_path = tmp_path / "activation-events.jsonl"
    snapshot = PublicGrowthSnapshot(
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
        release_readiness=PublicReleaseReadiness(
            local_version="0.1.0",
            expected_tag="v0.1.0",
            status="missing",
        ),
        distribution_readiness=PublicDistributionReadiness(
            package_name="tiangong-mcp",
            local_version="0.1.0",
            published_version="0.0.1",
            status="stale",
        ),
    )

    result = format_public_launch_preflight(
        snapshot,
        activation_events=[],
        source_path=event_path,
        target_contributors=30,
    )

    assert "Recheck install loop: `public_growth_report(record_snapshot=True, target_contributors=30)`" in result
    assert "public_proof_pack(target_contributors=30)" in result
    assert "target_contributors=10" not in result


def test_public_growth_snapshot_history_records_jsonl_and_reports_velocity(tmp_path):
    """Public traction needs real velocity history, not just a static snapshot."""
    from tiangong.activation import (
        EVENT_ISSUEOPS_REFERRAL_RECORDED,
        EVENT_SHARE_ATTRIBUTION_RECORDED,
        load_activation_events,
        record_activation_event,
    )
    from tiangong.public_growth import (
        PublicGrowthIssueMetrics,
        PublicGrowthSnapshot,
        PublicRepoMetrics,
        format_public_growth_report,
        load_public_growth_snapshots,
        record_public_growth_snapshot,
    )

    event_path = tmp_path / "activation-events.jsonl"
    history_path = tmp_path / "public-growth-snapshots.jsonl"
    record_activation_event(
        EVENT_ISSUEOPS_REFERRAL_RECORDED,
        actor="newbie",
        metadata={"source_url": "https://github.com/octo-org/octo-repo/issues/11"},
        path=event_path,
    )
    record_activation_event(
        EVENT_SHARE_ATTRIBUTION_RECORDED,
        actor="newbie",
        metadata={"share_url": "https://github.com/octo-org/octo-repo/issues/13"},
        path=event_path,
    )
    previous = PublicGrowthSnapshot(
        repo=PublicRepoMetrics(
            full_name="octo-org/octo-repo",
            html_url="https://github.com/octo-org/octo-repo",
            stargazers=7,
            forks=2,
            watchers=7,
            subscribers=3,
            open_issues=5,
            pushed_at="2026-06-01T00:00:00Z",
            updated_at="2026-06-02T00:00:00Z",
            api_url="https://api.github.com/repos/octo-org/octo-repo",
        ),
        growth_issues=PublicGrowthIssueMetrics("tiangong:growth", 2, 1, 1, [], ""),
        share_issues=PublicGrowthIssueMetrics("tiangong:share", 1, 0, 1, [], ""),
    )
    current = PublicGrowthSnapshot(
        repo=PublicRepoMetrics(
            full_name="octo-org/octo-repo",
            html_url="https://github.com/octo-org/octo-repo",
            stargazers=10,
            forks=3,
            watchers=10,
            subscribers=4,
            open_issues=6,
            pushed_at="2026-06-03T00:00:00Z",
            updated_at="2026-06-03T01:00:00Z",
            api_url="https://api.github.com/repos/octo-org/octo-repo",
        ),
        growth_issues=PublicGrowthIssueMetrics("tiangong:growth", 4, 2, 2, [], ""),
        share_issues=PublicGrowthIssueMetrics("tiangong:share", 2, 1, 1, [], ""),
    )

    entry = record_public_growth_snapshot(
        previous,
        activation_events=load_activation_events(path=event_path),
        path=history_path,
        now=1000.0,
    )
    history = load_public_growth_snapshots(path=history_path)
    result = format_public_growth_report(
        current,
        activation_events=load_activation_events(path=event_path),
        source_path=event_path,
        history=history,
        history_path=history_path,
    )

    assert history_path.read_text(encoding="utf-8").count("\n") == 1
    assert entry.repo_full_name == "octo-org/octo-repo"
    assert entry.stargazers == 7
    assert history[0].growth_issues == 2
    assert "# TianGong Public Growth Proof" in result
    assert "## Public Growth Velocity" in result
    assert "public-growth-snapshots.jsonl" in result
    assert "| Stars delta | +3 |" in result
    assert "| Forks delta | +1 |" in result
    assert "| Growth IssueOps delta | +2 |" in result
    assert "| Share Proof Issue delta | +1 |" in result
    assert "| Local return event delta | +0 |" in result
    assert "| Local share attribution delta | +0 |" in result
    assert "`public_growth_report(record_snapshot=True)`" in result
    assert "does not invent downloads, retention, repost counts, referral conversions, or rewards" in result


@pytest.mark.asyncio
async def test_mcp_public_growth_report_exposes_external_snapshot(monkeypatch, tmp_path):
    """The public proof surface should be callable from MCP."""
    from tiangong import mcp_server
    from tiangong.activation import EVENT_ISSUEOPS_REFERRAL_RECORDED, record_activation_event
    from tiangong.public_growth import (
        PublicGrowthIssueMetrics,
        PublicGrowthSnapshot,
        PublicRepoMetrics,
    )

    event_path = tmp_path / "activation-events.jsonl"
    record_activation_event(
        EVENT_ISSUEOPS_REFERRAL_RECORDED,
        actor="newbie",
        metadata={"source_url": "https://github.com/octo-org/octo-repo/issues/11"},
        path=event_path,
    )
    snapshot = PublicGrowthSnapshot(
        repo=PublicRepoMetrics(
            full_name="octo-org/octo-repo",
            html_url="https://github.com/octo-org/octo-repo",
            stargazers=7,
            forks=2,
            watchers=7,
            subscribers=3,
            open_issues=5,
            pushed_at="2026-06-01T00:00:00Z",
            updated_at="2026-06-02T00:00:00Z",
            api_url="https://api.github.com/repos/octo-org/octo-repo",
        ),
        growth_issues=PublicGrowthIssueMetrics("tiangong:growth", 1, 1, 0, [], ""),
        share_issues=PublicGrowthIssueMetrics("tiangong:share", 0, 0, 0, [], ""),
    )

    monkeypatch.setattr(mcp_server, "get_activation_event_path", lambda: event_path)
    monkeypatch.setattr(mcp_server, "fetch_public_growth_snapshot", lambda: snapshot)

    result = await mcp_server.public_growth_report()

    assert "TianGong Public Growth Proof" in result
    assert "octo-org/octo-repo" in result
    assert "| Stars | 7 |" in result
    assert "`public_growth_report()`" in result
    assert "TianGong" in result


@pytest.mark.asyncio
async def test_mcp_public_install_command_exposes_current_install_bridge(monkeypatch):
    """MCP users should get the same short install bridge without using the terminal CLI."""
    from tiangong import mcp_server
    from tiangong.public_growth import PublicDistributionReadiness

    monkeypatch.setattr(
        mcp_server,
        "fetch_public_distribution_readiness",
        lambda: PublicDistributionReadiness(
            package_name="tiangong-mcp",
            local_version="0.1.4",
            published_version="0.0.1",
            status="stale",
            api_url="https://pypi.org/pypi/tiangong-mcp/json",
            project_url="https://pypi.org/project/tiangong-mcp/",
            reason="PyPI latest version differs from the local package metadata",
        ),
    )

    result = await mcp_server.public_install_command()

    assert "TianGong Public Install Command" in result
    assert 'python -m pip install --upgrade "tiangong-mcp @ git+https://github.com/JinNing6/TianGong.git@v0.1.4"' in result
    assert "Canonical install after PyPI latest is current: `pip install -U tiangong-mcp`" in result
    assert 'start_cultivation(username="your_github_username")' in result
    assert "does not close the PyPI install loop" in result


@pytest.mark.asyncio
async def test_mcp_public_growth_report_can_record_public_snapshot(monkeypatch, tmp_path):
    """The MCP report should be able to persist real public snapshots on request."""
    from tiangong import mcp_server
    from tiangong.public_growth import (
        PublicGrowthIssueMetrics,
        PublicGrowthSnapshot,
        PublicRepoMetrics,
    )

    event_path = tmp_path / "activation-events.jsonl"
    history_path = tmp_path / "public-growth-snapshots.jsonl"
    snapshot = PublicGrowthSnapshot(
        repo=PublicRepoMetrics(
            full_name="octo-org/octo-repo",
            html_url="https://github.com/octo-org/octo-repo",
            stargazers=10,
            forks=3,
            watchers=10,
            subscribers=4,
            open_issues=6,
            pushed_at="2026-06-03T00:00:00Z",
            updated_at="2026-06-03T01:00:00Z",
            api_url="https://api.github.com/repos/octo-org/octo-repo",
        ),
        growth_issues=PublicGrowthIssueMetrics("tiangong:growth", 4, 2, 2, [], ""),
        share_issues=PublicGrowthIssueMetrics("tiangong:share", 2, 1, 1, [], ""),
    )

    monkeypatch.setattr(mcp_server, "get_activation_event_path", lambda: event_path)
    monkeypatch.setattr(mcp_server, "get_public_growth_snapshot_path", lambda: history_path)
    monkeypatch.setattr(mcp_server, "fetch_public_growth_snapshot", lambda: snapshot)

    result = await mcp_server.public_growth_report(record_snapshot=True, target_contributors=4)

    assert history_path.exists()
    assert history_path.read_text(encoding="utf-8").count("\n") == 1
    assert "Snapshot recorded: yes" in result
    assert "octo-org/octo-repo" in result
    assert "`public_growth_report(record_snapshot=True)`" in result
    assert "Target contributors" in result


def test_public_launch_preflight_formats_ordered_release_runbook(tmp_path):
    """The launch preflight should turn real public blockers into one release runbook."""
    from tiangong.public_growth import (
        PublicDistributionReadiness,
        PublicGrowthIssueMetrics,
        PublicGrowthSnapshot,
        PublicIssueOpsReadiness,
        PublicIssueOpsRemoteFile,
        PublicReleaseReadiness,
        PublicRepoMetrics,
        format_public_launch_preflight,
    )

    event_path = tmp_path / "activation-events.jsonl"
    snapshot = PublicGrowthSnapshot(
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
            local_version="0.1.0",
            expected_tag="v0.1.0",
            status="missing",
            api_url="https://api.github.com/repos/octo-org/octo-repo/releases/tags/v0.1.0",
        ),
        distribution_readiness=PublicDistributionReadiness(
            package_name="tiangong-mcp",
            local_version="0.1.0",
            published_version="0.0.1",
            status="stale",
            api_url="https://pypi.org/pypi/tiangong-mcp/json",
            project_url="https://pypi.org/project/tiangong-mcp/",
        ),
    )

    result = format_public_launch_preflight(
        snapshot,
        activation_events=[],
        source_path=event_path,
        target_contributors=10,
    )

    assert "# TianGong Public Launch Preflight" in result
    assert "## Current Public Gate Status" in result
    assert "| Remote IssueOps routes | blocked" in result
    assert "| GitHub Release trigger | blocked" in result
    assert "| PyPI install loop | blocked" in result
    assert "| First public proof | blocked" in result
    assert "## Local Quality Gates Before Release" in result
    assert "python -m ruff check .github tiangong tests" in result
    assert "python -m pytest -q" in result
    assert "python -m build" in result
    assert "python -m twine check dist/*" in result
    assert "## Public Launch Closure Checklist" in result
    assert "## PyPI Trusted Publisher Setup Runbook" in result
    assert "https://pypi.org/manage/project/tiangong-mcp/settings/publishing/" in result
    assert "| Workflow filename | `publish-pypi.yml` |" in result
    assert "| Environment | `pypi` | `environment`: `pypi`" in result
    assert "## First Public Proof Entrypoints" in result
    assert "template=tiangong-growth-flywheel.yml" in result
    assert "template=tiangong-share-proof.yml" in result
    assert "https://github.com/octo-org/octo-repo/issues/<opened-growth-issue-number>" in result
    assert "https://github.com/octo-org/octo-repo/issues/<opened-share-proof-issue-number>" in result
    assert "## After Submission CLI Ledger Commands" in result
    assert "tiangong-mcp record-growth-referral --route growth" in result
    assert "tiangong-mcp record-share-attribution --contribution forge" in result
    assert "## After Submission MCP Ledger Commands" in result
    assert 'record_growth_referral(route="growth"' in result
    assert 'record_share_attribution(contribution="forge"' in result
    assert "Use created Issue URLs, not `issues/new?...` form URLs, for ledger commands." in result
    assert "tiangong-mcp public-launch-assets" in result
    assert "gh release create v0.1.0 --generate-notes" in result
    assert "https://github.com/octo-org/octo-repo/releases/new" in result
    assert "Select existing tag `v0.1.0`" in result
    assert "https://github.com/octo-org/octo-repo/actions/workflows/publish-pypi.yml" in result
    assert "git push origin v0.1.0" in result
    assert "workflow_dispatch tag `v0.1.0`" in result
    assert "verifies `pyproject.toml` version before upload" in result
    assert "public_growth_report(record_snapshot=True, target_contributors=10)" in result
    assert "public_proof_pack(target_contributors=10)" in result
    assert "does not invent downloads, retention, repost counts, referral conversions, or rewards" in result


@pytest.mark.asyncio
async def test_mcp_public_launch_preflight_exposes_release_runbook(monkeypatch, tmp_path):
    """The public launch preflight should be callable directly from MCP."""
    from tiangong import mcp_server
    from tiangong.public_growth import (
        PublicDistributionReadiness,
        PublicGrowthIssueMetrics,
        PublicGrowthSnapshot,
        PublicReleaseReadiness,
        PublicRepoMetrics,
    )

    event_path = tmp_path / "activation-events.jsonl"
    snapshot = PublicGrowthSnapshot(
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
        release_readiness=PublicReleaseReadiness(local_version="0.1.0", expected_tag="v0.1.0", status="missing"),
        distribution_readiness=PublicDistributionReadiness(
            package_name="tiangong-mcp",
            local_version="0.1.0",
            published_version="0.0.1",
            status="stale",
        ),
    )

    monkeypatch.setattr(mcp_server, "get_activation_event_path", lambda: event_path)
    monkeypatch.setattr(mcp_server, "fetch_public_growth_snapshot", lambda: snapshot)

    result = await mcp_server.public_launch_preflight(target_contributors=10)

    assert "TianGong Public Launch Preflight" in result
    assert "Public Launch Closure Checklist" in result
    assert "PyPI Trusted Publisher Setup Runbook" in result
    assert "First Public Proof Entrypoints" in result
    assert "template=tiangong-growth-flywheel.yml" in result
    assert "template=tiangong-share-proof.yml" in result
    assert "gh release create v0.1.0 --generate-notes" in result
    assert "https://github.com/octo-org/octo-repo/releases/new" in result
    assert "Select existing tag `v0.1.0`" in result
    assert "https://github.com/octo-org/octo-repo/actions/workflows/publish-pypi.yml" in result
    assert "workflow_dispatch tag `v0.1.0`" in result
    assert "public_growth_report(record_snapshot=True, target_contributors=10)" in result
    assert "public_proof_pack(target_contributors=10)" in result
    assert "TianGong" in result


@pytest.mark.asyncio
async def test_mcp_public_proof_pack_exposes_external_contributor_invite():
    """MCP users should get the no-network proof pack without switching to the terminal CLI."""
    from tiangong import mcp_server

    result = await mcp_server.public_proof_pack(
        repo_owner="octo-org",
        repo_name="octo-repo",
        target_contributors=10,
        actor="maintainer",
        artifact_name="first-growth-artifact",
        contribution="forge",
    )

    assert "TianGong First Public Proof Pack" in result
    assert "https://github.com/octo-org/octo-repo/issues/new?" in result
    assert "template=tiangong-growth-flywheel.yml" in result
    assert "template=tiangong-share-proof.yml" in result
    assert "First External Contributor Path" in result
    assert "Copy External Contributor Invite" in result
    assert "tiangong-mcp public-install-command" in result
    assert "Install decision: tiangong-mcp public-install-command" in result
    assert "PyPI-current install after registry readiness: pip install -U tiangong-mcp" in result
    assert "Git Tag Candidate Install Bridge" in result
    assert 'python -m pip install --upgrade "tiangong-mcp @ git+https://github.com/octo-org/octo-repo.git@v0.1.4"' in result
    assert "Use this only when public preflight reports PyPI latest is stale or unverified." in result
    assert 'start_cultivation(username="your_github_username")' in result
    assert 'forge_agent(name="first-growth-artifact"' in result
    assert "tiangong-mcp record-growth-referral" in result
    assert "tiangong-mcp record-share-attribution" in result
    assert 'record_growth_referral(route="growth"' in result
    assert 'record_share_attribution(contribution="forge"' in result
    assert "actor=\"maintainer\"" in result
    assert "Use created Issue URLs, not `issues/new?...` form URLs" in result
    assert "Only public Growth/Share Issue authors, public PR authors, and local ledger actors count" in result
    assert "does not invent downloads, retention, repost counts, referral conversions, or rewards" in result
    assert "TianGong" in result
