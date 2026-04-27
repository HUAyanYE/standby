"""
情境感知引擎 — gRPC 服务实现 (最小版)

职责:
1. 接收端侧提交的情境状态
2. 基于情境提供话题权重建议

一期实现: 简单规则引擎，后续升级为模型驱动。
"""

import logging
import sys
import time
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent))
from shared.engine_base import EngineConfig, EngineServicer, timing_decorator

# gRPC 生成代码
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src" / "proto" / "generated" / "python"))
from engines import engines_pb2_grpc
from engines import engines_pb2
from common import common_pb2

logger = logging.getLogger(__name__)


class ContextEngineServicer(EngineServicer):
    """情境感知引擎 gRPC 服务"""

    def __init__(self, config: EngineConfig):
        super().__init__(config)
        # 用户最新情境缓存
        self._user_contexts: dict[str, dict] = {}

    def register_services(self, server):
        engines_pb2_grpc.add_ContextEngineServicer_to_server(self, server)
        logger.info("ContextEngine service 已注册")

    # --------------------------------------------------------
    # gRPC PascalCase 别名
    # --------------------------------------------------------

    def SubmitContextState(self, request, context):
        result = self.submit_context_state(request)
        return engines_pb2.ContextStateResponse(accepted=result.get("accepted", False))

    def GetContextualWeights(self, request, context):
        result = self.get_contextual_weights(request)
        return engines_pb2.ContextualWeightsResponse(
            topic_weights=result.get("topic_weights", {}),
            recommended_scene=result.get("recommended_scene", ""),
        )

    # --------------------------------------------------------
    # 业务逻辑
    # --------------------------------------------------------

    @timing_decorator
    def submit_context_state(self, request) -> dict:
        """接收端侧情境状态"""
        user_id = request.user_id if hasattr(request, 'user_id') else ""
        state = {
            "scene_type": request.scene_type if hasattr(request, 'scene_type') else "",
            "mood_hint": request.mood_hint if hasattr(request, 'mood_hint') else "",
            "attention_level": request.attention_level if hasattr(request, 'attention_level') else "",
            "device": request.active_device if hasattr(request, 'active_device') else 0,
            "timestamp": request.timestamp if hasattr(request, 'timestamp') else int(time.time()),
        }
        self._user_contexts[user_id] = state
        logger.info(f"情境更新: user={user_id[:8]}, scene={state['scene_type']}, mood={state['mood_hint']}")
        return {"accepted": True}

    @timing_decorator
    def get_contextual_weights(self, request) -> dict:
        """基于情境计算话题权重"""
        user_id = request.user_id if hasattr(request, 'user_id') else ""
        candidates = list(request.candidate_topics) if hasattr(request, 'candidate_topics') else []

        ctx = self._user_contexts.get(user_id, {})
        scene = ctx.get("scene_type", "")
        mood = ctx.get("mood_hint", "")
        hour = datetime.now().hour

        # 情境→话题权重映射（规则版）
        scene_boost = {
            "commute": ["孤独", "城市", "日常", "思考"],
            "home_relax": ["回忆", "温暖", "家庭", "放松"],
            "work_break": ["灵感", "创意", "职场", "效率"],
            "driving": ["自由", "远方", "音乐", "独处"],
            "深夜": ["孤独", "时间", "意义", "自我", "人生"],
        }

        mood_boost = {
            "calm": ["哲学", "自然", "安静"],
            "reflective": ["回忆", "时间", "成长"],
            "energetic": ["冒险", "挑战", "变化"],
            "tired": ["温暖", "休息", "简单"],
        }

        # 基于时间推断场景
        if not scene:
            if hour >= 22 or hour < 6:
                scene = "深夜"
            elif 7 <= hour < 9:
                scene = "commute"

        # 计算权重
        weights = {}
        boost_topics = scene_boost.get(scene, []) + mood_boost.get(mood, [])

        for topic in candidates:
            w = 1.0
            if topic in boost_topics:
                w += 0.5
            weights[topic] = round(w, 2)

        recommended = {
            "深夜": "深度阅读",
            "commute": "碎片浏览",
            "home_relax": "沉浸阅读",
            "work_break": "轻量浏览",
        }.get(scene, "沉浸阅读")

        return {
            "topic_weights": weights,
            "recommended_scene": recommended,
        }


def main():
    config = EngineConfig.from_yaml("context_engine")
    servicer = ContextEngineServicer(config)

    # 本地测试
    print("=" * 60)
    print("  情境引擎服务测试")
    print("=" * 60)

    # 提交情境
    class MockCtx:
        user_id = "u001"
        scene_type = "深夜"
        mood_hint = "calm"
        attention_level = "focused"
        active_device = 1
        timestamp = int(time.time())

    result = servicer.submit_context_state(MockCtx())
    print(f"\n情境提交: {result}")

    # 获取权重
    class MockWeights:
        user_id = "u001"
        candidate_topics = ["孤独", "城市", "工作", "时间", "美食"]

    result = servicer.get_contextual_weights(MockWeights())
    print(f"话题权重: {result['topic_weights']}")
    print(f"推荐场景: {result['recommended_scene']}")

    print(f"\n✅ 情境引擎服务测试完成")
    print("启动gRPC服务器...")
    servicer.run()


if __name__ == "__main__":
    main()
