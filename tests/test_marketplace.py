"""
测试 marketplace 模块
"""
from unittest.mock import MagicMock, patch

import pytest

from tiangong.marketplace import publish_agent, summon_artifact, validate_artifact_for_publish


def test_validate_artifact_for_publish(tmp_path):
    """测试法宝发布前的本地校验"""
    artifact_dir = tmp_path / "test_artifact"
    artifact_dir.mkdir()

    # 1. 没有任何文件时
    valid, errors = validate_artifact_for_publish(artifact_dir)
    assert not valid
    assert "❌ 缺少 `tiangong.yaml` 元数据文件" in errors
    assert "❌ 缺少 `README.md` 使用说明" in errors

    # 2. 提供所需文件
    yaml_file = artifact_dir / "tiangong.yaml"
    yaml_file.write_text("name: test\ndescription: Test artifact\nentry: main.py\nversion: 1.0.0", encoding="utf-8")

    readme_file = artifact_dir / "README.md"
    readme_file.write_text("=" * 100, encoding="utf-8")  # 内容大于 100 字符

    entry_file = artifact_dir / "main.py"
    entry_file.write_text("print('hello')", encoding="utf-8")

    valid, errors = validate_artifact_for_publish(artifact_dir)
    assert valid is True
    assert len(errors) == 0


@pytest.mark.asyncio
@patch("tiangong.marketplace.httpx.AsyncClient.post")
@patch("tiangong.marketplace.config")
async def test_publish_agent_success(mock_config, mock_post, tmp_path):
    """测试飞升上界 (使用 mock)"""
    mock_config.FORGE_DIR = str(tmp_path)
    mock_config.GITHUB_TOKEN = "fake_token"
    mock_config.GITHUB_REPO_OWNER = "test"
    mock_config.GITHUB_REPO_NAME = "repo"
    mock_config.GITHUB_USERNAME = "tester"

    # 构造合法的法宝目录
    artifact_name = "mock_artifact"
    artifact_dir = tmp_path / artifact_name
    artifact_dir.mkdir()
    (artifact_dir / "tiangong.yaml").write_text("name: test\ndescription: Test\nentry: main.py\nversion: 1.0.0", encoding="utf-8")
    (artifact_dir / "README.md").write_text("=" * 100, encoding="utf-8")
    (artifact_dir / "main.py").write_text("", encoding="utf-8")

    # Mock HTTP 响应
    mock_resp = MagicMock()
    mock_resp.status_code = 201
    mock_resp.json.return_value = {"number": 42, "html_url": "https://github.com/test/repo/issues/42"}
    mock_post.return_value = mock_resp

    result = await publish_agent(artifact_name)
    assert "✅ 飞升上界成功！" in result
    assert "Issue: #42" in result
    assert "复制分享" in result
    assert "我在 TianGong" in result
    assert "mock_artifact" in result
    assert "https://github.com/test/repo/issues/42" in result
    assert "tiangong-mcp public-install-command" in result
    assert "`treasure_pavilion`" in result
    assert "`infuse_spirit`" in result
    assert "`leaderboard(type=\"artifact\")`" in result
    assert "record_share_attribution" in result
    assert 'contribution="publish"' in result
    assert 'share_url="https://github.com/test/repo/issues/42"' in result


@pytest.mark.asyncio
async def test_summon_artifact_success_contains_shareable_next_actions(monkeypatch, tmp_path):
    """A successful summon should become a shareable appraisal and vault moment."""
    from tiangong import marketplace

    saved_meta = []

    async def fake_fetch_meta(artifact_name):
        return {
            "version": "1.2.3",
            "creator": "forgeking",
            "grade": "🟣 仙器",
        }

    async def fake_download(artifact_name, target_dir):
        return True

    def fake_save_artifact_meta(**kwargs):
        saved_meta.append(kwargs)

    monkeypatch.setattr(marketplace.config, "VAULT_DIR", str(tmp_path / "vault"))
    monkeypatch.setattr(marketplace.config, "GITHUB_REPO_OWNER", "JinNing6")
    monkeypatch.setattr(marketplace.config, "GITHUB_REPO_NAME", "TianGong")
    monkeypatch.setattr(marketplace, "ensure_cave", lambda: None)
    monkeypatch.setattr(marketplace, "check_artifact_exists", lambda artifact_name, location: False)
    monkeypatch.setattr(marketplace, "_fetch_artifact_meta", fake_fetch_meta)
    monkeypatch.setattr(marketplace, "_download_artifact_files", fake_download)
    monkeypatch.setattr(marketplace, "save_artifact_meta", fake_save_artifact_meta)

    result = await summon_artifact("dragon-forge")

    assert "请宝下凡成功" in result
    assert "复制分享" in result
    assert "我在 TianGong" in result
    assert "dragon-forge" in result
    assert "forgeking" in result
    assert "🟣 仙器" in result
    assert "tiangong-mcp public-install-command" in result
    assert "`infuse_spirit(artifact_name=\"dragon-forge\")`" in result
    assert "`my_vault()`" in result
    assert "`leaderboard(type=\"artifact\")`" in result
    assert "record_share_attribution" in result
    assert 'contribution="summon"' in result
    assert 'artifact_name="dragon-forge"' in result
    assert saved_meta[0]["source"] == "github:JinNing6/TianGong"
    assert saved_meta[0]["version"] == "1.2.3"


@pytest.mark.asyncio
async def test_summon_artifact_existing_copy_points_to_real_tools(monkeypatch, tmp_path):
    """Existing local artifacts should not expose internal helper names."""
    from tiangong import marketplace

    monkeypatch.setattr(marketplace.config, "VAULT_DIR", str(tmp_path / "vault"))
    monkeypatch.setattr(marketplace, "ensure_cave", lambda: None)
    monkeypatch.setattr(marketplace, "check_artifact_exists", lambda artifact_name, location: True)

    result = await summon_artifact("dragon-forge")

    assert "已存在于藏宝阁" in result
    assert "banish_artifact" not in result
    assert "`my_vault()`" in result
    assert "`infuse_spirit(artifact_name=\"dragon-forge\")`" in result
    assert "`treasure_pavilion(action=\"search\", query=\"dragon-forge\")`" in result
