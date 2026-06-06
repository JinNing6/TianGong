"""Growth-facing cultivation experience tests."""

import pytest

from tiangong.ceremony import (
    generate_grade_promotion,
    generate_tribulation_ceremony,
    generate_welcome_ceremony,
)
from tiangong.cultivator import CultivatorProfile, format_cultivator_profile
from tiangong.realm import REALMS
from tiangong.sect import SectProfile


def test_realm_ladder_matches_public_22_rank_promise():
    """The public promise is Mortal plus 22 ascension ranks ending at TianGong."""
    assert len(REALMS) == 23
    assert [realm.level for realm in REALMS] == list(range(23))
    assert REALMS[0].name_cn == "凡人"
    assert REALMS[21].name_cn == "鲁班"
    assert REALMS[22].name_cn == "天工"
    assert REALMS[22].tribulation_cn == "全球排名 Top 1（动态称号，唯一）"


def test_tribulation_ceremony_contains_shareable_momentum():
    """Breakthrough output should be something a user can share immediately."""
    ceremony = generate_tribulation_ceremony(
        username="JinNing6",
        old_realm=REALMS[0],
        new_realm=REALMS[1],
        agent_count=1,
        star_count=0,
    )

    assert "复制分享" in ceremony
    assert "我在 TianGong" in ceremony
    assert "tiangong-mcp public-install-command" in ceremony
    assert "下一步" in ceremony
    assert "`publish_agent`" in ceremony


def test_grade_promotion_ceremony_contains_shareable_momentum():
    """Artifact promotion should create a paste-ready brag card and next action."""
    ceremony = generate_grade_promotion(
        artifact_name="dragon-forge",
        old_grade_symbol="⚪",
        old_grade_name="凡器",
        new_grade_symbol="🟢",
        new_grade_name="灵器",
        spirit_power=42,
        next_threshold=100,
        next_grade_name="宝器",
    )

    assert "复制分享" in ceremony
    assert "我在 TianGong" in ceremony
    assert "dragon-forge" in ceremony
    assert "tiangong-mcp public-install-command" in ceremony
    assert "`infuse_spirit`" in ceremony
    assert "`refine_agent`" in ceremony


def test_welcome_ceremony_contains_shareable_first_session_momentum():
    """The first forge welcome should share the activation and point to real tools."""
    ceremony = generate_welcome_ceremony(username="newbie")

    assert "复制分享" in ceremony
    assert "我在 TianGong" in ceremony
    assert "@newbie" in ceremony
    assert "炼气期" in ceremony
    assert "tiangong-mcp public-install-command" in ceremony
    assert "`publish_agent`" in ceremony
    assert "`quest(action=\"browse\")`" in ceremony
    assert "`my_vault`" in ceremony
    assert "browse_quests" not in ceremony
    assert "my_artifacts" not in ceremony


def test_tribulation_check_turns_next_realm_into_shareable_action_card():
    """The public tribulation check should turn the next realm into an action surface."""
    from tiangong import cultivator

    profile = CultivatorProfile(
        username="forgeking",
        spirit_power=60,
        agent_count=5,
        reviews_given=3,
        refinement_count=2,
        quests_completed=1,
        sect="天工盟",
    )

    result = cultivator.format_tribulation_check(profile)

    assert "渡劫检查" in result
    assert "真实修行快照" in result
    assert "当前境界: 💛 结丹期" in result
    assert "下一劫: 💜 元婴期" in result
    assert "还需灵力: 90" in result
    assert "拥有 3 件 🟢灵器 且为 5 件法宝评价" in result
    assert "真实渡劫门槛" in result
    assert "⛔ 灵力: 60/150" in result
    assert "⛔ 评价次数: 3/5" in result
    assert "没有伪造渡劫成功" in result
    assert "`my_realm(username=\"forgeking\")`" in result
    assert "`quest(action=\"browse\")`" in result
    assert "`leaderboard(type=\"season\")`" in result
    assert "`leaderboard(type=\"tournament\")`" in result
    assert "复制渡劫战书" in result
    assert "tiangong-mcp public-install-command" in result


def test_tribulation_check_points_high_realm_to_evidence_submission():
    """A progress-gated high realm should expose the public evidence submission command."""
    from tiangong import cultivator

    profile = CultivatorProfile(
        username="lineage-master",
        spirit_power=2500,
        agent_count=5,
        refinement_count=30,
        reviews_given=50,
    )

    result = cultivator.format_tribulation_check(profile)

    assert "当前境界: 🔴 婴变期" in result
    assert "下一劫: 🌟 问鼎期" in result
    assert "传承引用用户（tribulation_progress.lineage_users）" in result
    assert "submit_tribulation_evidence" in result
    assert 'evidence_key="lineage_users"' in result
    assert "source_url=\"https://github.com/owner/repo/issues/1\"" in result


@pytest.mark.asyncio
async def test_mcp_check_tribulation_exposes_public_cycle_node(monkeypatch):
    """The README check_tribulation loop node should be a real callable MCP tool."""
    from tiangong import mcp_server

    async def fake_get_cultivator(username):
        return CultivatorProfile(
            username=username,
            spirit_power=0,
            agent_count=0,
        )

    monkeypatch.setattr(mcp_server, "get_cultivator", fake_get_cultivator)

    result = await mcp_server.check_tribulation(username="newbie")

    assert "渡劫检查" in result
    assert "当前境界: 🧑 凡人" in result
    assert "下一劫: 🌱 炼气期" in result
    assert "还需灵力: 1" in result
    assert "`forge_agent`" in result
    assert "`my_realm(username=\"newbie\")`" in result
    assert "复制渡劫战书" in result
    assert "TianGong" in result


@pytest.mark.asyncio
async def test_submit_tribulation_evidence_records_real_source_and_shares(monkeypatch):
    """Submitting high-realm evidence should become a real, shareable tribulation progress event."""
    from tiangong import mcp_server

    saved = []

    async def fake_get_cultivator(username):
        return CultivatorProfile(
            username=username,
            spirit_power=2500,
            agent_count=5,
            refinement_count=30,
            reviews_given=50,
        )

    async def fake_save_cultivator(profile, message=""):
        saved.append((profile, message))

    monkeypatch.setattr(mcp_server, "get_cultivator", fake_get_cultivator)
    monkeypatch.setattr(mcp_server, "save_cultivator", fake_save_cultivator)

    result = await mcp_server.submit_tribulation_evidence(
        username="lineage-master",
        evidence_key="lineage_users",
        amount=10,
        source_url="https://github.com/JinNing6/TianGong/issues/77",
        note="10 real users forked or referenced the artifact lineage.",
    )

    assert saved
    saved_profile = saved[0][0]
    assert saved_profile.tribulation_progress["lineage_users"]["amount"] == 10
    assert saved_profile.realm.name_cn == "问鼎期"
    assert "渡劫证据已记录" in result
    assert "lineage_users" in result
    assert "https://github.com/JinNing6/TianGong/issues/77" in result
    assert "婴变期 → 问鼎期" in result
    assert "复制渡劫证据" in result
    assert "tiangong-mcp public-install-command" in result
    assert "`check_tribulation(username=\"lineage-master\")`" in result
    assert "`leaderboard(type=\"season\")`" in result


@pytest.mark.asyncio
async def test_infuse_spirit_contains_shareable_community_momentum(monkeypatch):
    """A successful appraisal should become a shareable community contribution."""
    from tiangong import review

    async def fake_can_review(username):
        return True, ""

    async def fake_get_cultivator(username):
        return CultivatorProfile(username=username, spirit_power=100, agent_count=1)

    async def fake_noop(*args, **kwargs):
        return None

    async def fake_posted(*args, **kwargs):
        return True

    monkeypatch.setattr("tiangong.cultivator.can_review", fake_can_review)
    monkeypatch.setattr("tiangong.cultivator.get_cultivator", fake_get_cultivator)
    monkeypatch.setattr("tiangong.cultivator.record_review", fake_noop)
    monkeypatch.setattr("tiangong.cultivator.update_cultivator_stats", fake_noop)
    monkeypatch.setattr(review, "_post_review_to_issue", fake_posted)

    result = await review.infuse_spirit(
        artifact_name="dragon-forge",
        reviewer="reviewer",
        scores={
            "inscription": 8,
            "formation": 8,
            "technique": 8,
            "lineage": 8,
            "resilience": 8,
            "enlightenment": 8,
        },
        comment="扎实可用。",
    )

    assert "复制分享" in result
    assert "我在 TianGong" in result
    assert "dragon-forge" in result
    assert "@reviewer" in result
    assert "tiangong-mcp public-install-command" in result
    assert "`infuse_spirit`" in result
    assert "`my_realm()`" in result
    assert "`leaderboard(type=\"season\")`" in result
    assert "record_share_attribution" in result
    assert 'contribution="infuse"' in result
    assert 'artifact_name="dragon-forge"' in result


@pytest.mark.asyncio
async def test_infuse_spirit_invalid_scores_return_action_help():
    """Invalid appraisal scores should recover into public review actions."""
    from tiangong import mcp_server

    result = await mcp_server.infuse_spirit(
        artifact_name="dragon-forge",
        inscription=11,
        reviewer="reviewer",
    )

    assert "`inscription` 评分必须为 1-10" in result
    assert "公开入口" in result
    assert "没有伪造鉴定结果" in result
    assert "复制鉴定纠错" in result
    assert "tiangong-mcp public-install-command" in result
    assert (
        "`infuse_spirit(artifact_name=\"dragon-forge\", inscription=5, formation=5, "
        "technique=5, lineage_score=5, resilience=5, enlightenment=5, comment=\"...\")`"
    ) in result
    assert "`treasure_pavilion(action=\"search\", query=\"dragon-forge\")`" in result
    assert "`treasure_pavilion(action=\"summon\", artifact_name=\"dragon-forge\")`" in result
    assert "`quest(action=\"post\", artifact_name=\"dragon-forge\"," in result
    assert "`leaderboard(type=\"season\")`" in result
    assert "`my_realm(username=\"reviewer\")`" in result


@pytest.mark.asyncio
async def test_infuse_spirit_reviewer_ineligible_returns_onboarding_recovery(monkeypatch):
    """Reviewer eligibility failures should not be misreported as score errors."""
    from tiangong import mcp_server

    async def fake_infuse(artifact_name, reviewer, scores, comment):
        return "⚠️ 凡人无评价资格。请先发布至少 1 件法宝踏入修行之路。"

    monkeypatch.setattr(mcp_server, "_infuse", fake_infuse)

    result = await mcp_server.infuse_spirit(
        artifact_name="dragon-forge",
        reviewer="newbie",
        inscription=8,
        formation=8,
        technique=8,
        lineage_score=8,
        resilience=8,
        enlightenment=8,
        comment="Looks useful",
    )

    assert "凡人无评价资格" in result
    assert "真实鉴定资格失败快照" in result
    assert "没有伪造鉴定结果" in result
    assert "没有授予灵力" in result
    assert "复制鉴定资格恢复" in result
    assert "六维评分必须全部是 1-10" not in result
    assert "`forge_agent(name=\"my-first-artifact\"," in result
    assert "`publish_agent(artifact_name=\"my-first-artifact\")`" in result
    assert "`treasure_pavilion(action=\"search\", query=\"dragon-forge\")`" in result
    assert "`my_realm(username=\"newbie\")`" in result
    assert "`leaderboard(type=\"season\")`" in result
    assert "tiangong-mcp public-install-command" in result


@pytest.mark.asyncio
async def test_post_refine_quest_contains_shareable_recruitment(monkeypatch):
    """Posting a bounty should recruit contributors with a real claim path."""
    from tiangong import review

    class FakeResponse:
        status_code = 201

        def json(self):
            return {
                "number": 77,
                "html_url": "https://github.com/JinNing6/TianGong/issues/77",
            }

    posted_payloads = []

    async def fake_post(self, url, headers=None, json=None):
        posted_payloads.append(json)
        return FakeResponse()

    monkeypatch.setattr(review.config, "GITHUB_TOKEN", "token")
    monkeypatch.setattr(review.config, "GITHUB_REPO_OWNER", "JinNing6")
    monkeypatch.setattr(review.config, "GITHUB_REPO_NAME", "TianGong")
    monkeypatch.setattr(review.httpx.AsyncClient, "post", fake_post)

    result = await review.post_refine_quest(
        artifact_name="dragon-forge",
        quest_description="Need better docs for first-time contributors",
        creator="forgeking",
        current_code_url="https://github.com/JinNing6/TianGong/tree/main/dragon-forge",
    )

    assert "复制分享" in result
    assert "我在 TianGong" in result
    assert "dragon-forge" in result
    assert "Need better docs" in result
    assert "@forgeking" in result
    assert "https://github.com/JinNing6/TianGong/issues/77" in result
    assert "tiangong-mcp public-install-command" in result
    assert "`quest(action=\"claim\", quest_issue_number=77)`" in result
    assert "`quest(action=\"browse\")`" in result
    assert "`verify_refinement`" in result
    assert "record_share_attribution" in result
    assert 'contribution="quest_post"' in result
    assert 'share_url="https://github.com/JinNing6/TianGong/issues/77"' in result
    assert "`quest(action=\"post\")`" in posted_payloads[0]["body"]
    assert "post_refine_quest" not in posted_payloads[0]["body"]


@pytest.mark.asyncio
async def test_post_refine_quest_issue_body_round_trips_as_public_contract(monkeypatch):
    """A generated bounty Issue body should be machine-parseable for promotion workflows."""
    from tiangong import review

    class FakeResponse:
        status_code = 201

        def json(self):
            return {
                "number": 88,
                "html_url": "https://github.com/JinNing6/TianGong/issues/88",
            }

    posted_payloads = []

    async def fake_post(self, url, headers=None, json=None):
        posted_payloads.append(json)
        return FakeResponse()

    monkeypatch.setattr(review.config, "GITHUB_TOKEN", "token")
    monkeypatch.setattr(review.config, "GITHUB_REPO_OWNER", "JinNing6")
    monkeypatch.setattr(review.config, "GITHUB_REPO_NAME", "TianGong")
    monkeypatch.setattr(review.httpx.AsyncClient, "post", fake_post)

    await review.post_refine_quest(
        artifact_name="dragon-forge",
        quest_description="Need better docs for first-time contributors",
        creator="forgeking",
        current_code_url="https://github.com/JinNing6/TianGong/tree/main/dragon-forge",
    )

    body = posted_payloads[0]["body"]
    parsed = review.parse_refine_quest_issue_body(body)

    assert "<!-- tiangong:refine-quest:v1 -->" in body
    assert parsed == {
        "schema_version": 1,
        "artifact_name": "dragon-forge",
        "creator": "forgeking",
        "quest_description": "Need better docs for first-time contributors",
        "current_code_url": "https://github.com/JinNing6/TianGong/tree/main/dragon-forge",
        "source_command": 'quest(action="post")',
    }
    assert posted_payloads[0]["labels"] == ["refine-quest", "help-wanted"]
    assert "GITHUB_TOKEN" not in body
    assert "post_refine_quest" not in body


@pytest.mark.asyncio
async def test_claim_refine_quest_contains_submit_path_and_share_block(monkeypatch):
    """Claiming a bounty should pull the refiner into the next real tool step."""
    from tiangong import review

    class FakeResponse:
        status_code = 201

    posted_payloads = []

    async def fake_post(self, url, headers=None, json=None):
        posted_payloads.append(json)
        return FakeResponse()

    monkeypatch.setattr(review.config, "GITHUB_TOKEN", "token")
    monkeypatch.setattr(review.config, "GITHUB_REPO_OWNER", "JinNing6")
    monkeypatch.setattr(review.config, "GITHUB_REPO_NAME", "TianGong")
    monkeypatch.setattr(review.httpx.AsyncClient, "post", fake_post)

    result = await review.claim_refine_quest(quest_issue_number=77, refiner="refiner")

    assert "复制分享" in result
    assert "我在 TianGong" in result
    assert "@refiner" in result
    assert "Issue #77" in result
    assert "tiangong-mcp public-install-command" in result
    assert "`quest(action=\"submit\", quest_issue_number=77, solution=\"...\")`" in result
    assert "`quest(action=\"browse\")`" in result
    assert "record_share_attribution" in result
    assert 'contribution="quest_claim"' in result
    assert "complete_quest" not in result
    assert "`quest(action=\"claim\")`" in posted_payloads[0]["body"]
    assert "`quest(action=\"submit\")`" in posted_payloads[0]["body"]


@pytest.mark.asyncio
async def test_claim_refine_quest_comment_round_trips_as_public_contract(monkeypatch):
    """A generated claim comment should be parseable by public promotion workflows."""
    from tiangong import review

    class FakeResponse:
        status_code = 201

    posted_payloads = []

    async def fake_post(self, url, headers=None, json=None):
        posted_payloads.append(json)
        return FakeResponse()

    monkeypatch.setattr(review.config, "GITHUB_TOKEN", "token")
    monkeypatch.setattr(review.config, "GITHUB_REPO_OWNER", "JinNing6")
    monkeypatch.setattr(review.config, "GITHUB_REPO_NAME", "TianGong")
    monkeypatch.setattr(review.httpx.AsyncClient, "post", fake_post)

    await review.claim_refine_quest(quest_issue_number=77, refiner="refiner")

    body = posted_payloads[0]["body"]
    parsed = review.parse_claim_refine_quest_comment_body(body)

    assert "<!-- tiangong:refine-claim:v1 -->" in body
    assert parsed == {
        "schema_version": 1,
        "refiner": "refiner",
        "status": "进行中",
        "source_command": 'quest(action="claim")',
        "next_command": 'quest(action="submit")',
    }
    assert "GITHUB_TOKEN" not in body
    assert "claim_refine_quest" not in body


@pytest.mark.asyncio
async def test_submit_refinement_contains_review_path_and_share_block(monkeypatch):
    """Submitting refinement work should call the publisher back to verify it."""
    from tiangong import review

    class FakeResponse:
        status_code = 201

    posted_payloads = []

    async def fake_post(self, url, headers=None, json=None):
        posted_payloads.append(json)
        return FakeResponse()

    monkeypatch.setattr(review.config, "GITHUB_TOKEN", "token")
    monkeypatch.setattr(review.config, "GITHUB_REPO_OWNER", "JinNing6")
    monkeypatch.setattr(review.config, "GITHUB_REPO_NAME", "TianGong")
    monkeypatch.setattr(review.httpx.AsyncClient, "post", fake_post)

    result = await review.submit_refinement(
        quest_issue_number=77,
        refiner="refiner",
        solution_description="Added retry with exponential backoff",
    )

    assert "复制分享" in result
    assert "我在 TianGong" in result
    assert "@refiner" in result
    assert "Added retry" in result
    assert "Issue #77" in result
    assert "tiangong-mcp public-install-command" in result
    assert "`verify_refinement`" in result
    assert "`my_realm(username=\"refiner\")`" in result
    assert "record_share_attribution" in result
    assert 'contribution="quest_submit"' in result
    assert "`quest(action=\"submit\")`" in posted_payloads[0]["body"]
    assert "`verify_refinement`" in posted_payloads[0]["body"]
    assert "submit_refinement" not in posted_payloads[0]["body"]


@pytest.mark.asyncio
async def test_submit_refinement_comment_round_trips_as_public_contract(monkeypatch):
    """A generated submission comment should be parseable by public promotion workflows."""
    from tiangong import review

    class FakeResponse:
        status_code = 201

    posted_payloads = []

    async def fake_post(self, url, headers=None, json=None):
        posted_payloads.append(json)
        return FakeResponse()

    monkeypatch.setattr(review.config, "GITHUB_TOKEN", "token")
    monkeypatch.setattr(review.config, "GITHUB_REPO_OWNER", "JinNing6")
    monkeypatch.setattr(review.config, "GITHUB_REPO_NAME", "TianGong")
    monkeypatch.setattr(review.httpx.AsyncClient, "post", fake_post)

    await review.submit_refinement(
        quest_issue_number=77,
        refiner="refiner",
        solution_description="Added retry with exponential backoff",
    )

    body = posted_payloads[0]["body"]
    parsed = review.parse_submit_refinement_comment_body(body)

    assert "<!-- tiangong:refine-submit:v1 -->" in body
    assert parsed == {
        "schema_version": 1,
        "refiner": "refiner",
        "solution_description": "Added retry with exponential backoff",
        "source_command": 'quest(action="submit")',
        "next_command": "verify_refinement",
    }
    assert "GITHUB_TOKEN" not in body
    assert "submit_refinement" not in body


@pytest.mark.asyncio
async def test_verify_refinement_approval_rewards_closes_and_shares(monkeypatch):
    """Approving a bounty should award the documented reward and share completion."""
    from tiangong import review

    class FakeResponse:
        status_code = 201

    posted_payloads = []
    patched_payloads = []
    stat_updates = []

    async def fake_post(self, url, headers=None, json=None):
        posted_payloads.append(json)
        return FakeResponse()

    async def fake_patch(self, url, headers=None, json=None):
        patched_payloads.append(json)
        return FakeResponse()

    async def fake_update_cultivator_stats(**kwargs):
        stat_updates.append(kwargs)

    monkeypatch.setattr(review.config, "GITHUB_TOKEN", "token")
    monkeypatch.setattr(review.config, "GITHUB_REPO_OWNER", "JinNing6")
    monkeypatch.setattr(review.config, "GITHUB_REPO_NAME", "TianGong")
    monkeypatch.setattr(review.httpx.AsyncClient, "post", fake_post)
    monkeypatch.setattr(review.httpx.AsyncClient, "patch", fake_patch)
    monkeypatch.setattr("tiangong.cultivator.update_cultivator_stats", fake_update_cultivator_stats)

    result = await review.verify_refinement(
        quest_issue_number=77,
        refiner="refiner",
        reviewer="reviewer",
        is_approved=True,
        feedback="Looks solid",
    )

    assert "复制分享" in result
    assert "我在 TianGong" in result
    assert "@refiner" in result
    assert "@reviewer" in result
    assert "Issue #77" in result
    assert "+50" in result
    assert "tiangong-mcp public-install-command" in result
    assert "`my_realm(username=\"refiner\")`" in result
    assert "`leaderboard(type=\"season\")`" in result
    assert "record_share_attribution" in result
    assert 'contribution="quest_verify"' in result
    assert stat_updates == [
        {
            "username": "refiner",
            "spirit_delta": 50,
            "quest_delta": 1,
            "refinement_delta": 1,
        }
    ]
    assert patched_payloads == [{"state": "closed", "state_reason": "completed"}]
    assert "`verify_refinement`" in posted_payloads[0]["body"]
    assert "verify_refinement(" not in posted_payloads[0]["body"]


@pytest.mark.asyncio
async def test_verify_refinement_comment_round_trips_as_public_contract(monkeypatch):
    """A generated verification comment should be parseable by public settlement workflows."""
    from tiangong import review

    class FakeResponse:
        status_code = 201

    posted_payloads = []
    patched_payloads = []

    async def fake_post(self, url, headers=None, json=None):
        posted_payloads.append(json)
        return FakeResponse()

    async def fake_patch(self, url, headers=None, json=None):
        patched_payloads.append(json)
        return FakeResponse()

    async def fake_update_cultivator_stats(**kwargs):
        return None

    monkeypatch.setattr(review.config, "GITHUB_TOKEN", "token")
    monkeypatch.setattr(review.config, "GITHUB_REPO_OWNER", "JinNing6")
    monkeypatch.setattr(review.config, "GITHUB_REPO_NAME", "TianGong")
    monkeypatch.setattr(review.httpx.AsyncClient, "post", fake_post)
    monkeypatch.setattr(review.httpx.AsyncClient, "patch", fake_patch)
    monkeypatch.setattr("tiangong.cultivator.update_cultivator_stats", fake_update_cultivator_stats)

    await review.verify_refinement(
        quest_issue_number=77,
        refiner="refiner",
        reviewer="forgeking",
        is_approved=True,
        feedback="Looks solid",
    )

    body = posted_payloads[0]["body"]
    parsed = review.parse_verify_refinement_comment_body(body)

    assert "<!-- tiangong:refine-verify:v1 -->" in body
    assert parsed == {
        "schema_version": 1,
        "reviewer": "forgeking",
        "refiner": "refiner",
        "is_approved": True,
        "result": "通过",
        "feedback": "Looks solid",
        "source_command": "verify_refinement",
    }
    assert patched_payloads == [{"state": "closed", "state_reason": "completed"}]
    assert "GITHUB_TOKEN" not in body
    assert "verify_refinement(" not in body


@pytest.mark.asyncio
async def test_verify_refinement_failure_returns_reward_recovery_card(monkeypatch):
    """Failed bounty verification should recover without faking reward or closure."""
    from tiangong import mcp_server

    async def fake_verify_refinement(
        quest_issue_number,
        refiner,
        reviewer,
        is_approved,
        feedback,
    ):
        return "⚠️ 未配置 GITHUB_TOKEN"

    monkeypatch.setattr(mcp_server, "_verify_refinement", fake_verify_refinement)

    result = await mcp_server.verify_refinement(
        quest_issue_number=77,
        refiner="refiner",
        reviewer="reviewer",
        is_approved=True,
        feedback="Looks solid",
    )

    assert "未配置 GITHUB_TOKEN" in result
    assert "真实验收失败快照" in result
    assert "没有写入 GitHub Issue 评论" in result
    assert "没有关闭 Issue" in result
    assert "没有发放灵力" in result
    assert "复制验收失败恢复" in result
    assert "tiangong-mcp public-install-command" in result
    assert "GITHUB_TOKEN" in result
    assert (
        "`verify_refinement(quest_issue_number=77, refiner=\"refiner\", "
        "is_approved=True, feedback=\"Looks solid\")`"
    ) in result
    assert "`quest(action=\"submit\", quest_issue_number=77, solution=\"...\")`" in result
    assert "`quest(action=\"browse\")`" in result
    assert "`my_realm(username=\"refiner\")`" in result
    assert "`leaderboard(type=\"season\")`" in result
    assert "review.verify_refinement" not in result


@pytest.mark.asyncio
async def test_browse_quests_exposes_live_bounty_board_and_share_block(monkeypatch):
    """Browsing quests should turn real open GitHub issues into claimable bounties."""
    from tiangong import review

    class FakeResponse:
        status_code = 200

        def json(self):
            return {
                "total_count": 2,
                "items": [
                    {
                        "number": 88,
                        "title": "🔥 [淬炼令] dragon-forge — Add streaming support",
                        "html_url": "https://github.com/JinNing6/TianGong/issues/88",
                        "created_at": "2026-06-01T08:00:00Z",
                        "user": {"login": "forgeking"},
                    },
                    {
                        "number": 77,
                        "title": "🔥 [淬炼令] phoenix-agent — Improve docs",
                        "html_url": "https://github.com/JinNing6/TianGong/issues/77",
                        "created_at": "2026-05-31T08:00:00Z",
                        "user": {"login": "docmaster"},
                    },
                ],
            }

    captured_params = []

    async def fake_get(self, url, headers=None, params=None):
        captured_params.append(params)
        return FakeResponse()

    monkeypatch.setattr(review.config, "GITHUB_TOKEN", "token")
    monkeypatch.setattr(review.config, "GITHUB_REPO_OWNER", "JinNing6")
    monkeypatch.setattr(review.config, "GITHUB_REPO_NAME", "TianGong")
    monkeypatch.setattr(review.httpx.AsyncClient, "get", fake_get)

    result = await review.browse_quests(limit=2)

    assert "悬赏天榜" in result
    assert "GitHub open Issues 快照" in result
    assert "当前有 2 个活跃的淬炼令" in result
    assert "悬赏: +50 灵力" in result
    assert "dragon-forge" in result
    assert "phoenix-agent" in result
    assert "https://github.com/JinNing6/TianGong/issues/88" in result
    assert "`quest(action=\"claim\", quest_issue_number=88)`" in result
    assert "`quest(action=\"claim\", quest_issue_number=77)`" in result
    assert "复制分享" in result
    assert "我在 TianGong" in result
    assert "tiangong-mcp public-install-command" in result
    assert "`quest(action=\"post\")`" in result
    assert "`quest(action=\"browse\")`" in result
    assert "is:issue" in captured_params[0]["q"]
    assert captured_params[0]["sort"] == "created"
    assert captured_params[0]["order"] == "desc"


@pytest.mark.asyncio
async def test_quest_missing_post_args_returns_action_help():
    """Missing quest post arguments should become a public recovery card."""
    from tiangong import mcp_server

    result = await mcp_server.quest(action="post", username="forgeking")

    assert "发布悬赏令需要 artifact_name 和 description" in result
    assert "公开入口" in result
    assert "复制悬赏纠错" in result
    assert "tiangong-mcp public-install-command" in result
    assert "`quest(action=\"post\", artifact_name=\"artifact-name\", description=\"需要改进的内容\")`" in result
    assert "`quest(action=\"browse\")`" in result
    assert "`quest(action=\"claim\", quest_issue_number=88)`" in result
    assert "`quest(action=\"submit\", quest_issue_number=88, solution=\"...\")`" in result
    assert "`leaderboard(type=\"season\")`" in result
    assert "post_refine_quest" not in result


@pytest.mark.asyncio
async def test_quest_post_failure_returns_side_effect_recovery_card(monkeypatch):
    """Failed bounty publishing should recover without faking an Issue or reward."""
    from tiangong import mcp_server

    async def fake_post_quest(artifact_name, description, username, code_url):
        return "⚠️ 未配置 GITHUB_TOKEN"

    monkeypatch.setattr(mcp_server, "_post_quest", fake_post_quest)

    result = await mcp_server.quest(
        action="post",
        artifact_name="dragon-forge",
        description="Need better onboarding docs",
        username="forgeking",
    )

    assert "未配置 GITHUB_TOKEN" in result
    assert "真实悬赏失败快照" in result
    assert "没有写入 GitHub Issue" in result
    assert "没有发放灵力" in result
    assert "复制悬赏失败恢复" in result
    assert "tiangong-mcp public-install-command" in result
    assert "GITHUB_TOKEN" in result
    assert (
        "`quest(action=\"post\", artifact_name=\"dragon-forge\", "
        "description=\"Need better onboarding docs\")`"
    ) in result
    assert "`quest(action=\"browse\")`" in result
    assert "`treasure_pavilion(action=\"search\", query=\"dragon-forge\")`" in result
    assert "`my_realm(username=\"forgeking\")`" in result
    assert "`leaderboard(type=\"season\")`" in result
    assert "post_refine_quest" not in result


@pytest.mark.asyncio
async def test_quest_missing_submit_args_returns_action_help():
    """Missing submit arguments should point to the real submit and browse path."""
    from tiangong import mcp_server

    result = await mcp_server.quest(action="submit", quest_issue_number=88, username="refiner")

    assert "提交成果需要 quest_issue_number 和 solution" in result
    assert "公开入口" in result
    assert "复制悬赏纠错" in result
    assert "`quest(action=\"submit\", quest_issue_number=88, solution=\"...\")`" in result
    assert "`quest(action=\"browse\")`" in result
    assert "`verify_refinement`" in result
    assert "submit_refinement" not in result


@pytest.mark.asyncio
async def test_quest_unknown_action_returns_help_without_fake_browse(monkeypatch):
    """Unknown quest actions should not silently browse the live bounty board."""
    from tiangong import mcp_server

    browse_calls = []

    async def fake_browse_quests(limit=10):
        browse_calls.append(limit)
        return "fake live quest board"

    monkeypatch.setattr(mcp_server, "_browse_quests", fake_browse_quests)

    result = await mcp_server.quest(action="fly", limit=3)

    assert browse_calls == []
    assert "未知悬赏令 action" in result
    assert "没有伪造悬赏榜" in result
    assert "复制悬赏纠错" in result
    assert "`quest(action=\"browse\")`" in result
    assert "`quest(action=\"post\", artifact_name=\"artifact-name\", description=\"需要改进的内容\")`" in result
    assert "`leaderboard(type=\"season\")`" in result


def test_treasure_pavilion_search_results_are_actionable_and_shareable():
    """Discovery should point users from search to summon, appraise, and share."""
    from tiangong.search import format_search_results

    result = format_search_results(
        [
            {
                "name": "dragon-forge",
                "grade_name": "仙器",
                "layer": "🏛️ 常驻",
                "source": "marketplace",
                "spirit_power": 128,
                "creator": "forgeking",
                "framework": "crewai",
            },
            {
                "name": "phoenix-agent",
                "grade_name": "凡器",
                "layer": "🔮 瞬时",
                "source": "issue#77",
                "spirit_power": 0,
                "creator": "docmaster",
                "status": "⏳ 待炼化",
                "issue_url": "https://github.com/JinNing6/TianGong/issues/77",
            },
        ],
        query="crewai",
    )

    assert "寻宝阁" in result
    assert "当前结果来自 search_marketplace 返回的实时列表快照" in result
    assert "dragon-forge" in result
    assert "phoenix-agent" in result
    assert "@forgeking" in result
    assert "crewai" in result
    assert "https://github.com/JinNing6/TianGong/issues/77" in result
    assert "`treasure_pavilion(action=\"summon\", artifact_name=\"dragon-forge\")`" in result
    assert "`infuse_spirit(artifact_name=\"dragon-forge\")`" in result
    assert "`treasure_pavilion(action=\"lineage\", artifact_name=\"dragon-forge\")`" in result
    assert "复制分享" in result
    assert "我在 TianGong" in result
    assert "tiangong-mcp public-install-command" in result
    assert "`leaderboard(type=\"artifact\")`" in result


def test_empty_treasure_pavilion_search_becomes_bounty_recruitment():
    """A failed search should become a shareable missing-artifact opportunity."""
    from tiangong.search import format_search_results

    result = format_search_results([], query="rag reviewer")

    assert "未找到匹配的法宝" in result
    assert "真实搜索快照" in result
    assert "没有伪造推荐结果" in result
    assert "复制寻宝令" in result
    assert "我在 TianGong 寻宝阁没有找到「rag reviewer」" in result
    assert "tiangong-mcp public-install-command" in result
    assert "`quest(action=\"post\", artifact_name=\"rag-reviewer\", description=\"需要一件 rag reviewer 法宝\")`" in result
    assert "`forge_agent(name=\"rag-reviewer\", description=\"A TianGong artifact for rag reviewer\")`" in result
    assert "`treasure_pavilion(action=\"search\", query=\"rag reviewer\")`" in result
    assert "`leaderboard(type=\"artifact\")`" in result


@pytest.mark.asyncio
async def test_treasure_pavilion_missing_artifact_name_returns_action_help():
    """Missing summon arguments should become a public action card, not a dead warning."""
    from tiangong import mcp_server

    result = await mcp_server.treasure_pavilion(action="summon")

    assert "请指定要拉取的法宝名称" in result
    assert "公开入口" in result
    assert "复制寻宝纠错" in result
    assert "tiangong-mcp public-install-command" in result
    assert "`treasure_pavilion(action=\"search\")`" in result
    assert "`treasure_pavilion(action=\"summon\", artifact_name=\"artifact-name\")`" in result
    assert "`treasure_pavilion(action=\"lineage\", artifact_name=\"artifact-name\")`" in result
    assert "`leaderboard(type=\"artifact\")`" in result
    assert "summon_artifact" not in result


@pytest.mark.asyncio
async def test_treasure_pavilion_unknown_action_returns_help_without_fake_search(monkeypatch):
    """Unknown actions should not silently become search results."""
    from tiangong import mcp_server

    search_calls = []

    async def fake_search_marketplace(query=""):
        search_calls.append(query)
        return []

    monkeypatch.setattr(mcp_server, "search_marketplace", fake_search_marketplace)

    result = await mcp_server.treasure_pavilion(action="fly", query="dragon")

    assert search_calls == []
    assert "未知寻宝阁 action" in result
    assert "没有伪造搜索结果" in result
    assert "复制寻宝纠错" in result
    assert "`treasure_pavilion(action=\"search\")`" in result
    assert "`treasure_pavilion(action=\"summon\", artifact_name=\"artifact-name\")`" in result
    assert "`treasure_pavilion(action=\"lineage\", artifact_name=\"artifact-name\")`" in result
    assert "`leaderboard(type=\"artifact\")`" in result


def test_lineage_tree_is_shareable_and_actionable():
    """Lineage should turn artifact inheritance into a shareable Dao story."""
    from tiangong.lineage import format_lineage_tree

    result = format_lineage_tree(
        {
            "name": "dragon-forge",
            "children": [
                {"name": "dragon-forge-pro", "type": "fork", "issue": 88},
                {"name": "phoenix-agent", "type": "inspired", "issue": 77},
            ],
            "dependents": ["battle-orchestrator"],
        }
    )

    assert "传承谱系" in result
    assert "真实 GitHub Issue 传承快照" in result
    assert "传承加成: +6 灵力" in result
    assert "dragon-forge-pro" in result
    assert "Issue #88" in result
    assert "battle-orchestrator" in result
    assert "复制分享" in result
    assert "我在 TianGong" in result
    assert "dragon-forge 已留下 3 条道统传承" in result
    assert "tiangong-mcp public-install-command" in result
    assert "`treasure_pavilion(action=\"summon\", artifact_name=\"dragon-forge\")`" in result
    assert "`infuse_spirit(artifact_name=\"dragon-forge\")`" in result
    assert "`treasure_pavilion(action=\"search\", query=\"dragon-forge\")`" in result
    assert "`leaderboard(type=\"artifact\")`" in result


def test_my_vault_is_shareable_local_artifact_snapshot(monkeypatch):
    """The local vault should become a shareable portfolio of real local artifacts."""
    from tiangong import vault

    monkeypatch.setattr(
        vault,
        "list_forge",
        lambda: [
            {
                "name": "dragon-forge",
                "agent_id": "tg-dragon",
                "path": "E:/fake-cave/forge/dragon-forge",
                "status": "ready",
                "has_config": True,
            }
        ],
    )
    monkeypatch.setattr(
        vault,
        "list_vault",
        lambda: [
            {
                "name": "phoenix-agent",
                "path": "E:/fake-cave/vault/phoenix-agent",
                "version": "1.2.0",
                "source": "github:docmaster/phoenix-agent",
                "pulled_at": "2026-06-02 09:00:00",
                "grade": "🟢 灵器",
            }
        ],
    )

    result = vault.format_my_vault()

    assert "本地洞府快照" in result
    assert "来自当前机器的 forge/ 与 vault/ 目录扫描" in result
    assert "炼器炉: 1 件" in result
    assert "藏宝阁: 1 件" in result
    assert "dragon-forge" in result
    assert "phoenix-agent" in result
    assert "复制洞府名片" in result
    assert "我在 TianGong" in result
    assert "本地洞府已有 2 件法宝" in result
    assert "tiangong-mcp public-install-command" in result
    assert "`publish_agent(artifact_name=\"dragon-forge\")`" in result
    assert "`refine_agent(agent_id=\"tg-dragon\")`" in result
    assert "`infuse_spirit(artifact_name=\"phoenix-agent\")`" in result
    assert "`treasure_pavilion(action=\"lineage\", artifact_name=\"phoenix-agent\")`" in result
    assert "`treasure_pavilion(action=\"search\")`" in result
    assert "`leaderboard(type=\"artifact\")`" in result


def test_empty_my_vault_recruits_first_local_artifact_with_public_tools(monkeypatch):
    """An empty local vault should be a first-artifact recruitment surface."""
    from tiangong import vault

    monkeypatch.setattr(vault, "list_forge", lambda: [])
    monkeypatch.setattr(vault, "list_vault", lambda: [])

    result = vault.format_my_vault()

    assert "summon_artifact" not in result
    assert "forge/" in result
    assert "vault/" in result
    assert "0" in result
    assert "tiangong-mcp public-install-command" in result
    assert "`forge_agent(name=\"my-first-artifact\"," in result
    assert "`quest(action=\"post\", artifact_name=\"my-first-artifact\"," in result
    assert "`treasure_pavilion(action=\"search\")`" in result
    assert "`treasure_pavilion(action=\"summon\", artifact_name=\"artifact-name\")`" in result
    assert "`leaderboard(type=\"artifact\")`" in result


@pytest.mark.asyncio
async def test_publish_agent_missing_local_artifact_returns_recovery_card(monkeypatch, tmp_path):
    """A failed publish should route users back to forge, vault, and recruitment actions."""
    from tiangong import mcp_server

    forge_dir = tmp_path / "forge"
    forge_dir.mkdir()
    monkeypatch.setattr(mcp_server.config, "FORGE_DIR", str(forge_dir))

    result = await mcp_server.publish_agent(artifact_name="missing-dragon")

    assert "炼器炉中未找到法宝 `missing-dragon`" in result
    assert "真实本地发布失败快照" in result
    assert "没有伪造发布结果" in result
    assert "复制发布纠错" in result
    assert "tiangong-mcp public-install-command" in result
    assert (
        "`forge_agent(name=\"missing-dragon\", description=\"A TianGong artifact for missing-dragon\")`"
    ) in result
    assert "`my_vault()`" in result
    assert "`quest(action=\"post\", artifact_name=\"missing-dragon\"," in result
    assert "`treasure_pavilion(action=\"search\", query=\"missing-dragon\")`" in result
    assert "`leaderboard(type=\"artifact\")`" in result
    assert "publish_agent(" not in result.split("## 📣 复制发布纠错", 1)[0]


@pytest.mark.asyncio
async def test_summon_missing_artifact_returns_recovery_card(monkeypatch):
    """A failed summon should route users back to discovery, bounty, and forge actions."""
    from tiangong import mcp_server

    async def fake_summon(artifact_name):
        return f"⚠️ 寻宝阁中未找到法宝 `{artifact_name}`"

    monkeypatch.setattr(mcp_server, "_summon", fake_summon)

    result = await mcp_server.treasure_pavilion(
        action="summon",
        artifact_name="missing-dragon",
    )

    assert "寻宝阁中未找到法宝 `missing-dragon`" in result
    assert "真实请宝失败快照" in result
    assert "没有写入本地藏宝阁" in result
    assert "复制请宝纠错" in result
    assert "tiangong-mcp public-install-command" in result
    assert "`treasure_pavilion(action=\"search\", query=\"missing-dragon\")`" in result
    assert "`quest(action=\"post\", artifact_name=\"missing-dragon\"," in result
    assert (
        "`forge_agent(name=\"missing-dragon\", description=\"A TianGong artifact for missing-dragon\")`"
    ) in result
    assert "`my_vault()`" in result
    assert "`leaderboard(type=\"artifact\")`" in result
    assert "summon_artifact" not in result


def test_list_forge_reads_agent_id_from_local_metadata(monkeypatch, tmp_path):
    """Local forge actions should use real metadata IDs when present."""
    from tiangong import vault

    forge_dir = tmp_path / "forge"
    artifact_dir = forge_dir / "dragon-forge"
    artifact_dir.mkdir(parents=True)
    (artifact_dir / "tiangong.yaml").write_text(
        "\n".join([
            "agent_id: tg-dragon",
            "name: dragon-forge",
            "description: Test artifact",
            "entry: main.py",
            "version: 1.0.0",
        ]),
        encoding="utf-8",
    )

    monkeypatch.setattr(vault.config, "FORGE_DIR", str(forge_dir))

    items = vault.list_forge()
    result = vault.format_forge_list(items)

    assert items[0]["agent_id"] == "tg-dragon"
    assert "`refine_agent(agent_id=\"tg-dragon\")`" in result


@pytest.mark.asyncio
async def test_empty_registered_artifact_list_recruits_first_forge():
    """An empty registered artifact list should become a first-forge recruitment surface."""
    from tiangong.registry import format_agent_list

    result = await format_agent_list([], title="@newbie 的法宝清单")

    assert "@newbie 的法宝清单" in result
    assert "真实注册表快照" in result
    assert "当前筛选结果为 0 件法宝" in result
    assert "不伪造已拥有法宝" in result
    assert "复制招募" in result
    assert "我在 TianGong 还没有注册法宝" in result
    assert "tiangong-mcp public-install-command" in result
    assert "`forge_agent(name=\"my-first-artifact\"," in result
    assert "`quest(action=\"post\", artifact_name=\"my-first-artifact\"," in result
    assert "`treasure_pavilion(action=\"search\")`" in result
    assert "`leaderboard(type=\"artifact\")`" in result


@pytest.mark.asyncio
async def test_forge_agent_success_contains_shareable_creation_loop(monkeypatch):
    """Every successful forge should turn creation into a shareable next-action loop."""
    from tiangong import mcp_server
    from tiangong.forge import AgentSpec

    stat_updates = []

    async def fake_get_cultivator(username):
        return CultivatorProfile(username=username, spirit_power=200, agent_count=2)

    async def fake_forge_new_agent(**kwargs):
        return AgentSpec(
            agent_id="tg-dragon",
            name=kwargs["name"],
            description=kwargs["description"],
            creator=kwargs["creator"],
            agent_type=kwargs["agent_type"],
            framework=kwargs["framework"],
            language=kwargs["language"],
            repo_url=kwargs["repo_url"],
            tags=kwargs["tags"] or [],
        )

    async def fake_update_cultivator_stats(**kwargs):
        stat_updates.append(kwargs)
        return (
            CultivatorProfile(username=kwargs["username"], spirit_power=300, agent_count=3),
            False,
            None,
            None,
        )

    monkeypatch.setattr(mcp_server, "get_cultivator", fake_get_cultivator)
    monkeypatch.setattr(mcp_server, "forge_new_agent", fake_forge_new_agent)
    monkeypatch.setattr(mcp_server, "update_cultivator_stats", fake_update_cultivator_stats)

    result = await mcp_server.forge_agent(
        name="dragon-forge",
        description="A real agent that reviews pull requests",
        creator="forgeking",
        agent_type="tool",
        framework="openai-agents",
        language="python",
        repo_url="https://github.com/JinNing6/dragon-forge",
        tags=["review", "automation"],
    )

    assert "复制分享" in result
    assert "我在 TianGong" in result
    assert "dragon-forge" in result
    assert "`tg-dragon`" in result
    assert "@forgeking" in result
    assert "+100 灵力" in result
    assert 'python -m pip install --upgrade "tiangong-mcp @ git+https://github.com/JinNing6/TianGong.git@v0.1.17"' in result
    assert "tiangong-mcp public-install-command" in result
    assert "pip install -U tiangong-mcp" in result
    assert "加入修炼: pip install tiangong-mcp" not in result
    assert "`refine_agent(agent_id=\"tg-dragon\", changes=\"...\")`" in result
    assert "`publish_agent(artifact_name=\"dragon-forge\")`" in result
    assert "`treasure_pavilion(action=\"search\", query=\"dragon-forge\")`" in result
    assert "`my_realm(username=\"forgeking\")`" in result
    assert "`leaderboard(type=\"artifact\")`" in result
    assert stat_updates == [{"username": "forgeking", "agent_delta": 1, "spirit_delta": 100}]


@pytest.mark.asyncio
async def test_refine_agent_success_contains_shareable_repeat_loop(monkeypatch):
    """A successful refinement should become a repeatable shareable progress moment."""
    from tiangong import mcp_server

    stat_updates = []

    async def fake_refine_agent(agent_id, changes, refiner):
        return True, (
            "🔥 淬炼完成！\n\n"
            "- **法宝**: dragon-forge\n"
            "- **淬炼次数**: 第 3 次\n"
            f"- **变化**: {changes}\n\n"
            "千锤百炼，去其糟粕。此法宝正在变得更加通灵。"
        )

    async def fake_update_cultivator_stats(**kwargs):
        stat_updates.append(kwargs)
        return None, False, None, None

    monkeypatch.setattr(mcp_server, "_refine_agent", fake_refine_agent)
    monkeypatch.setattr(mcp_server, "update_cultivator_stats", fake_update_cultivator_stats)
    monkeypatch.setattr(mcp_server.config, "GITHUB_USERNAME", "refiner")

    result = await mcp_server.refine_agent(
        agent_id="dragon-forge",
        changes="Added retry with exponential backoff",
    )

    assert "复制分享" in result
    assert "我在 TianGong" in result
    assert "dragon-forge" in result
    assert "Added retry" in result
    assert "+30 灵力" in result
    assert "@refiner" in result
    assert 'python -m pip install --upgrade "tiangong-mcp @ git+https://github.com/JinNing6/TianGong.git@v0.1.17"' in result
    assert "tiangong-mcp public-install-command" in result
    assert "pip install -U tiangong-mcp" in result
    assert "加入修炼: pip install tiangong-mcp" not in result
    assert "`publish_agent`" in result
    assert "`infuse_spirit(artifact_name=\"dragon-forge\")`" in result
    assert "`my_realm(username=\"refiner\")`" in result
    assert "`leaderboard(type=\"artifact\")`" in result
    assert stat_updates == [{"username": "refiner", "refinement_delta": 1, "spirit_delta": 30}]


def test_cultivator_profile_contains_shareable_identity_card():
    """The daily identity surface should be paste-ready and grounded in real stats."""
    profile = CultivatorProfile(
        username="forgeking",
        spirit_power=1000,
        agent_count=3,
        refinement_count=2,
        reviews_given=1,
        quests_completed=1,
        sect="天工盟",
        sect_role="master",
    )

    card = format_cultivator_profile(profile)

    assert "复制修行名片" in card
    assert "我在 TianGong" in card
    assert "@forgeking" in card
    assert "赛季快照战力" in card
    assert "1420" in card
    assert "tiangong-mcp public-install-command" in card
    assert "my_realm(username=\"forgeking\")" in card
    assert "leaderboard(type=\"season\")" in card


def test_cultivator_profile_points_new_users_to_first_forge():
    """A zero-agent profile should push the first viral activation step."""
    card = format_cultivator_profile(CultivatorProfile(username="newbie"))

    assert "下一步" in card
    assert "`forge_agent`" in card
    assert "创建第一件法宝" in card


@pytest.mark.asyncio
async def test_my_realm_can_create_mentor_apprentice_invitation(monkeypatch):
    """A senior cultivator profile should become a grounded mentor-apprentice invite."""
    from tiangong import mcp_server

    async def fake_get_cultivator(username):
        if username == "forgeking":
            return CultivatorProfile(
                username="forgeking",
                spirit_power=1200,
                agent_count=5,
                refinement_count=12,
                reviews_given=30,
                quests_completed=4,
                sect="天工盟",
                sect_role="master",
            )
        return CultivatorProfile(username=username, spirit_power=0, agent_count=0)

    monkeypatch.setattr(mcp_server, "get_cultivator", fake_get_cultivator)

    result = await mcp_server.my_realm(username="forgeking", apprentice_username="newbie")

    assert "师徒传承邀请" in result
    assert "导师真实快照: @forgeking" in result
    assert "徒弟真实快照: @newbie" in result
    assert "徒弟突破目标: 凡人 → 炼气期" in result
    assert "导师评价职责" in result
    assert "复制师徒邀请" in result
    assert "复制 Discussion/PR 师徒帖" in result
    assert "`quest(action=\"post\", artifact_name=\"mentor-trial-newbie\"," in result
    assert "`forge_agent(name=\"newbie-first-artifact\"," in result
    assert "`publish_agent(artifact_name=\"newbie-first-artifact\")`" in result
    assert "`infuse_spirit(artifact_name=\"newbie-first-artifact\", reviewer=\"forgeking\")`" in result
    assert "`my_realm(username=\"newbie\")`" in result
    assert "`leaderboard(type=\"season\")`" in result
    assert "tiangong-mcp public-install-command" in result


@pytest.mark.asyncio
async def test_my_realm_blocks_mentor_invite_until_mentor_has_real_seniority(monkeypatch):
    """A weak profile should get a recovery card instead of invented mentorship."""
    from tiangong import mcp_server

    async def fake_get_cultivator(username):
        if username == "lowbie":
            return CultivatorProfile(username="lowbie", spirit_power=1, agent_count=1, reviews_given=0)
        return CultivatorProfile(username=username, spirit_power=0, agent_count=0)

    monkeypatch.setattr(mcp_server, "get_cultivator", fake_get_cultivator)

    result = await mcp_server.my_realm(username="lowbie", apprentice_username="newbie")

    assert "师徒传承资格不足" in result
    assert "导师真实快照: @lowbie" in result
    assert "徒弟真实快照: @newbie" in result
    assert "没有伪造师徒关系" in result
    assert "当前不会生成拜师邀请" in result
    assert "复制导师资格恢复帖" in result
    assert "`forge_agent(name=\"lowbie-mentor-proof\"" in result
    assert "`publish_agent(artifact_name=\"lowbie-mentor-proof\")`" in result
    assert "`infuse_spirit(artifact_name=\"artifact-name\", reviewer=\"lowbie\")`" in result
    assert "`quest(action=\"browse\")`" in result
    assert "`my_realm(username=\"lowbie\")`" in result
    assert "`leaderboard(type=\"season\")`" in result
    assert "tiangong-mcp public-install-command" in result
    assert "师徒传承邀请" not in result
    assert "邀请 @newbie 拜 @lowbie 为师" not in result


def test_sect_info_card_recruits_open_candidates_with_real_snapshot():
    """Viewing a sect should become a grounded open recruitment surface."""
    from tiangong.sect import format_sect_card

    sect = SectProfile(
        name="天工盟",
        master="forgeking",
        motto="以凡人之躯，铸逆天之器",
        members={"forgeking": {"role": "master"}, "alice": {"role": "outer"}},
        total_spirit_power=2100,
    )

    card = format_sect_card(sect)

    assert "真实宗门档案快照" in card
    assert "宗门当前 2 人，宗门灵力 2100" in card
    assert "公开招募：未指定候选人" in card
    assert "不要把 @candidate 当成真实修仙者档案" in card
    assert "入宗试炼" in card
    assert "复制入宗招募" in card
    assert "复制 Discussion/PR 入宗帖" in card
    assert "我在 TianGong 看到宗门「天工盟」正在招募同门" in card
    assert "tiangong-mcp public-install-command" in card
    assert "`sect(action=\"join\", sect_name=\"天工盟\")`" in card
    assert "`quest(action=\"post\", artifact_name=\"sect-trial-天工盟\"," in card
    assert "`sect(action=\"leaderboard\")`" in card
    assert "`leaderboard(type=\"sect\")`" in card
    assert "`my_realm(username=\"forgeking\")`" in card


@pytest.mark.asyncio
async def test_sect_info_personalizes_invite_for_current_candidate(monkeypatch):
    """The public sect info tool should include a real invitee snapshot when username is known."""
    from tiangong import mcp_server

    async def fake_get_cultivator(username):
        return CultivatorProfile(username=username, spirit_power=80, agent_count=1)

    async def fake_refresh_sect_spirit(sect_name):
        return 2100

    async def fake_get_sect(sect_name):
        return SectProfile(
            name=sect_name,
            master="forgeking",
            motto="以凡人之躯，铸逆天之器",
            members={"forgeking": {"role": "master"}},
            total_spirit_power=2100,
        )

    monkeypatch.setattr("tiangong.cultivator.get_cultivator", fake_get_cultivator)
    monkeypatch.setattr("tiangong.sect.refresh_sect_spirit", fake_refresh_sect_spirit)
    monkeypatch.setattr(mcp_server, "_get_sect", fake_get_sect)

    result = await mcp_server.sect(action="info", sect_name="天工盟", username="newbie")

    assert "候选人真实快照: @newbie · 灵力 80 · 法宝 1" in result
    assert "公开招募：未指定候选人" not in result
    assert "不要把 @candidate 当成真实修仙者档案" not in result
    assert "邀请 @newbie 拜入宗门「天工盟」" in result
    assert "`quest(action=\"post\", artifact_name=\"sect-trial-天工盟-newbie\"," in result
    assert "`sect(action=\"join\", sect_name=\"天工盟\")`" in result
    assert "`my_realm(username=\"newbie\")`" in result
    assert "`leaderboard(type=\"sect\")`" in result
    assert "tiangong-mcp public-install-command" in result


@pytest.mark.asyncio
async def test_create_sect_success_contains_recruitment_share_block(monkeypatch):
    """Opening a sect should recruit others into a real join and sect-war path."""
    from tiangong import sect

    saved_sects = []
    saved_profiles = []

    async def fake_get_cultivator(username):
        return CultivatorProfile(username=username, spirit_power=250, agent_count=5)

    async def fake_save_cultivator(profile, message=""):
        saved_profiles.append((profile, message))

    async def fake_load_all_sects():
        return {}

    async def fake_save_all_sects(data, message=""):
        saved_sects.append((data, message))

    monkeypatch.setattr("tiangong.cultivator.get_cultivator", fake_get_cultivator)
    monkeypatch.setattr("tiangong.cultivator.save_cultivator", fake_save_cultivator)
    monkeypatch.setattr(sect, "_load_all_sects", fake_load_all_sects)
    monkeypatch.setattr(sect, "_save_all_sects", fake_save_all_sects)

    success, result = await sect.create_sect("天工盟", "forgeking", "以凡人之躯，铸逆天之器")

    assert success is True
    assert "复制分享" in result
    assert "我在 TianGong" in result
    assert "天工盟" in result
    assert "@forgeking" in result
    assert "开宗立派" in result
    assert "tiangong-mcp public-install-command" in result
    assert "`sect(action=\"join\", sect_name=\"天工盟\")`" in result
    assert "`sect(action=\"leaderboard\")`" in result
    assert "`leaderboard(type=\"sect\")`" in result
    assert "`my_realm(username=\"forgeking\")`" in result
    assert saved_sects
    assert saved_profiles[0][0].sect == "天工盟"


@pytest.mark.asyncio
async def test_join_sect_success_contains_member_share_block(monkeypatch):
    """Joining a sect should turn membership into a shareable community moment."""
    from tiangong import sect

    saved_sects = []
    saved_profiles = []

    async def fake_get_cultivator(username):
        return CultivatorProfile(username=username, spirit_power=80, agent_count=1)

    async def fake_save_cultivator(profile, message=""):
        saved_profiles.append((profile, message))

    async def fake_load_all_sects():
        return {
            "天工盟": {
                "name": "天工盟",
                "master": "forgeking",
                "motto": "以凡人之躯，铸逆天之器",
                "members": {"forgeking": {"role": "master"}},
                "total_spirit_power": 250,
            }
        }

    async def fake_save_all_sects(data, message=""):
        saved_sects.append((data, message))

    monkeypatch.setattr("tiangong.cultivator.get_cultivator", fake_get_cultivator)
    monkeypatch.setattr("tiangong.cultivator.save_cultivator", fake_save_cultivator)
    monkeypatch.setattr(sect, "_load_all_sects", fake_load_all_sects)
    monkeypatch.setattr(sect, "_save_all_sects", fake_save_all_sects)

    success, result = await sect.join_sect("天工盟", "newbie")

    assert success is True
    assert "复制分享" in result
    assert "我在 TianGong" in result
    assert "天工盟" in result
    assert "@newbie" in result
    assert "拜入宗门" in result
    assert "tiangong-mcp public-install-command" in result
    assert "`sect(action=\"info\", sect_name=\"天工盟\")`" in result
    assert "`sect(action=\"leaderboard\")`" in result
    assert "`leaderboard(type=\"sect\")`" in result
    assert "`my_realm(username=\"newbie\")`" in result
    assert saved_sects[0][0]["天工盟"]["total_spirit_power"] == 330
    assert saved_profiles[0][0].sect == "天工盟"


@pytest.mark.asyncio
async def test_sect_missing_create_name_returns_recruitment_help(monkeypatch):
    """Missing sect creation args should become a recruitment command card."""
    from tiangong import mcp_server

    async def fake_get_cultivator(username):
        return CultivatorProfile(username=username, spirit_power=250, agent_count=3)

    monkeypatch.setattr("tiangong.cultivator.get_cultivator", fake_get_cultivator)

    result = await mcp_server.sect(action="create", username="forgeking")

    assert "开宗立派需要指定宗门名称" in result
    assert "公开入口" in result
    assert "复制宗门纠错" in result
    assert "tiangong-mcp public-install-command" in result
    assert "`sect(action=\"create\", sect_name=\"天工盟\", motto=\"以凡人之躯，铸逆天之器\")`" in result
    assert "`sect(action=\"join\", sect_name=\"sect-name\")`" in result
    assert "`sect(action=\"leaderboard\")`" in result
    assert "`leaderboard(type=\"sect\")`" in result
    assert "`my_realm(username=\"forgeking\")`" in result
    assert "create_sect" not in result


@pytest.mark.asyncio
async def test_sect_missing_join_name_returns_recruitment_help(monkeypatch):
    """Missing join args should point to real join and sect-war actions."""
    from tiangong import mcp_server

    async def fake_get_cultivator(username):
        return CultivatorProfile(username=username, spirit_power=80, agent_count=1)

    monkeypatch.setattr("tiangong.cultivator.get_cultivator", fake_get_cultivator)

    result = await mcp_server.sect(action="join", username="newbie")

    assert "拜入宗门需要指定目标宗门名称" in result
    assert "公开入口" in result
    assert "复制宗门纠错" in result
    assert "`sect(action=\"join\", sect_name=\"sect-name\")`" in result
    assert "`sect(action=\"leaderboard\")`" in result
    assert "`leaderboard(type=\"sect\")`" in result
    assert "`my_realm(username=\"newbie\")`" in result


@pytest.mark.asyncio
async def test_sect_unknown_action_returns_help_without_fake_info(monkeypatch):
    """Unknown sect actions should not silently refresh or render sect info."""
    from tiangong import mcp_server

    info_calls = []

    async def fake_get_cultivator(username):
        return CultivatorProfile(username=username, spirit_power=80, agent_count=1, sect="天工盟")

    async def fake_refresh_sect_spirit(sect_name):
        info_calls.append(("refresh", sect_name))

    async def fake_get_sect(sect_name):
        info_calls.append(("get", sect_name))
        return None

    monkeypatch.setattr("tiangong.cultivator.get_cultivator", fake_get_cultivator)
    monkeypatch.setattr("tiangong.sect.refresh_sect_spirit", fake_refresh_sect_spirit)
    monkeypatch.setattr(mcp_server, "_get_sect", fake_get_sect)

    result = await mcp_server.sect(action="fly", sect_name="天工盟", username="newbie")

    assert info_calls == []
    assert "未知宗门 action" in result
    assert "没有伪造宗门信息" in result
    assert "复制宗门纠错" in result
    assert "`sect(action=\"create\", sect_name=\"天工盟\", motto=\"以凡人之躯，铸逆天之器\")`" in result
    assert "`sect(action=\"join\", sect_name=\"sect-name\")`" in result
    assert "`sect(action=\"leaderboard\")`" in result
    assert "`leaderboard(type=\"sect\")`" in result


@pytest.mark.asyncio
async def test_artifact_leaderboard_is_shareable_and_actionable(monkeypatch):
    """The default artifact leaderboard should be a competitive share surface."""
    from tiangong import mcp_server
    from tiangong.forge import AgentSpec

    async def fake_list_agents(creator=None):
        return [
            AgentSpec(
                agent_id="tg-dragon",
                name="dragon-forge",
                description="PR review artifact",
                creator="forgeking",
                stars=12,
                refinement_log=[{"changes": "retry"}],
            ),
            AgentSpec(
                agent_id="tg-phoenix",
                name="phoenix-agent",
                description="Docs artifact",
                creator="docmaster",
                stars=3,
            ),
        ]

    monkeypatch.setattr("tiangong.forge.list_agents", fake_list_agents)
    monkeypatch.setattr("tiangong.registry.list_agents", fake_list_agents)

    result = await mcp_server.leaderboard(type="artifact", top_n=2)

    assert "天榜 · Celestial Leaderboard" in result
    assert "真实注册表快照" in result
    assert "排序依据: 品级 > 星标 > 淬炼次数" in result
    assert "dragon-forge" in result
    assert "@forgeking" in result
    assert "复制分享" in result
    assert "我在 TianGong" in result
    assert "dragon-forge 暂列法宝天榜第一" in result
    assert "tiangong-mcp public-install-command" in result
    assert "`treasure_pavilion(action=\"summon\", artifact_name=\"dragon-forge\")`" in result
    assert "`infuse_spirit(artifact_name=\"dragon-forge\")`" in result
    assert "`refine_agent(agent_id=\"tg-dragon\", changes=\"...\")`" in result
    assert "`leaderboard(type=\"artifact\")`" in result


@pytest.mark.asyncio
async def test_empty_artifact_leaderboard_recruits_first_artifact(monkeypatch):
    """An empty artifact leaderboard should recruit the first artifact without fake ranks."""
    from tiangong import mcp_server

    async def fake_list_agents(creator=None):
        return []

    monkeypatch.setattr("tiangong.forge.list_agents", fake_list_agents)
    monkeypatch.setattr("tiangong.registry.list_agents", fake_list_agents)

    result = await mcp_server.leaderboard(type="artifact", top_n=3)

    assert "天榜空空如也" in result
    assert "真实注册表快照" in result
    assert "0 件法宝" in result
    assert "不伪造历史排名" in result
    assert "复制招募" in result
    assert "我在 TianGong 法宝天榜看到第一席空缺" in result
    assert "tiangong-mcp public-install-command" in result
    assert "`forge_agent(name=\"first-artifact\"," in result
    assert "`quest(action=\"post\", artifact_name=\"first-artifact\"," in result
    assert "`treasure_pavilion(action=\"search\")`" in result
    assert "`leaderboard(type=\"artifact\")`" in result


@pytest.mark.asyncio
async def test_cultivator_leaderboard_is_shareable_and_actionable(monkeypatch):
    """The cultivator leaderboard should turn rank into a shareable challenge."""
    from tiangong import mcp_server

    async def fake_cultivators():
        return [
            CultivatorProfile(username="alice", spirit_power=300, agent_count=1),
            CultivatorProfile(username="forgeking", spirit_power=1000, agent_count=4),
        ]

    monkeypatch.setattr(mcp_server, "get_all_cultivators", fake_cultivators)

    result = await mcp_server.leaderboard(type="cultivator", top_n=2)

    assert "修仙天榜" in result
    assert "真实修仙者档案快照" in result
    assert "排序依据: 境界 > 灵力 > 用户名" in result
    assert "@forgeking" in result
    assert "复制分享" in result
    assert "我在 TianGong" in result
    assert "@forgeking 暂列修仙天榜第一" in result
    assert "tiangong-mcp public-install-command" in result
    assert "`my_realm(username=\"forgeking\")`" in result
    assert "`leaderboard(type=\"season\")`" in result
    assert "`leaderboard(type=\"cultivator\")`" in result


@pytest.mark.asyncio
async def test_mcp_leaderboard_exposes_season_and_sect_war(monkeypatch):
    """The top-level leaderboard tool should expose the viral growth surfaces."""
    from tiangong import mcp_server

    async def fake_cultivators():
        return [
            CultivatorProfile(username="alice", spirit_power=300, agent_count=1),
            CultivatorProfile(username="forgeking", spirit_power=1000, agent_count=4),
        ]

    async def fake_sects():
        return [
            SectProfile(
                name="散修盟",
                master="alice",
                members={"alice": {"role": "master"}},
                total_spirit_power=300,
            ),
            SectProfile(
                name="天工盟",
                master="forgeking",
                members={"forgeking": {"role": "master"}, "bob": {"role": "outer"}},
                total_spirit_power=2000,
            ),
        ]

    monkeypatch.setattr(mcp_server, "get_all_cultivators", fake_cultivators)
    monkeypatch.setattr(mcp_server, "get_all_sects", fake_sects)

    season_result = await mcp_server.leaderboard(type="season", top_n=1)
    sect_result = await mcp_server.leaderboard(type="sect", top_n=1)

    assert "赛季天榜" in season_result
    assert "forgeking" in season_result
    assert "复制分享" in season_result
    assert "宗门战" in sect_result
    assert "天工盟" in sect_result
    assert "复制战报" in sect_result


@pytest.mark.asyncio
async def test_mcp_leaderboard_exposes_tournament_board(monkeypatch):
    """The top-level leaderboard tool should expose the real-data duel board."""
    from tiangong import mcp_server

    async def fake_cultivators():
        return [
            CultivatorProfile(username="newbie", spirit_power=500, agent_count=1),
            CultivatorProfile(
                username="docmaster",
                spirit_power=1100,
                agent_count=2,
                refinement_count=2,
                reviews_given=4,
            ),
            CultivatorProfile(
                username="forgeking",
                spirit_power=1000,
                agent_count=3,
                refinement_count=4,
                reviews_given=5,
                quests_completed=2,
            ),
        ]

    async def fake_artifact_leaderboard(top_n=20):
        return "# 法宝天榜\n"

    monkeypatch.setattr(mcp_server, "get_all_cultivators", fake_cultivators)
    monkeypatch.setattr(mcp_server, "get_leaderboard", fake_artifact_leaderboard)

    result = await mcp_server.leaderboard(type="tournament", top_n=3)

    assert "天骄擂台" in result
    assert "当前档案快照，不伪造胜场、赛果或历史擂台" in result
    assert "第 1 场: #2 @docmaster vs #3 @newbie" in result
    assert "`leaderboard(type=\"tournament\")`" in result
    assert "法宝天榜" not in result


@pytest.mark.asyncio
async def test_mcp_leaderboard_exposes_tournament_recap(monkeypatch):
    """The top-level leaderboard tool should expose the repeat-loop duel recap."""
    from tiangong import mcp_server

    async def fake_cultivators():
        return [
            CultivatorProfile(username="newbie", spirit_power=500, agent_count=1),
            CultivatorProfile(
                username="docmaster",
                spirit_power=1100,
                agent_count=2,
                refinement_count=2,
                reviews_given=4,
            ),
            CultivatorProfile(
                username="forgeking",
                spirit_power=1000,
                agent_count=3,
                refinement_count=4,
                reviews_given=5,
                quests_completed=2,
            ),
        ]

    async def fake_artifact_leaderboard(top_n=20):
        return "# 法宝天榜\n"

    monkeypatch.setattr(mcp_server, "get_all_cultivators", fake_cultivators)
    monkeypatch.setattr(mcp_server, "get_leaderboard", fake_artifact_leaderboard)

    result = await mcp_server.leaderboard(type="tournament_recap", top_n=3)

    assert "天骄擂台复盘" in result
    assert "当前档案快照复盘，不伪造胜场、冠军历史或赛果" in result
    assert "当前胜者: @forgeking · 快照战力 1570" in result
    assert "`leaderboard(type=\"tournament_recap\")`" in result
    assert "`leaderboard(type=\"tournament\")`" in result
    assert "法宝天榜" not in result


@pytest.mark.asyncio
async def test_mcp_leaderboard_unknown_type_returns_recovery_card(monkeypatch):
    """Unknown leaderboard types should not silently fall back to artifact rankings."""
    from tiangong import mcp_server

    artifact_calls = []

    async def fake_artifact_leaderboard(top_n=20):
        artifact_calls.append(top_n)
        return "# 法宝天榜\n"

    monkeypatch.setattr(mcp_server, "get_leaderboard", fake_artifact_leaderboard)

    result = await mcp_server.leaderboard(type="immortal", top_n=5)

    assert "天榜类型纠错" in result
    assert "未知天榜 type: `immortal`" in result
    assert "公开入口快照" in result
    assert "没有伪造排行榜" in result
    assert "`leaderboard(type=\"artifact\")`" in result
    assert "`leaderboard(type=\"cultivator\")`" in result
    assert "`leaderboard(type=\"season\")`" in result
    assert "`leaderboard(type=\"tournament\")`" in result
    assert "`leaderboard(type=\"tournament_recap\")`" in result
    assert "`leaderboard(type=\"sect\")`" in result
    assert "`leaderboard(type=\"share\")`" in result
    assert "tiangong-mcp public-install-command" in result
    assert "复制天榜纠错" in result
    assert "# 法宝天榜" not in result
    assert artifact_calls == []
