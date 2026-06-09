"""
Rust 引擎客户端 — 集成测试

测试覆盖:
- call_resonance_compute_sync: 同步调用
- 错误处理: 超时、连接失败

注意: 这些测试需要 Rust resonance-service 运行。
  标记 @pytest.mark.integration 以跳过 CI。
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "shared"))

pytestmark = pytest.mark.integration


class TestRustEngineClient:
    """Rust 引擎客户端测试"""

    def test_import(self):
        """模块可导入"""
        from shared.rust_engine_client import (
            call_resonance_compute_sync,
            call_resonance_compute,
            RustEngineError,
        )
        assert callable(call_resonance_compute_sync)
        assert callable(call_resonance_compute)

    def test_sync_call_success(self):
        """同步调用成功"""
        try:
            from shared.rust_engine_client import call_resonance_compute_sync

            result = call_resonance_compute_sync(
                user_id="test_user",
                anchor_id="test_anchor",
                reaction_type="共鸣",
                opinion_embedding=[0.1] * 768,
                anchor_embedding=[0.1] * 768,
                existing_embeddings=[],
                opinion_text="测试文本",
                emotion_word="同感",
            )
            assert "value" in result
            assert "components" in result
            assert isinstance(result["value"], float)
        except Exception as e:
            # 如果 Rust 服务未运行，跳过
            if "无法连接" in str(e) or "超时" in str(e):
                pytest.skip(f"Rust 服务未运行: {e}")
            raise

    def test_sync_call_with_all_reaction_types(self):
        """所有反应类型都应能调用"""
        try:
            from shared.rust_engine_client import call_resonance_compute_sync

            for rtype in ["共鸣", "无感", "反对"]:
                result = call_resonance_compute_sync(
                    user_id="test_user",
                    anchor_id="test_anchor",
                    reaction_type=rtype,
                    opinion_embedding=[0.1] * 768,
                    anchor_embedding=[0.1] * 768,
                    existing_embeddings=[],
                )
                # 共鸣和反对应有值，无感应为 0
                if rtype == "无感":
                    assert result["value"] == 0.0
                elif rtype == "反对":
                    assert result["value"] <= 0.0
        except Exception as e:
            if "无法连接" in str(e) or "超时" in str(e):
                pytest.skip(f"Rust 服务未运行: {e}")
            raise

    def test_unexperienced_returns_zero(self):
        """未体验 → value 为 0"""
        try:
            from shared.rust_engine_client import call_resonance_compute_sync

            result = call_resonance_compute_sync(
                user_id="test_user",
                anchor_id="test_anchor",
                reaction_type="未体验",
                opinion_embedding=[0.1] * 768,
                anchor_embedding=[0.1] * 768,
                existing_embeddings=[],
            )
            # 未体验不计入共鸣值
            assert result["value"] == 0.0
        except Exception as e:
            if "无法连接" in str(e) or "超时" in str(e):
                pytest.skip(f"Rust 服务未运行: {e}")
            raise

    def test_connection_error_handling(self):
        """连接失败应抛出 RustEngineError"""
        import os
        from shared import rust_engine_client

        # 临时修改 URL 到不存在的端口
        original_url = rust_engine_client.RESONANCE_SERVICE_URL
        rust_engine_client.RESONANCE_SERVICE_URL = "http://localhost:19999"
        rust_engine_client.REQUEST_TIMEOUT = 0.5

        try:
            from shared.rust_engine_client import call_resonance_compute_sync, RustEngineError
            with pytest.raises(RustEngineError):
                call_resonance_compute_sync(
                    user_id="test",
                    anchor_id="test",
                    reaction_type="共鸣",
                    opinion_embedding=[0.1] * 768,
                    anchor_embedding=[0.1] * 768,
                    existing_embeddings=[],
                )
        finally:
            rust_engine_client.RESONANCE_SERVICE_URL = original_url
            rust_engine_client.REQUEST_TIMEOUT = 5.0

    def test_components_structure(self):
        """返回的 components 应包含所有分量"""
        try:
            from shared.rust_engine_client import call_resonance_compute_sync

            result = call_resonance_compute_sync(
                user_id="test_user",
                anchor_id="test_anchor",
                reaction_type="共鸣",
                opinion_embedding=[0.1] * 768,
                anchor_embedding=[0.1] * 768,
                existing_embeddings=[],
                opinion_text="测试",
                emotion_word="震撼",
            )
            components = result["components"]
            expected_keys = [
                "resonance_weight", "depth", "relevance_raw",
                "relevance_sigmoid", "novelty",
                "harmful_penalty", "unexperienced_penalty",
            ]
            for key in expected_keys:
                assert key in components, f"缺少分量: {key}"
        except Exception as e:
            if "无法连接" in str(e) or "超时" in str(e):
                pytest.skip(f"Rust 服务未运行: {e}")
            raise
