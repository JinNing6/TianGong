"""
测试 marketplace 模块
"""
import os
import pytest
from pathlib import Path
from unittest.mock import patch, AsyncMock

from tiangong.marketplace import validate_artifact_for_publish, publish_agent


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

    from unittest.mock import MagicMock
    # Mock HTTP 响应
    mock_resp = MagicMock()
    mock_resp.status_code = 201
    mock_resp.json.return_value = {"number": 42, "html_url": "https://github.com/test/repo/issues/42"}
    mock_post.return_value = mock_resp

    result = await publish_agent(artifact_name)
    assert "✅ 飞升上界成功！" in result
    assert "Issue: #42" in result

