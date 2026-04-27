"""
Standby gRPC 集成测试

通过 gRPC 调用各引擎，测试真实的通信链路
- 不依赖容器内部模块结构
- 测试完整的请求/响应流程
- 验证跨引擎协作

运行方式：
  cd /mnt/d/Hermes/standby
  python3 engines/tests/test_integration_grpc.py
"""

import sys
import time
import grpc
import numpy as np
from pathlib import Path

# 添加 proto 路径
proto_path = Path(__file__).parent.parent.parent / "src" / "proto" / "generated" / "python"
sys.path.insert(0, str(proto_path))

# 导入 gRPC 生成代码
from engines import engines_pb2
from engines import engines_pb2_grpc
from common import common_pb2

# ============================================================
# 配置
# ============================================================

ENGINE_ENDPOINTS = {
    'resonance': 'localhost:8091',
    'anchor': 'localhost:8090',
    'governance': 'localhost:8092',
    'user': 'localhost:8093',
    'context': 'localhost:8094',
}


class TestResult:
    """测试结果收集"""
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []
    
    def success(self, name: str, detail: str = ""):
        self.passed += 1
        print(f"  ✅ {name}" + (f": {detail}" if detail else ""))
    
    def fail(self, name: str, error: str):
        self.failed += 1
        self.errors.append((name, error))
        print(f"  ❌ {name}: {error}")
    
    def summary(self):
        total = self.passed + self.failed
        print(f"\n{'='*60}")
        print(f"测试完成: {self.passed}/{total} 通过, {self.failed} 失败")
        if self.errors:
            print(f"\n失败详情:")
            for name, error in self.errors:
                print(f"  ❌ {name}: {error}")
        return self.failed == 0


def get_stub(engine_name: str, stub_class):
    """获取 gRPC stub"""
    channel = grpc.insecure_channel(ENGINE_ENDPOINTS[engine_name])
    return stub_class(channel)


# ============================================================
# 测试类
# ============================================================

class GrpcIntegrationTest:
    """gRPC 集成测试"""
    
    def __init__(self):
        self.result = TestResult()
        self.test_anchor_id = None
    
    def run(self):
        """运行所有测试"""
        print("=" * 60)
        print("Standby gRPC 集成测试")
        print("=" * 60)
        
        # 测试各引擎连接
        print("\n📍 Phase 1: 引擎连接测试")
        self.test_engine_connections()
        
        # 测试锚点引擎
        print("\n📍 Phase 2: 锚点引擎测试")
        self.test_anchor_engine()
        
        # 测试共鸣引擎
        print("\n📍 Phase 3: 共鸣引擎测试")
        self.test_resonance_engine()
        
        # 测试治理引擎
        print("\n📍 Phase 4: 治理引擎测试")
        self.test_governance_engine()
        
        # 测试用户引擎
        print("\n📍 Phase 5: 用户引擎测试")
        self.test_user_engine()
        
        # 测试情境引擎
        print("\n📍 Phase 6: 情境引擎测试")
        self.test_context_engine()
        
        return self.result.summary()
    
    def test_engine_connections(self):
        """测试各引擎 gRPC 连接"""
        for name, endpoint in ENGINE_ENDPOINTS.items():
            try:
                channel = grpc.insecure_channel(endpoint)
                grpc.channel_ready_future(channel).result(timeout=3)
                self.result.success(f"{name} 引擎连接", endpoint)
            except Exception as e:
                self.result.fail(f"{name} 引擎连接", str(e))
    
    def test_anchor_engine(self):
        """测试锚点引擎"""
        try:
            stub = get_stub('anchor', engines_pb2_grpc.AnchorEngineStub)
            
            # 测试 ListAnchors
            request = engines_pb2.ListAnchorsRequest(
                page=1,
                page_size=10,
            )
            response = stub.ListAnchors(request)
            self.result.success(
                "ListAnchors",
                f"返回 {len(response.anchors)} 个锚点"
            )
            
            # 测试 GenerateAnchor (如果有足够内容)
            if len(response.anchors) > 0:
                self.test_anchor_id = response.anchors[0].anchor_id
                self.result.success(
                    "获取测试锚点",
                    f"anchor_id={self.test_anchor_id}"
                )
            
        except grpc.RpcError as e:
            self.result.fail("锚点引擎测试", f"gRPC 错误: {e.code()}")
        except Exception as e:
            self.result.fail("锚点引擎测试", str(e))
    
    def test_resonance_engine(self):
        """测试共鸣引擎"""
        try:
            stub = get_stub('resonance', engines_pb2_grpc.ResonanceEngineStub)
            
            # 测试 ProcessReaction
            request = engines_pb2.ProcessReactionRequest(
                event_id=f"test_{int(time.time())}",
                user_id="test_user_001",
                anchor_id=self.test_anchor_id or "test_anchor",
                reaction_type=common_pb2.RESONANCE,
                emotion_word=common_pb2.EMPATHY,
                opinion_text="这是一个测试观点，用于验证共鸣引擎的 gRPC 接口。",
                timestamp=int(time.time()),
            )
            
            response = stub.ProcessReaction(request)
            
            if response.success:
                self.result.success(
                    "ProcessReaction",
                    f"resonance_value={response.resonance_value:.4f}"
                )
            else:
                self.result.fail("ProcessReaction", response.error)
            
            # 测试 GetReactionDistribution
            dist_request = engines_pb2.GetReactionDistributionRequest(
                anchor_id=self.test_anchor_id or "test_anchor"
            )
            dist_response = stub.GetReactionDistribution(dist_request)
            
            if dist_response.found:
                dist = dist_response.distribution
                self.result.success(
                    "GetReactionDistribution",
                    f"total={dist.total_count}"
                )
            else:
                self.result.success("GetReactionDistribution", "未找到数据 (正常)")
            
            # EncodeText 测试跳过（需要特定参数格式）
            
        except grpc.RpcError as e:
            self.result.fail("共鸣引擎测试", f"gRPC 错误: {e.code()}")
        except Exception as e:
            self.result.fail("共鸣引擎测试", str(e))
    
    def test_governance_engine(self):
        """测试治理引擎"""
        try:
            stub = get_stub('governance', engines_pb2_grpc.GovernanceEngineStub)
            
            # 测试 EvaluateContent
            request = engines_pb2.EvaluateContentRequest(
                content_id=self.test_anchor_id or "test_anchor",
                content_type=common_pb2.USER_CONTENT,
                text="这是一个正常的内容，用于测试治理引擎。",
            )
            
            response = stub.EvaluateContent(request)
            self.result.success(
                "EvaluateContent",
                f"evaluated={response.evaluated}, decision={response.decision}"
            )
            
            # 测试 DetectAnomaly
            anomaly_request = engines_pb2.DetectAnomalyRequest(
                anchor_id=self.test_anchor_id or "test_anchor",
                mark_timestamps=[float(i) for i in range(10)],
                marker_ids=[f"user_{i}" for i in range(10)],
            )
            
            anomaly_response = stub.DetectAnomaly(anomaly_request)
            self.result.success(
                "DetectAnomaly",
                f"anomaly_detected={anomaly_response.anomaly_detected}"
            )
            
        except grpc.RpcError as e:
            self.result.fail("治理引擎测试", f"gRPC 错误: {e.code()}")
        except Exception as e:
            self.result.fail("治理引擎测试", str(e))
    
    def test_user_engine(self):
        """测试用户引擎"""
        try:
            stub = get_stub('user', engines_pb2_grpc.UserEngineStub)
            
            # 测试 UpdateTrustLevel (更新关系分)
            trust_request = engines_pb2.UpdateTrustLevelRequest(
                user_a_id="test_user_001",
                user_b_id="test_user_002",
                new_score_a_to_b=0.5,
                new_score_b_to_a=0.5,
                topic_diversity=3,
                current_timestamp=int(time.time()),
            )
            
            trust_response = stub.UpdateTrustLevel(trust_request)
            self.result.success(
                "UpdateTrustLevel",
                f"updated={trust_response.updated}, level={trust_response.new_level}"
            )
            
        except grpc.RpcError as e:
            self.result.fail("用户引擎测试", f"gRPC 错误: {e.code()}")
        except Exception as e:
            self.result.fail("用户引擎测试", str(e))
    
    def test_context_engine(self):
        """测试情境引擎"""
        try:
            stub = get_stub('context', engines_pb2_grpc.ContextEngineStub)
            
            # 测试 SubmitContextState
            request = engines_pb2.ContextStateRequest(
                user_id="test_user_001",
                scene_type="工作",
                mood_hint="专注",
                attention_level="高",
                active_device=common_pb2.PHONE,
                timestamp=int(time.time()),
            )
            
            response = stub.SubmitContextState(request)
            self.result.success(
                "SubmitContextState",
                f"accepted={response.accepted}"
            )
            
            # 测试 GetContextualWeights
            weights_request = engines_pb2.ContextualWeightsRequest(
                user_id="test_user_001",
                candidate_topics=["科技", "生活", "工作"],
            )
            
            weights_response = stub.GetContextualWeights(weights_request)
            self.result.success(
                "GetContextualWeights",
                f"scene={weights_response.recommended_scene}"
            )
            
        except grpc.RpcError as e:
            self.result.fail("情境引擎测试", f"gRPC 错误: {e.code()}")
        except Exception as e:
            self.result.fail("情境引擎测试", str(e))


if __name__ == "__main__":
    test = GrpcIntegrationTest()
    success = test.run()
    sys.exit(0 if success else 1)
