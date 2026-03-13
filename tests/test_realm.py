"""
⚒️ 天工 TianGong — 境界体系单元测试
"""

from tiangong.realm import (
    REALMS,
    calculate_realm,
    check_tribulation,
    get_next_realm,
)


def test_initial_realm():
    """新修仙者应该是炼气期"""
    realm = calculate_realm(0, 0)
    assert realm.level == 0
    assert realm.name_cn == "炼气期"
    assert realm.symbol == "🌱"


def test_foundation_building():
    """创建 1 个 Agent 应进入筑基期"""
    realm = calculate_realm(1, 0)
    assert realm.level == 1
    assert realm.name_cn == "筑基期"


def test_core_formation():
    """3 Agent + 10 星应进入结丹期"""
    realm = calculate_realm(3, 10)
    assert realm.level == 2
    assert realm.name_cn == "结丹期"


def test_partial_requirements():
    """只满足一个条件不应升境"""
    # 有足够 Agent 但星标不够
    realm = calculate_realm(10, 5)
    assert realm.level == 1  # 停在筑基期

    # 有足够星标但 Agent 不够
    realm = calculate_realm(2, 100)
    assert realm.level == 1  # 停在筑基期


def test_tribulation_detection():
    """渡劫检测"""
    # 从 0 Agent 到 1 Agent：应触发渡劫
    triggered, old, new = check_tribulation(0, 0, 1, 0)
    assert triggered is True
    assert old.level == 0
    assert new.level == 1

    # 从 1 Agent 到 2 Agent：不应触发渡劫
    triggered, _, _ = check_tribulation(1, 0, 2, 0)
    assert triggered is False


def test_next_realm():
    """获取下一个境界"""
    realm = REALMS[0]  # 炼气期
    next_r = get_next_realm(realm)
    assert next_r is not None
    assert next_r.name_cn == "筑基期"

    # 古神没有下一个境界
    ancient = REALMS[-1]
    assert get_next_realm(ancient) is None


def test_all_realms_defined():
    """确保九大境界全部定义"""
    assert len(REALMS) == 9


def test_ascendant_realm():
    """问鼎期需要 100 Agent + 1000 星"""
    realm = calculate_realm(100, 1000)
    assert realm.level == 6
    assert realm.name_cn == "问鼎期"


def test_community_realms_unreachable():
    """碎虚期和古神不能通过数量自动达到"""
    realm = calculate_realm(99999, 99999)
    assert realm.level == 6  # 最高只能到问鼎期
