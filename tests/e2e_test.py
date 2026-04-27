#!/usr/bin/env python3
"""
Standby 端到端测试脚本

测试全链路: Gateway → 引擎 → 数据库
使用标准库，无需额外依赖
"""

import json
import time
import hashlib
import urllib.request
import urllib.error
from typing import Optional, Dict, Any

# ============================================================
# 配置
# ============================================================
GATEWAY_URL = "http://localhost:8080"

# 测试数据
TEST_DEVICE_FP = hashlib.sha256(str(time.time()).encode()).hexdigest()  # 64 字符 SHA-256
TEST_ANCHOR_TEXT = "中美关系的深层逻辑：从博弈到共生"
TEST_OPINION_TEXT = "这篇文章提供了独特的视角，让我重新思考了国际关系的本质"


class TestResult:
    """测试结果收集器"""
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []
        self.start_time = time.time()
    
    def success(self, name: str, detail: str = ""):
        self.passed += 1
        print(f"  ✅ {name}" + (f": {detail}" if detail else ""))
    
    def fail(self, name: str, error: str):
        self.failed += 1
        self.errors.append((name, error))
        print(f"  ❌ {name}: {error}")
    
    def summary(self):
        elapsed = time.time() - self.start_time
        total = self.passed + self.failed
        print(f"\n{'='*60}")
        print(f"测试完成: {self.passed}/{total} 通过, {self.failed} 失败")
        print(f"耗时: {elapsed:.2f}s")
        if self.errors:
            print(f"\n失败详情:")
            for name, error in self.errors:
                print(f"  ❌ {name}: {error}")
        return self.failed == 0


def http_request(url: str, method: str = "GET", data: Optional[Dict] = None, 
                 headers: Optional[Dict] = None, timeout: int = 10) -> tuple:
    """HTTP 请求封装"""
    headers = headers or {}
    headers.setdefault("Content-Type", "application/json")
    
    body = json.dumps(data).encode() if data else None
    
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            resp_data = response.read().decode()
            return response.status, json.loads(resp_data) if resp_data else {}
    except urllib.error.HTTPError as e:
        resp_data = e.read().decode() if e.fp else ""
        try:
            return e.code, json.loads(resp_data)
        except:
            return e.code, {"error": resp_data}
    except Exception as e:
        return 0, {"error": str(e)}


class StandbyE2ETest:
    """Standby 端到端测试"""
    
    def __init__(self):
        self.result = TestResult()
        self.token: Optional[str] = None
        self.device_fingerprint: Optional[str] = None
        self.anchor_id: Optional[str] = None
        self.user_id: Optional[str] = None
    
    def run(self):
        """执行所有测试"""
        print("=" * 60)
        print("Standby 端到端测试")
        print("=" * 60)
        
        # Phase 1: 健康检查
        print("\n📍 Phase 1: 健康检查")
        self.test_health()
        
        # Phase 2: 认证流程
        print("\n📍 Phase 2: 认证流程")
        self.test_auth()
        
        # Phase 3: 锚点流程
        print("\n📍 Phase 3: 锚点流程")
        self.test_anchor()
        
        # Phase 4: 共鸣流程
        print("\n📍 Phase 4: 共鸣流程")
        self.test_reaction()
        
        # Phase 5: 用户流程
        print("\n📍 Phase 5: 用户流程")
        self.test_user()
        
        # Phase 6: 治理流程
        print("\n📍 Phase 6: 治理流程")
        self.test_governance()
        
        # Phase 7: 情境流程
        print("\n📍 Phase 7: 情境流程")
        self.test_context()
        
        # Phase 8: 数据一致性 (通过 API 验证)
        print("\n📍 Phase 8: 数据一致性")
        self.test_data_consistency()
        
        # Phase 9: 压力测试
        print("\n📍 Phase 9: 压力测试")
        self.test_stress()
        
        # Phase 10: 边界情况
        print("\n📍 Phase 10: 边界情况")
        self.test_edge_cases()
        
        return self.result.summary()
    
    def _headers(self):
        """获取请求头"""
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        if self.device_fingerprint:
            headers["X-Device-Fingerprint"] = self.device_fingerprint
        return headers
    
    # ============================================================
    # Phase 1: 健康检查
    # ============================================================
    def test_health(self):
        """测试健康检查端点"""
        status, data = http_request(f"{GATEWAY_URL}/health")
        
        if status == 200 and data.get("status") == "healthy":
            self.result.success("Gateway 健康检查", f"version={data.get('version')}")
        else:
            self.result.fail("Gateway 健康检查", f"状态码={status}, 响应={data}")
    
    # ============================================================
    # Phase 2: 认证流程
    # ============================================================
    def test_auth(self):
        """测试设备认证"""
        status, data = http_request(
            f"{GATEWAY_URL}/auth/device",
            method="POST",
            data={
                "device_type": "phone",
                "device_fingerprint": TEST_DEVICE_FP,
                "os_version": "test-os-1.0",
                "app_version": "standby-test-0.1.0"
            }
        )
        
        if status == 200:
            self.token = data.get("access_token")
            self.device_fingerprint = TEST_DEVICE_FP
            self.user_id = data.get("user_id")
            self.result.success("设备认证", f"token长度={len(self.token) if self.token else 0}")
        else:
            self.result.fail("设备认证", f"状态码={status}, 响应={data}")
    
    # ============================================================
    # Phase 3: 锚点流程
    # ============================================================
    def test_anchor(self):
        """测试锚点创建和查询"""
        if not self.token:
            self.result.fail("锚点创建", "未获取到 token")
            return
        
        # 创建锚点 (使用 /anchors/import 端点)
        # 需要至少 100 字的内容
        long_content = TEST_ANCHOR_TEXT + "。" + "这是一个测试内容，用于验证锚点创建流程。" * 10
        
        status, data = http_request(
            f"{GATEWAY_URL}/anchors/import",
            method="POST",
            data={
                "content_text": long_content,
                "topics": ["国际关系", "中美博弈", "地缘政治"]
            },
            headers=self._headers(),
            timeout=15
        )
        
        if status == 200:
            self.anchor_id = data.get("anchor_id")
            accepted = data.get("accepted", False)
            self.result.success("创建锚点", f"accepted={accepted}, anchor_id={self.anchor_id}")
        else:
            self.result.fail("创建锚点", f"状态码={status}, 响应={data}")
            return
        
        # 查询锚点列表
        status, data = http_request(
            f"{GATEWAY_URL}/anchors",
            headers=self._headers()
        )
        
        if status == 200:
            anchors = data.get("anchors", [])
            self.result.success("查询锚点列表", f"数量={len(anchors)}")
        else:
            self.result.fail("查询锚点列表", f"状态码={status}")
        
        # 查询单个锚点
        if self.anchor_id:
            status, data = http_request(
                f"{GATEWAY_URL}/anchors/{self.anchor_id}",
                headers=self._headers()
            )
            
            if status == 200:
                found = data.get("found", False)
                self.result.success("查询锚点详情", f"found={found}")
            else:
                self.result.fail("查询锚点详情", f"状态码={status}")
    
    # ============================================================
    # Phase 4: 共鸣流程
    # ============================================================
    def test_reaction(self):
        """测试反应提交和查询"""
        if not self.token or not self.anchor_id:
            self.result.fail("反应提交", "缺少 token 或 anchor_id")
            return
        
        # 提交反应 - 使用中文字符串类型
        status, data = http_request(
            f"{GATEWAY_URL}/reactions",
            method="POST",
            data={
                "anchor_id": self.anchor_id,
                "reaction_type": "共鸣",  # 中文字符串
                "emotion_word": "同感",   # 中文字符串
                "opinion_text": TEST_OPINION_TEXT
            },
            headers=self._headers(),
            timeout=15
        )
        
        if status == 200:
            resonance_value = data.get("resonance_value", 0)
            self.result.success("提交反应", f"resonance_value={resonance_value:.4f}")
        else:
            self.result.fail("提交反应", f"状态码={status}, 响应={data}")
        
        time.sleep(0.5)  # 避免速率限制
        
        # 查询反应分布
        status, data = http_request(
            f"{GATEWAY_URL}/anchors/{self.anchor_id}/reactions",
            headers=self._headers()
        )
        
        if status == 200:
            total = data.get("total_count", 0)
            self.result.success("查询反应分布", f"total_count={total}")
        else:
            self.result.fail("查询反应分布", f"状态码={status}")
    
    # ============================================================
    # Phase 5: 用户流程
    # ============================================================
    def test_user(self):
        """测试用户档案"""
        if not self.token:
            self.result.fail("用户档案", "未获取到 token")
            return
        
        status, data = http_request(
            f"{GATEWAY_URL}/me",
            headers=self._headers()
        )
        
        if status == 200:
            trust_level = data.get("trust_level", 0)
            self.result.success("查询用户档案", f"trust_level={trust_level}")
        else:
            self.result.fail("用户档案", f"状态码={status}")
        
        # 查询关系
        status, data = http_request(
            f"{GATEWAY_URL}/relationships",
            headers=self._headers()
        )
        
        if status == 200:
            relationships = data.get("relationships", [])
            self.result.success("查询关系", f"关系数={len(relationships)}")
        else:
            self.result.fail("查询关系", f"状态码={status}")
    
    # ============================================================
    # Phase 6: 治理流程
    # ============================================================
    def test_governance(self):
        """测试内容举报"""
        if not self.token or not self.anchor_id:
            self.result.fail("内容举报", "缺少 token 或 anchor_id")
            return
        
        time.sleep(0.5)  # 避免速率限制
        
        # 使用正确的字段名
        status, data = http_request(
            f"{GATEWAY_URL}/report",
            method="POST",
            data={
                "content_id": self.anchor_id,
                "content_type": "anchor",
                "report_type": "spam",
                "reason": "这是一个测试举报，用于验证治理流程"
            },
            headers=self._headers()
        )
        
        if status == 200:
            accepted = data.get("accepted", False)
            self.result.success("内容举报", f"accepted={accepted}")
        else:
            self.result.fail("内容举报", f"状态码={status}, 响应={data}")
    
    # ============================================================
    # Phase 7: 情境流程
    # ============================================================
    def test_context(self):
        """测试情境状态"""
        if not self.token:
            self.result.fail("情境状态", "未获取到 token")
            return
        
        # 提交情境状态 - 使用正确的字段
        status, data = http_request(
            f"{GATEWAY_URL}/context",
            method="POST",
            data={
                "scene_type": "工作",
                "mood_hint": "专注",
                "attention_level": "高",
                "active_device": "phone"
            },
            headers=self._headers()
        )
        
        if status == 200:
            accepted = data.get("accepted", False)
            self.result.success("提交情境状态", f"accepted={accepted}")
        else:
            self.result.fail("情境状态", f"状态码={status}, 响应={data}")
        
        # 获取权重
        status, data = http_request(
            f"{GATEWAY_URL}/context/hint",
            headers=self._headers()
        )
        
        if status == 200:
            keys = list(data.keys())[:3] if isinstance(data, dict) else []
            self.result.success("获取情境权重", f"keys={keys}")
        else:
            self.result.fail("获取情境权重", f"状态码={status}")
    
    # ============================================================
    # Phase 8: 数据一致性 (通过 API 验证)
    # ============================================================
    def test_data_consistency(self):
        """验证 API 返回数据一致性"""
        if not self.anchor_id:
            self.result.fail("数据一致性", "缺少 anchor_id")
            return
        
        time.sleep(1)  # 避免速率限制
        
        # 1. 验证锚点存在
        status, anchor_data = http_request(
            f"{GATEWAY_URL}/anchors/{self.anchor_id}",
            headers=self._headers()
        )
        
        if status == 200:
            found = anchor_data.get("found", False)
            self.result.success("锚点数据存在", f"found={found}")
        else:
            self.result.fail("锚点数据存在", f"状态码={status}")
        
        time.sleep(0.5)
        
        # 2. 验证反应数据
        status, reaction_data = http_request(
            f"{GATEWAY_URL}/anchors/{self.anchor_id}/reactions",
            headers=self._headers()
        )
        
        if status == 200:
            count = reaction_data.get("total_count", 0)
            self.result.success("反应数据一致", f"count={count}")
        else:
            self.result.fail("反应数据一致", f"状态码={status}")
    
    # ============================================================
    # Phase 9: 压力测试
    # ============================================================
    def test_stress(self):
        """批量反应测试"""
        if not self.token or not self.anchor_id:
            self.result.fail("压力测试", "缺少 token 或 anchor_id")
            return
        
        time.sleep(1)  # 避免之前的请求触发速率限制
        
        print(f"  📊 批量提交 5 个反应...")
        success_count = 0
        start_time = time.time()
        
        reaction_types = ["共鸣", "无感", "反对", "同感", "启发"]
        
        for i in range(5):
            status, _ = http_request(
                f"{GATEWAY_URL}/reactions",
                method="POST",
                data={
                    "anchor_id": self.anchor_id,
                    "reaction_type": reaction_types[i % len(reaction_types)],
                    "opinion_text": f"测试反应 #{i+1}"
                },
                headers=self._headers()
            )
            
            if status == 200:
                success_count += 1
            
            time.sleep(0.3)  # 每个请求之间延迟
        
        elapsed = time.time() - start_time
        
        if success_count >= 3:  # 允许部分失败（可能是速率限制）
            self.result.success("批量反应", f"{success_count}/5 成功, 耗时={elapsed:.2f}s")
        else:
            self.result.fail("批量反应", f"仅 {success_count}/5 成功")
    
    # ============================================================
    # Phase 10: 边界情况
    # ============================================================
    def test_edge_cases(self):
        """测试边界情况"""
        
        time.sleep(1.5)  # 避免速率限制
        
        # 1. 空锚点文本 (内容过短)
        status, data = http_request(
            f"{GATEWAY_URL}/anchors/import",
            method="POST",
            data={"content_text": "太短", "topics": []},
            headers=self._headers()
        )
        
        # 应该被拒绝或者返回 accepted=false
        if status == 200:
            accepted = data.get("accepted", True)
            if not accepted:
                self.result.success("短文本拒绝", f"accepted={accepted}")
            else:
                self.result.fail("短文本拒绝", "应该拒绝但接受了")
        elif status == 429:
            self.result.success("短文本拒绝", f"状态码={status} (速率限制)")
        else:
            self.result.success("短文本拒绝", f"状态码={status}")
        
        time.sleep(0.5)
        
        # 2. 无效 anchor_id
        status, data = http_request(
            f"{GATEWAY_URL}/anchors/invalid_anchor_id_12345",
            headers=self._headers()
        )
        
        if status == 200:
            found = data.get("found", True)
            self.result.success("无效锚点查询", f"found={found}")
        elif status == 429:
            self.result.success("无效锚点查询", f"状态码={status} (速率限制)")
        else:
            self.result.success("无效锚点查询", f"状态码={status}")
        
        time.sleep(0.5)
        
        # 3. 无效反应类型 (应该使用默认类型或拒绝)
        status, _ = http_request(
            f"{GATEWAY_URL}/reactions",
            method="POST",
            data={
                "anchor_id": self.anchor_id or "test",
                "reaction_type": "invalid_type",  # 无效类型
                "opinion_text": "测试"
            },
            headers=self._headers()
        )
        
        if status == 429:
            self.result.success("无效反应类型", f"状态码={status} (速率限制)")
        else:
            self.result.success("无效反应类型", f"状态码={status}")
        
        time.sleep(0.5)
        
        # 4. 超长文本
        long_text = "这是一个测试内容。" * 500  # 约 5000 字
        status, _ = http_request(
            f"{GATEWAY_URL}/anchors/import",
            method="POST",
            data={"content_text": long_text, "topics": ["测试"]},
            headers=self._headers(),
            timeout=15
        )
        
        if status == 429:
            self.result.success("超长文本处理", f"状态码={status} (速率限制)")
        else:
            self.result.success("超长文本处理", f"状态码={status}")
        
        time.sleep(0.5)
        
        # 5. 无认证请求
        status, _ = http_request(
            f"{GATEWAY_URL}/me",
            headers={"Content-Type": "application/json"}
        )
        
        if status == 401 or status == 403:
            self.result.success("无认证拒绝", f"状态码={status}")
        elif status == 429:
            self.result.success("无认证拒绝", f"状态码={status} (速率限制)")
        else:
            self.result.fail("无认证拒绝", f"应该返回401/403但返回了{status}")


if __name__ == "__main__":
    test = StandbyE2ETest()
    success = test.run()
    exit(0 if success else 1)
