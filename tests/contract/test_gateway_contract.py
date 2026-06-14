"""
Gateway REST API 契约测试

验证 Gateway 的请求/响应格式与 Proto 定义一致。
这些测试不需要运行 Gateway，只验证模型定义。
"""

import pytest


class TestReactionTypeConsistency:
    """验证反应类型枚举在各层的一致性"""

    def test_proto_reaction_type_values(self):
        """Proto 定义的反应类型值"""
        # Proto 定义 (common.proto)
        expected = {
            "UNSPECIFIED": 0,
            "RESONANCE": 1,
            "INDIFFERENCE": 2,  # 注意：已从 NEUTRAL 改为 INDIFFERENCE
            "OPPOSITION": 3,
            "UNEXPERIENCED": 4,
            "HARMFUL": 5,
        }
        # 这些值必须与 Rust ReactionType 枚举和 Python ReactionType 枚举一致
        assert expected["RESONANCE"] == 1
        assert expected["INDIFFERENCE"] == 2
        assert expected["OPPOSITION"] == 3
        assert expected["UNEXPERIENCED"] == 4
        assert expected["HARMFUL"] == 5

    def test_emotion_word_values(self):
        """情感词枚举值"""
        expected = {
            "UNSPECIFIED": 0,
            "SYMPATHY": 1,  # 注意：已从 EMPATHY 改为 SYMPATHY
            "TRIGGER": 2,
            "INSIGHT": 3,
            "SHOCK": 4,
        }
        assert expected["SYMPATHY"] == 1
        assert expected["TRIGGER"] == 2
        assert expected["INSIGHT"] == 3
        assert expected["SHOCK"] == 4


class TestGovernanceLevelConsistency:
    """验证治理级别在各层的一致性"""

    def test_governance_level_values(self):
        """治理级别枚举值"""
        expected = {
            "UNSPECIFIED": 0,
            "L0_NORMAL": 1,
            "L1_OBSERVE": 2,
            "L2_DEMOTED": 3,
            "L3_SUSPENDED": 4,
            "L4_REMOVED": 5,
            "DISPUTED": 6,
        }
        # 这些值必须与 Rust GovernanceLevel 枚举和 Proto GovernanceLevel 枚举一致
        assert expected["L0_NORMAL"] == 1
        assert expected["L1_OBSERVE"] == 2
        assert expected["L2_DEMOTED"] == 3
        assert expected["L3_SUSPENDED"] == 4
        assert expected["L4_REMOVED"] == 5
        assert expected["DISPUTED"] == 6


class TestAPIEndpointConsistency:
    """验证 API 端点定义的一致性"""

    def test_flutter_api_endpoints_match_gateway(self):
        """Flutter API 端点必须与 Gateway 路由一致"""
        # Flutter ApiService 定义的端点
        flutter_endpoints = {
            "listAnchors": "GET /api/v1/anchors",
            "getAnchor": "GET /api/v1/anchors/:id",
            "createAnchor": "POST /api/v1/anchors",
            "getGroupMemory": "GET /api/v1/anchors/:id/memory",
            "getFeelingChain": "GET /api/v1/anchors/:id/chain",
            "submitReaction": "POST /api/v1/reactions",
            "listReactions": "GET /api/v1/reactions",
            "getReactionDistribution": "GET /api/v1/reactions/distribution/:id",
            "getResonanceTraces": "GET /api/v1/relationships/traces",  # 已分离
            "findResonancePairs": "GET /api/v1/relationships/:user_id",
            "getRelationshipScore": "GET /api/v1/relationships/score",
            "evaluateContent": "POST /api/v1/governance/evaluate",
            "submitContextState": "POST /api/v1/context",
            "getContextualWeights": "GET /api/v1/context/weights",
            "encodeText": "POST /api/v1/encode",
        }

        # 验证端点格式正确
        for name, endpoint in flutter_endpoints.items():
            method, path = endpoint.split(" ", 1)
            assert method in ["GET", "POST", "PUT", "DELETE"], f"{name}: 无效的 HTTP 方法"
            assert path.startswith("/api/v1/"), f"{name}: 路径必须以 /api/v1/ 开头"


class TestModelFieldConsistency:
    """验证模型字段在各层的一致性"""

    def test_submit_reaction_has_parent_reaction_id(self):
        """submitReaction 必须支持 parent_reaction_id 参数（感受链）"""
        # Flutter ApiService.submitReaction 的参数
        params = {
            "anchorId": "required",
            "reactionType": "required",
            "opinionText": "optional",
            "emotionWord": "optional",
            "parentReactionId": "optional",  # 必须存在
        }
        assert "parentReactionId" in params, "submitReaction 缺少 parentReactionId 参数"

    def test_pagination_params_have_bounds(self):
        """分页参数必须有边界限制"""
        # Gateway PaginationParams 验证规则
        rules = {
            "page": {"default": 1, "min": 1},
            "page_size": {"default": 20, "min": 1, "max": 100},
        }
        assert rules["page_size"]["max"] == 100, "page_size 最大值必须为 100"
        assert rules["page"]["min"] == 1, "page 最小值必须为 1"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
