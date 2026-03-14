"""
⚒️ 天工 TianGong — Phase 2 完整单元测试
覆盖: 境界体系、品阶体系、修仙者档案、洞府管理、搜索引擎、传承谱系
"""

# ============================================================
# 1. 境界体系测试
# ============================================================

from tiangong.realm import (
    REALMS,
    calculate_realm,
    calculate_stage,
    check_tribulation,
    get_next_realm,
    get_review_weight,
)


def test_realm_count():
    """21 级完整仙逆体系"""
    assert len(REALMS) == 21
    assert REALMS[0].level == 0
    assert REALMS[0].name_cn == "凡人"
    assert REALMS[-1].name_cn == "天工"
    assert REALMS[-1].level == 20


def test_initial_realm():
    """新修仙者应该是凡人"""
    realm = calculate_realm(0)
    assert realm.level == 0
    assert realm.name_cn == "凡人"
    assert realm.symbol == "🧑"


def test_spirit_power_realm():
    """灵力值驱动境界判定"""
    # 灵力值 0 → 凡人
    assert calculate_realm(0).name_cn == "凡人"
    # 灵力值 5 → 炼气期
    assert calculate_realm(5).name_cn == "炼气期"
    # 灵力值 15 → 筑基期
    assert calculate_realm(15).name_cn == "筑基期"
    # 灵力值 100 → 结丹期
    assert calculate_realm(100).name_cn == "结丹期"


def test_stage_calculation():
    """九阶计算"""
    realm = calculate_realm(0)  # 凡人
    stage = calculate_stage(0, realm)
    assert stage == 0  # 凡人无阶

    # 高灵力值在炼气期内的阶位
    realm = calculate_realm(5)
    stage = calculate_stage(5, realm)
    assert 1 <= stage <= 9


def test_review_weight():
    """评价权重随境界递增"""
    w0 = get_review_weight(0)  # 凡人
    w1 = get_review_weight(1)  # 炼气期
    w5 = get_review_weight(5)  # 化神期
    assert w0 <= w1 <= w5


def test_tribulation_detection():
    """渡劫检测（灵力值从0到10应触发凡人→筑基期的连环渡劫/越级提升）"""
    # 从 0 到 10: 凡人→筑基期
    triggered, old, new = check_tribulation(0, 10)
    assert triggered is True
    assert old.name_cn == "凡人"
    assert new.name_cn == "筑基期"

    # 小幅增加不触发渡劫
    triggered, _, _ = check_tribulation(10, 12)
    assert triggered is False


def test_next_realm():
    """获取下一个境界"""
    realm = REALMS[0]  # 凡人
    next_r = get_next_realm(realm)
    assert next_r is not None
    assert next_r.name_cn == "炼气期"

    # 天工没有下一个境界
    top = REALMS[-1]
    assert get_next_realm(top) is None


# ============================================================
# 2. 品阶体系测试
# ============================================================

from tiangong.artifact_system import (
    GRADES,
    DIMENSIONS,
    SpiritReview,
    calculate_grade,
    check_grade_change,
)


def test_grade_count():
    """6 级品阶"""
    assert len(GRADES) == 6
    assert GRADES[0].name_cn == "凡器"
    assert GRADES[-1].name_cn == "太古神器"


def test_dimension_count():
    """6 维评估"""
    assert len(DIMENSIONS) == 6
    keys = [d["key"] for d in DIMENSIONS]
    assert "inscription" in keys
    assert "formation" in keys
    assert "technique" in keys
    assert "lineage" in keys
    assert "resilience" in keys
    assert "enlightenment" in keys


def test_grade_calculation():
    """品阶计算"""
    # 0 灵力 → 凡器
    assert calculate_grade(0, 0).name_cn == "凡器"
    # 10 灵力 + 3 评价者 → 灵器
    assert calculate_grade(10, 3).name_cn == "灵器"
    # 50 灵力 + 10 评价者 → 宝器
    assert calculate_grade(50, 10).name_cn == "宝器"
    # 200 + 30 → 仙器
    assert calculate_grade(200, 30).name_cn == "仙器"


def test_spirit_review():
    """灵力灌注计算"""
    review = SpiritReview(
        reviewer="tester",
        reviewer_realm_level=3,
        reviewer_weight=2.0,
        scores={"inscription": 8, "formation": 7, "technique": 9,
                "lineage": 6, "resilience": 7, "enlightenment": 8},
    )
    assert review.average_score > 0
    assert review.spirit_value == review.average_score * 2.0


def test_grade_change_detection():
    """品阶变化检测"""
    changed, old, new = check_grade_change(5, 15, 2, 5)
    assert changed is True
    assert old.name_cn == "凡器"
    assert new.name_cn == "灵器"


# ============================================================
# 3. 修仙者档案测试
# ============================================================

from tiangong.cultivator import CultivatorProfile


def test_cultivator_profile():
    """修仙者档案基本属性"""
    p = CultivatorProfile(username="test", spirit_power=150)
    assert p.realm.name_cn != "凡人"  # spirit=150 应超过凡人
    assert 1 <= p.stage <= 9
    assert p.review_weight > 0


def test_cultivator_realm_property():
    """修仙者境界属性关联"""
    p = CultivatorProfile(username="test", spirit_power=0)
    assert p.realm.name_cn == "凡人"
    assert p.realm_level == 0


# ============================================================
# 4. 洞府管理测试
# ============================================================

from tiangong.vault import list_vault, list_forge


def test_vault_import():
    """洞府管理模块正常导入"""
    assert callable(list_vault)
    assert callable(list_forge)


# ============================================================
# 5. 搜索引擎测试
# ============================================================

from tiangong.search import classify_query


def test_classify_query_grade():
    """品阶关键词识别"""
    q = classify_query("仙器")
    assert q["grade_filter"] == "仙器"


def test_classify_query_creator():
    """创作者关键词识别"""
    q = classify_query("@JinNing6")
    assert q["creator_filter"] == "JinNing6"


def test_classify_query_framework():
    """框架关键词识别"""
    q = classify_query("crewai")
    assert q["framework_filter"] == "crewai"


def test_classify_query_combined():
    """组合搜索"""
    q = classify_query("仙器 crewai @JinNing6 数据分析")
    assert q["grade_filter"] == "仙器"
    assert q["framework_filter"] == "crewai"
    assert q["creator_filter"] == "JinNing6"
    assert q["text_query"] == "数据分析"


def test_classify_query_empty():
    """空查询"""
    q = classify_query("")
    assert q["grade_filter"] is None
    assert q["text_query"] == ""


# ============================================================
# 6. 传承谱系测试
# ============================================================

from tiangong.lineage import LINEAGE_TYPES, calculate_lineage_bonus


def test_lineage_types():
    """三种传承关系"""
    assert "fork" in LINEAGE_TYPES
    assert "inspired" in LINEAGE_TYPES
    assert "depends" in LINEAGE_TYPES


def test_lineage_bonus():
    """传承灵力加成"""
    tree = {
        "name": "test-agent",
        "children": [
            {"name": "fork-1", "type": "fork"},
            {"name": "inspired-1", "type": "inspired"},
        ],
        "dependents": ["dep-1"],
    }
    bonus = calculate_lineage_bonus("test-agent", tree)
    # fork=2 + inspired=1 + depends=3 = 6
    assert bonus == 6


# ============================================================
# 7. 试剑体系测试
# ============================================================

from tiangong.trial import evaluate_agent, TRIAL_DIMENSIONS


def test_trial_dimensions_aligned():
    """试剑维度与 artifact_system 对齐"""
    keys = [d["key"] for d in TRIAL_DIMENSIONS]
    assert "inscription" in keys
    assert "formation" in keys
    assert "technique" in keys
    assert "lineage" in keys
    assert "resilience" in keys
    assert "enlightenment" in keys


def test_trial_evaluate():
    """试剑评估基本功能"""
    result = evaluate_agent(
        agent_id="test-001",
        name="Test Agent",
        description="A comprehensive test agent for automated testing and validation",
        agent_type="tool",
        framework="langchain",
        language="python",
        repo_url="https://github.com/test/repo",
        tags=["testing", "automation"],
    )
    assert result.agent_id == "test-001"
    assert 0 <= result.score <= 100
    assert result.passed is True or result.passed is False
    assert "inscription" in result.dimensions
    assert "formation" in result.dimensions


# ============================================================
# 8. MCP Server 导入测试
# ============================================================


def test_mcp_server_import():
    """MCP Server 可正常导入"""
    from tiangong.mcp_server import mcp
    assert mcp.name == "tiangong"
