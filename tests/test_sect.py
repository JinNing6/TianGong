"""
⚒️ 天工 TianGong — 宗门系统单元测试
"""
import time
import pytest
from unittest.mock import patch, MagicMock

from tiangong.sect import (
    SECT_GRADES,
    ROLE_MASTER,
    ROLE_ELDER,
    ROLE_INNER,
    ROLE_OUTER,
    SectProfile,
    calculate_sect_grade,
    create_sect,
    join_sect,
    leave_sect,
    manage_sect,
    get_sect,
)
from tiangong.cultivator import CultivatorProfile
from tiangong.config import config


def test_sect_grades():
    """宗门等阶基本属性"""
    assert len(SECT_GRADES) == 5
    assert SECT_GRADES[0].name_cn == "小门派"
    assert SECT_GRADES[-1].name_cn == "超级势力"
    assert SECT_GRADES[-1].spirit_required == 50000


def test_calculate_sect_grade():
    """验证总灵力对应等阶"""
    assert calculate_sect_grade(0).name_cn == "小门派"
    assert calculate_sect_grade(499).name_cn == "小门派"
    assert calculate_sect_grade(500).name_cn == "中等宗门"
    assert calculate_sect_grade(2000).name_cn == "大宗门"
    assert calculate_sect_grade(15000).name_cn == "圣地"
    assert calculate_sect_grade(60000).name_cn == "超级势力"


@pytest.mark.asyncio
@patch("tiangong.sect._load_all_sects")
@patch("tiangong.sect._save_all_sects")
@patch("tiangong.cultivator.get_cultivator")
@patch("tiangong.cultivator.save_cultivator")
async def test_create_sect_success(mock_save_cult, mock_get_cult, mock_save_sects, mock_load_sects):
    """测试创建宗门成功"""
    # 模拟创建者境界达到结丹（level >= 3 需要的灵力）
    creator = CultivatorProfile(username="master_user", spirit_power=100)
    mock_get_cult.return_value = creator
    mock_load_sects.return_value = {}

    success, msg = await create_sect("测试宗门", "master_user", "测试宣言")
    assert success is True
    assert "测试宗门" in msg

    # 验证传入 save_sects 的数据
    saved_data = mock_save_sects.call_args[0][0]
    assert "测试宗门" in saved_data
    assert saved_data["测试宗门"]["master"] == "master_user"
    assert saved_data["测试宗门"]["motto"] == "测试宣言"
    assert "master_user" in saved_data["测试宗门"]["members"]
    assert saved_data["测试宗门"]["members"]["master_user"]["role"] == ROLE_MASTER


@pytest.mark.asyncio
@patch("tiangong.sect._load_all_sects")
@patch("tiangong.cultivator.get_cultivator")
async def test_create_sect_low_realm(mock_get_cult, mock_load_sects):
    """测试境界不够不能创建宗门"""
    # 灵力 0 = 凡人 (level 0) < 3
    creator = CultivatorProfile(username="noob", spirit_power=0)
    mock_get_cult.return_value = creator
    mock_load_sects.return_value = {}

    success, msg = await create_sect("测试宗门", "noob")
    assert success is False
    assert "结丹期" in msg


@pytest.mark.asyncio
@patch("tiangong.sect._load_all_sects")
@patch("tiangong.cultivator.get_cultivator")
async def test_create_sect_duplicate_name(mock_get_cult, mock_load_sects):
    """测试宗门重名"""
    creator = CultivatorProfile(username="master_user", spirit_power=100)
    mock_get_cult.return_value = creator
    # 模拟已有同名宗门
    mock_load_sects.return_value = {"同名宗门": {}}

    success, msg = await create_sect("同名宗门", "master_user")
    assert success is False
    assert "已被占用" in msg


@pytest.mark.asyncio
@patch("tiangong.sect._load_all_sects")
@patch("tiangong.sect._save_all_sects")
@patch("tiangong.cultivator.get_cultivator")
@patch("tiangong.cultivator.save_cultivator")
async def test_join_sect_success(mock_save_cult, mock_get_cult, mock_save_sects, mock_load_sects):
    """测试加入宗门"""
    joiner = CultivatorProfile(username="newbie", spirit_power=10)
    mock_get_cult.return_value = joiner
    
    mock_load_sects.return_value = {
        "测试宗门": {
            "name": "测试宗门",
            "master": "master_user",
            "members": {"master_user": {"role": ROLE_MASTER}},
            "total_spirit_power": 100
        }
    }

    success, msg = await join_sect("测试宗门", "newbie")
    assert success is True
    assert "拜入宗门成功" in msg
    
    saved_data = mock_save_sects.call_args[0][0]
    assert "newbie" in saved_data["测试宗门"]["members"]
    assert saved_data["测试宗门"]["members"]["newbie"]["role"] == ROLE_OUTER
    assert saved_data["测试宗门"]["total_spirit_power"] == 110  # 100 + 10


@pytest.mark.asyncio
@patch("tiangong.sect._load_all_sects")
@patch("tiangong.sect._save_all_sects")
@patch("tiangong.cultivator.get_cultivator")
@patch("tiangong.cultivator.save_cultivator")
async def test_leave_sect_success(mock_save_cult, mock_get_cult, mock_save_sects, mock_load_sects):
    """测试退出宗门"""
    leaver = CultivatorProfile(username="user1", spirit_power=10, sect="测试宗门", sect_role=ROLE_OUTER)
    mock_get_cult.return_value = leaver
    
    mock_load_sects.return_value = {
        "测试宗门": {
            "name": "测试宗门",
            "master": "master_user",
            "members": {
                "master_user": {"role": ROLE_MASTER},
                "user1": {"role": ROLE_OUTER}
            },
            "total_spirit_power": 110
        }
    }

    success, msg = await leave_sect("user1")
    assert success is True
    assert "退出宗门" in msg
    
    # 确认宗门成员移除且总灵力扣除
    saved_sects = mock_save_sects.call_args[0][0]
    assert "user1" not in saved_sects["测试宗门"]["members"]
    assert saved_sects["测试宗门"]["total_spirit_power"] == 100
    
    # 确认个人档案更新了冷却期
    saved_profile = mock_save_cult.call_args[0][0]
    assert saved_profile.sect == ""
    assert saved_profile.sect_role == ""
    assert saved_profile.sect_cooldown > time.time()


@pytest.mark.asyncio
@patch("tiangong.sect._load_all_sects")
@patch("tiangong.cultivator.get_cultivator")
async def test_join_on_cooldown(mock_get_cult, mock_load_sects):
    """测试冷却期内不能加入新宗门"""
    joiner = CultivatorProfile(username="newbie", sect_cooldown=time.time() + 3600)  # 在冷却中
    mock_get_cult.return_value = joiner
    mock_load_sects.return_value = {"目标宗门": {"name": "目标宗门", "members": {}}}

    success, msg = await join_sect("目标宗门", "newbie")
    assert success is False
    assert "冷却期" in msg


@pytest.mark.asyncio
@patch("tiangong.sect._load_all_sects")
@patch("tiangong.sect._save_all_sects")
@patch("tiangong.cultivator.get_cultivator")
@patch("tiangong.cultivator.save_cultivator")
async def test_manage_sect_promote(mock_save_cult, mock_get_cult, mock_save_sects, mock_load_sects):
    """测试宗门管理：任命长老"""
    mock_load_sects.return_value = {
        "测试宗门": {
            "name": "测试宗门",
            "master": "master_user",
            "members": {
                "master_user": {"role": ROLE_MASTER},
                "target": {"role": ROLE_OUTER}
            }
        }
    }
    target_profile = CultivatorProfile(username="target", sect="测试宗门", sect_role=ROLE_OUTER)
    mock_get_cult.return_value = target_profile

    # 只有宗主可以任命长老
    success, msg = await manage_sect("测试宗门", "promote_elder", "target", "master_user")
    assert success is True
    
    saved_sects = mock_save_sects.call_args[0][0]
    assert saved_sects["测试宗门"]["members"]["target"]["role"] == ROLE_ELDER

    saved_profile = mock_save_cult.call_args[0][0]
    assert saved_profile.sect_role == ROLE_ELDER
