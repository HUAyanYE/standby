"""
内容治理引擎 — gRPC 服务实现

将 rule_governance_v2 的算法暴露为 gRPC 服务。
三层检测: 端侧初筛 → 云端模型 → LLM 深度判定
本服务实现第二层 (规则 + 信用加权)。

数据层:
- PostgreSQL: 标记者信用 (users.marker_credit)
- MongoDB: 治理决策日志
"""

import logging
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src" / "proto" / "generated" / "python"))
from shared.engine_base import EngineConfig, EngineServicer, timing_decorator
from shared.db import get_pg, put_pg
from engines import engines_pb2_grpc
from engines import engines_pb2
from common import common_pb2

logger = logging.getLogger(__name__)

from rule_governance_v2 import (
    GovernanceLevel, DetectionResult, MarkerRecord, ContentReaction,
    GovernanceDecision,
    update_marker_credit_v2, get_time_decayed_credit,
    compute_harmful_weight_v2, evaluate_governance_v2,
    detect_coordinated_marking_v2, detect_topic_type_attack_v2,
    detect_velocity_anomaly,
)


class GovernanceEngineServicer(EngineServicer):
    """内容治理引擎 gRPC 服务 — PostgreSQL + MongoDB"""

    def __init__(self, config: EngineConfig):
        super().__init__(config)

        # 内存缓存 (从 PG 加载, 更新后写回)
        self._marker_credits: dict[str, MarkerRecord] = {}
        self._load_marker_credits()

        # 批量写入缓冲
        self._pending_credit_updates: dict[str, float] = {}
        self._flush_interval = 10  # 秒
        self._start_flush_thread()

    def _load_marker_credits(self):
        """从 PostgreSQL 加载标记者信用"""
        try:
            pg = get_pg()
            cur = pg.cursor()
            cur.execute("""
                SELECT internal_token, marker_credit
                FROM users
                WHERE marker_credit != 0.5
                ORDER BY updated_at DESC
                LIMIT 1000
            """)
            rows = cur.fetchall()
            put_pg(pg)
            for row in rows:
                token_hash = row[0]
                credit = row[1] or 0.5
                self._marker_credits[token_hash] = MarkerRecord(
                    token_hash=token_hash,
                    credit_score=credit,
                    total_marks=0,  # 简化: 从 governance_decisions 统计
                    accurate_marks=0,
                )
            logger.info(f"加载了 {len(self._marker_credits)} 条标记者信用记录")
        except Exception as e:
            logger.warning(f"加载标记者信用失败: {e}")

    def _start_flush_thread(self):
        """启动批量写入后台线程"""
        import threading
        def _flush_loop():
            while True:
                import time
                time.sleep(self._flush_interval)
                self._flush_pending_credits()
        t = threading.Thread(target=_flush_loop, daemon=True)
        t.start()

    def _flush_pending_credits(self):
        """批量刷入待写入的信用更新"""
        if not self._pending_credit_updates:
            return

        updates = dict(self._pending_credit_updates)
        self._pending_credit_updates.clear()

        try:
            pg = get_pg()
            cur = pg.cursor()
            # 批量更新
            for token_hash, credit in updates.items():
                cur.execute("""
                    UPDATE users SET marker_credit = %s, updated_at = NOW()
                    WHERE internal_token = %s
                """, (credit, token_hash))
                if cur.rowcount == 0:
                    cur.execute("""
                        INSERT INTO users (id, phone_hash, internal_token, device_fingerprint, marker_credit)
                        VALUES (gen_random_uuid(), %s, %s, 'unknown', %s)
                        ON CONFLICT (internal_token) DO UPDATE SET marker_credit = EXCLUDED.marker_credit
                    """, (f"hash_{token_hash}", token_hash, credit))
            put_pg(pg)
            logger.info(f"批量刷入 {len(updates)} 条标记者信用更新")
        except Exception as e:
            logger.error(f"批量刷入标记者信用失败: {e}")

    def _save_marker_credit(self, token_hash: str, credit: float):
        """缓冲标记者信用更新 (批量写入)"""
        self._pending_credit_updates[token_hash] = credit
        # 内存缓存立即更新
        if token_hash in self._marker_credits:
            self._marker_credits[token_hash].credit_score = credit

    def _save_decision(self, content_id: str, level: str, harmful_weight: float,
                       marker_avg_credit: float, reason: str, actions: list):
        """保存治理决策到 MongoDB"""
        try:
            mongo = get_mongo()
            mongo.governance_logs.insert_one({
                "content_id": content_id,
                "level": level,
                "harmful_weight": harmful_weight,
                "marker_avg_credit": marker_avg_credit,
                "reason": reason,
                "actions": actions,
                "timestamp": time.time(),
            })
        except Exception as e:
            logger.error(f"保存治理决策日志失败: {e}")

    def register_services(self, server):
        engines_pb2_grpc.add_GovernanceEngineServicer_to_server(self, server)
        logger.info("GovernanceEngine service 已注册")

    # --------------------------------------------------------
    # gRPC PascalCase 别名
    # --------------------------------------------------------

    _LEVEL_MAP = {
        "L0_正常": 1, "L1_观察": 2, "L2_降权": 3,
        "L3_暂停": 4, "L4_移除": 5, "争议": 6,
    }

    def EvaluateContent(self, request, context):
        result = self.evaluate_content(request)
        d = result.get("decision", {})
        level_str = d.get("level", "L0_正常")
        detection = d.get("detection", "")
        reason = d.get("reason", "")
        if detection and detection not in reason:
            reason = f"[{detection}] {reason}"
        return engines_pb2.EvaluateContentResponse(
            evaluated=result.get("evaluated", False),
            decision=common_pb2.GovernanceDecision(
                content_id=d.get("content_id", ""),
                level=self._LEVEL_MAP.get(level_str, 1),
                harmful_weight=d.get("harmful_weight", 0),
                marker_avg_credit=d.get("marker_avg_credit", 0),
                reason=reason,
                actions=d.get("actions", []),
            ),
        )

    def CheckMarkCredibility(self, request, context):
        result = self.check_mark_credibility(request)
        return engines_pb2.CheckMarkCredibilityResponse(
            credit_score=result.get("credit_score", 0.5),
            total_marks=result.get("total_marks", 0),
            accuracy_rate=result.get("accuracy_rate", 0),
            is_suspicious=result.get("is_suspicious", False),
        )

    def DetectAnomaly(self, request, context):
        result = self.detect_anomaly(request)
        anomalies = [
            engines_pb2.AnomalyReport(
                anomaly_type=a["anomaly_type"],
                description=a["description"],
                severity=a["severity"],
                actions=a["actions"],
            )
            for a in result.get("anomalies", [])
        ]
        return engines_pb2.DetectAnomalyResponse(
            anomaly_detected=result.get("anomaly_detected", False),
            anomalies=anomalies,
        )

    def UpdateMarkerCredit(self, request, context):
        result = self.update_marker_credit_batch(request)
        return engines_pb2.UpdateMarkerCreditResponse(
            success=result.get("success", False),
            updated_count=result.get("updated_count", 0),
        )

    @timing_decorator
    def evaluate_content(self, request) -> dict:
        """评估内容的治理级别"""
        content_id = request.content_id if hasattr(request, 'content_id') else request.get("content_id")

        # 构建 ContentReaction
        if hasattr(request, 'reaction_summary') and request.reaction_summary:
            rs = request.reaction_summary
            reactions = ContentReaction(
                anchor_id=content_id,
                resonance=getattr(rs, 'resonance_count', 0),
                neutral=getattr(rs, 'neutral_count', 0),
                opposition=getattr(rs, 'opposition_count', 0),
                unexperienced=getattr(rs, 'unexperienced_count', 0),
                harmful=getattr(rs, 'harmful_count', 0),
            )
        elif isinstance(request, dict):
            rs = request.get("reaction_summary", {})
            reactions = ContentReaction(
                anchor_id=content_id,
                resonance=rs.get("resonance_count", 0),
                neutral=rs.get("neutral_count", 0),
                opposition=rs.get("opposition_count", 0),
                unexperienced=rs.get("unexperienced_count", 0),
                harmful=rs.get("harmful_count", 0),
            )
        else:
            return {"evaluated": False, "error": "缺少 reaction_summary"}

        # 获取标记者信用
        marker_credits = []
        if hasattr(request, 'marker_credits'):
            marker_credits = list(request.marker_credits)

        # 评估 (v2)
        decision = evaluate_governance_v2(reactions, marker_credits, current_ts=time.time())

        logger.info(
            f"治理评估: {content_id} → {decision.level.value} "
            f"(有害{reactions.harmful_ratio:.0%}, 原因: {decision.reason[:30]})"
        )

        result = {
            "evaluated": True,
            "decision": {
                "content_id": content_id,
                "level": decision.level.value,
                "detection": decision.detection.value,
                "harmful_weight": round(decision.harmful_weight, 4),
                "marker_avg_credit": round(decision.marker_avg_credit, 4),
                "reason": decision.reason,
                "actions": decision.actions,
            },
        }

        # 保存决策日志到 Mongo
        self._save_decision(
            content_id, decision.level.value,
            decision.harmful_weight, decision.marker_avg_credit,
            decision.reason, decision.actions,
        )

        return result

    @timing_decorator
    def check_mark_credibility(self, request) -> dict:
        """检查标记者可信度 (从内存缓存)"""
        marker_hash = request.marker_token_hash if hasattr(request, 'marker_token_hash') else request

        marker = self._marker_credits.get(marker_hash)
        if not marker:
            return {
                "credit_score": 0.5,
                "total_marks": 0,
                "accuracy_rate": 0.0,
                "is_suspicious": False,
            }

        decayed = get_time_decayed_credit(marker, time.time())
        is_suspicious = marker.total_marks > 200 or (marker.total_marks >= 10 and marker.credit_score < 0.3)

        return {
            "credit_score": marker.credit_score,
            "total_marks": marker.total_marks,
            "accuracy_rate": marker.accurate_marks / max(1, marker.total_marks),
            "time_decayed_credit": decayed,
            "is_suspicious": is_suspicious,
        }

    @timing_decorator
    def detect_anomaly(self, request) -> dict:
        """检测异常模式"""
        anchor_id = request.anchor_id if hasattr(request, 'anchor_id') else request.get("anchor_id", "")
        anomalies = []

        # 1. 协同攻击检测
        if hasattr(request, 'mark_timestamps'):
            timestamps = list(request.mark_timestamps)
            marker_ids = list(request.marker_ids) if hasattr(request, 'marker_ids') else []
        else:
            timestamps = request.get("mark_timestamps", [])
            marker_ids = request.get("marker_ids", [])

        if timestamps and marker_ids:
            is_coordinated, reason = detect_coordinated_marking_v2(timestamps, marker_ids)
            if is_coordinated:
                anomalies.append({
                    "anomaly_type": "coordinated_attack",
                    "description": reason,
                    "severity": 0.8,
                    "actions": ["标记权重降低", "入队人工审核"],
                })

        # 2. 速度异常检测
        if timestamps:
            is_velocity, reason = detect_velocity_anomaly(timestamps, "check")
            if is_velocity:
                anomalies.append({
                    "anomaly_type": "velocity",
                    "description": reason,
                    "severity": 0.7,
                    "actions": ["反应无效化", "信用分惩罚"],
                })

        # 3. 话题类型打击检测
        if hasattr(request, 'reactions_by_type'):
            reactions_by_type = dict(request.reactions_by_type)
        else:
            reactions_by_type = request.get("reactions_by_type", {})

        if reactions_by_type:
            type_data = {}
            for rtype, count in reactions_by_type.items():
                type_data[rtype] = [{"unexperienced": False}] * count

            is_type_attack, reason = detect_topic_type_attack_v2(type_data)
            if is_type_attack:
                anomalies.append({
                    "anomaly_type": "type_targeting",
                    "description": reason,
                    "severity": 0.6,
                    "actions": ["标记权重归零"],
                })

        return {
            "anomaly_detected": len(anomalies) > 0,
            "anomalies": anomalies,
        }

    @timing_decorator
    def update_marker_credit_batch(self, request) -> dict:
        """批量更新标记者信用 (写入 PG)"""
        updates = request.updates if hasattr(request, 'updates') else request.get("updates", [])
        updated = 0

        for update in updates:
            marker_hash = update.marker_token_hash if hasattr(update, 'marker_token_hash') else update.get("marker_token_hash")
            was_accurate = update.was_accurate if hasattr(update, 'was_accurate') else update.get("was_accurate")
            ts = update.timestamp if hasattr(update, 'timestamp') else update.get("timestamp", time.time())

            if marker_hash not in self._marker_credits:
                self._marker_credits[marker_hash] = MarkerRecord(token_hash=marker_hash)

            self._marker_credits[marker_hash] = update_marker_credit_v2(
                self._marker_credits[marker_hash],
                was_accurate,
                current_ts=ts,
            )

            # 写回 PG
            new_credit = self._marker_credits[marker_hash].credit_score
            self._save_marker_credit(marker_hash, new_credit)
            updated += 1

        return {"success": True, "updated_count": updated}


def main():
    config = EngineConfig.from_yaml("governance_engine")
    servicer = GovernanceEngineServicer(config)
    servicer.run()


if __name__ == "__main__":
    main()
