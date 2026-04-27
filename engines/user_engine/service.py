"""
用户管理引擎 — gRPC 服务实现

将 user_manager 的逻辑暴露为 gRPC 服务。
覆盖:
- UserEngine (engines.proto): 引擎间调用
- UserService (gateway.proto): 客户端调用

数据层: PostgreSQL
"""

import logging
import sys
import time
import uuid
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent))
from shared.engine_base import EngineConfig, EngineServicer, timing_decorator
from shared.db import get_pg, put_pg, get_redis

# gRPC 生成代码
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src" / "proto" / "generated" / "python"))
from engines import engines_pb2_grpc
from engines import engines_pb2
from common import common_pb2

from user_manager import (
    TrustLevel, AnonymousIdentity, UserProfile, RelationshipState,
    generate_anonymous_identity,
    compute_trust_level, get_trust_permissions,
    compute_resonance_credit, compute_marker_credit,
    check_confidant_eligibility, express_confidant_intent,
    RelationshipManager,
)

logger = logging.getLogger(__name__)


class UserEngineServicer(EngineServicer):
    """用户管理引擎 gRPC 服务 — PostgreSQL 持久化"""

    def __init__(self, config: EngineConfig):
        super().__init__(config)

        # RelationshipManager 内存缓存 (从 PG 加载, 更新后写回)
        self._relationship_mgr = RelationshipManager()
        self._load_relationships()

        # 匿名身份缓存 (PG 中已有, 短期内存缓存)
        self._identity_cache: dict[str, AnonymousIdentity] = {}

    def _load_relationships(self):
        """从 PostgreSQL 加载所有关系记录到内存"""
        try:
            pg = get_pg()
            cur = pg.cursor()
            cur.execute("""
                SELECT user_a_hash, user_b_hash, score_a_to_b, score_b_to_a,
                       topic_diversity, trust_level, a_intent_expressed,
                       b_intent_expressed, is_confidant,
                       EXTRACT(EPOCH FROM first_resonance_at) as first_ts,
                       EXTRACT(EPOCH FROM last_resonance_at) as last_ts
                FROM relationships
            """)
            rows = cur.fetchall()
            for row in rows:
                state = RelationshipState(
                    user_a=row[0], user_b=row[1],
                    relationship_score_a_to_b=row[2],
                    relationship_score_b_to_a=row[3],
                    topic_diversity=row[4],
                    trust_level=TrustLevel(row[5]) if row[5] is not None else TrustLevel.L0_BROWSE,
                    a_intent_expressed=row[6],
                    b_intent_expressed=row[7],
                    is_confidant=row[8],
                    first_resonance_at=row[9] or 0,
                    last_resonance_at=row[10] or 0,
                )
                key = tuple(sorted([row[0], row[1]]))
                self._relationship_mgr._relationships[key] = state
            logger.info(f"加载了 {len(rows)} 条关系记录")
        except Exception as e:
            logger.warning(f"加载关系记录失败 (首次启动可能表为空): {e}")

    def _save_relationship(self, user_a: str, user_b: str):
        """将内存中的关系记录写回 PostgreSQL"""
        key = tuple(sorted([user_a, user_b]))
        state = self._relationship_mgr._relationships.get(key)
        if not state:
            return
        try:
            pg = get_pg()
            cur = pg.cursor()
            cur.execute("""
                INSERT INTO relationships
                    (user_a_hash, user_b_hash, score_a_to_b, score_b_to_a,
                     topic_diversity, trust_level, a_intent_expressed,
                     b_intent_expressed, is_confidant,
                     first_resonance_at, last_resonance_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s,
                        to_timestamp(%s), to_timestamp(%s), NOW())
                ON CONFLICT (user_a_hash, user_b_hash) DO UPDATE SET
                    score_a_to_b = EXCLUDED.score_a_to_b,
                    score_b_to_a = EXCLUDED.score_b_to_a,
                    topic_diversity = EXCLUDED.topic_diversity,
                    trust_level = EXCLUDED.trust_level,
                    a_intent_expressed = EXCLUDED.a_intent_expressed,
                    b_intent_expressed = EXCLUDED.b_intent_expressed,
                    is_confidant = EXCLUDED.is_confidant,
                    last_resonance_at = EXCLUDED.last_resonance_at,
                    updated_at = NOW()
            """, (
                state.user_a, state.user_b,
                state.relationship_score_a_to_b, state.relationship_score_b_to_a,
                state.topic_diversity, state.trust_level.value,
                state.a_intent_expressed, state.b_intent_expressed,
                state.is_confidant,
                state.first_resonance_at or 0, state.last_resonance_at or 0,
            ))
        except Exception as e:
            logger.error(f"保存关系记录失败: {e}")

    def register_services(self, server):
        engines_pb2_grpc.add_UserEngineServicer_to_server(self, server)
        logger.info("UserEngine service 已注册")

    # --------------------------------------------------------
    # gRPC PascalCase 别名
    # --------------------------------------------------------

    _TRUST_LEVEL_MAP = {
        "L0_BROWSE": 1,
        "L1_TRACE_VISIBLE": 2,
        "L2_OPINION_REPLY": 3,
        "L3_ASYNC_MESSAGE": 4,
        "L4_REALTIME_CHAT": 5,
        "L5_GROUP_CHAT": 6,
    }

    def GetMarkerCredit(self, request, context):
        result = self.get_marker_credit(request)
        return engines_pb2.GetMarkerCreditResponse(
            credit_score=result.get("credit_score", 0.5),
            total_marks=result.get("total_marks", 0),
            time_decayed_credit=result.get("time_decayed_credit", 0.5),
        )

    def GetMarkerHistory(self, request, context):
        result = self.get_marker_history(request)
        entries = [
            engines_pb2.MarkerHistoryEntry(
                content_id=e.get("content_id", ""),
                was_accurate=e.get("was_accurate", False),
                timestamp=e.get("timestamp", 0),
            )
            for e in result.get("entries", [])
        ]
        return engines_pb2.GetMarkerHistoryResponse(entries=entries)

    def UpdateTrustLevel(self, request, context):
        result = self.update_trust_level(request)
        old_name = result.get("old_level", "L0_BROWSE")
        new_name = result.get("new_level", "L0_BROWSE")
        return engines_pb2.UpdateTrustLevelResponse(
            updated=result.get("updated", False),
            old_level=self._TRUST_LEVEL_MAP.get(old_name, 1),
            new_level=self._TRUST_LEVEL_MAP.get(new_name, 1),
            confidant_eligible=result.get("confidant_eligible", False),
        )

    def GenerateAnonymousIdentity(self, request, context):
        result = self.generate_anonymous_identity(request)
        ident = result.get("identity", {})
        return engines_pb2.GenerateAnonymousIdentityResponse(
            identity=common_pb2.AnonymousIdentity(
                identity_id=ident.get("identity_id", ""),
                display_name=ident.get("display_name", ""),
                avatar_seed=ident.get("avatar_seed", ""),
                anchor_id=ident.get("anchor_id", ""),
                is_fixed=ident.get("is_fixed", False),
            ),
        )

    def CheckConfidantEligibility(self, request, context):
        result = self.check_confidant_eligibility(request)
        return engines_pb2.CheckConfidantEligibilityResponse(
            eligible=result.get("eligible", False),
            score_met=result.get("score_met", False),
            time_met=result.get("time_met", False),
            days_since_first=result.get("days_since_first", 0),
        )

    # --------------------------------------------------------
    # UserEngine (引擎间调用)
    # --------------------------------------------------------

    @timing_decorator
    def get_marker_credit(self, request) -> dict:
        """查询标记者信用 (从 PostgreSQL)"""
        marker_hash = request.marker_token_hash if hasattr(request, 'marker_token_hash') else request
        current_ts = request.current_timestamp if hasattr(request, 'current_timestamp') else time.time()

        try:
            pg = get_pg()
            cur = pg.cursor()
            cur.execute("""
                SELECT marker_credit, total_reactions,
                       EXTRACT(EPOCH FROM updated_at) as last_ts
                FROM users WHERE internal_token = %s
            """, (marker_hash,))
            row = cur.fetchone()
            put_pg(pg)

            if not row:
                return {
                    "credit_score": 0.5,
                    "total_marks": 0,
                    "time_decayed_credit": 0.5,
                }

            credit = row[0] or 0.5
            total = row[1] or 0
            last_ts = row[2] or current_ts

            # 时间衰减 (>30天不活跃 → 向0.5衰减)
            days_inactive = (current_ts - last_ts) / 86400
            if days_inactive > 30:
                decay_factor = 0.5 ** ((days_inactive - 30) / 90)
                decayed = 0.5 + (credit - 0.5) * decay_factor
            else:
                decayed = credit

            return {
                "credit_score": credit,
                "total_marks": total,
                "time_decayed_credit": round(max(0.0, min(1.0, decayed)), 4),
            }
        except Exception as e:
            logger.error(f"查询标记者信用失败: {e}")
            return {
                "credit_score": 0.5,
                "total_marks": 0,
                "time_decayed_credit": 0.5,
            }

    @timing_decorator
    def get_marker_history(self, request) -> dict:
        """查询标记者历史 (从 PostgreSQL)"""
        marker_hash = request.marker_token_hash if hasattr(request, 'marker_token_hash') else request
        limit = request.limit if hasattr(request, 'limit') else 50

        try:
            pg = get_pg()
            cur = pg.cursor()
            cur.execute("""
                SELECT content_id, level, harmful_weight,
                       EXTRACT(EPOCH FROM decided_at) as ts
                FROM governance_decisions
                WHERE content_id IN (
                    SELECT content_id FROM governance_decisions
                    WHERE decided_at > NOW() - INTERVAL '90 days'
                    ORDER BY decided_at DESC LIMIT %s
                )
                ORDER BY decided_at DESC
            """, (limit,))
            rows = cur.fetchall()
            entries = [
                {
                    "content_id": r[0],
                    "was_accurate": r[1] == "L0_正常",
                    "timestamp": r[3] or 0,
                }
                for r in rows
            ]
            return {"entries": entries}
        except Exception as e:
            logger.error(f"查询标记者历史失败: {e}")
            return {"entries": []}

    @timing_decorator
    def update_trust_level(self, request) -> dict:
        """更新信任级别"""
        user_a = request.user_a_id if hasattr(request, 'user_a_id') else request.get("user_a_id")
        user_b = request.user_b_id if hasattr(request, 'user_b_id') else request.get("user_b_id")
        score_ab = request.new_score_a_to_b if hasattr(request, 'new_score_a_to_b') else request.get("new_score_a_to_b", 0)
        score_ba = request.new_score_b_to_a if hasattr(request, 'new_score_b_to_a') else request.get("new_score_b_to_a", 0)
        topics = request.topic_diversity if hasattr(request, 'topic_diversity') else request.get("topic_diversity", 0)
        current_ts = request.current_timestamp if hasattr(request, 'current_timestamp') else time.time()

        state = self._relationship_mgr.get_or_create(user_a, user_b)
        old_level = state.trust_level

        self._relationship_mgr.update_scores(user_a, user_b, score_ab, score_ba, topics)
        new_level = self._relationship_mgr.compute_and_update_level(user_a, user_b, current_ts)

        # 写回 PG
        self._save_relationship(user_a, user_b)

        eligibility = check_confidant_eligibility(state, current_ts)

        return {
            "updated": True,
            "old_level": old_level.name,
            "new_level": new_level.name,
            "confidant_eligible": eligibility["eligible"],
        }

    @timing_decorator
    def generate_anonymous_identity(self, request) -> dict:
        """生成匿名身份 (写入 PostgreSQL)"""
        token_hash = request.internal_token_hash if hasattr(request, 'internal_token_hash') else request.get("internal_token_hash")
        anchor_id = request.anchor_id if hasattr(request, 'anchor_id') else request.get("anchor_id")

        cache_key = f"{token_hash}:{anchor_id}"
        if cache_key in self._identity_cache:
            identity = self._identity_cache[cache_key]
        else:
            # 先查 PG
            try:
                pg = get_pg()
                cur = pg.cursor()
                cur.execute("""
                    SELECT display_name, avatar_seed, is_fixed
                    FROM anonymous_identities
                    WHERE internal_token_hash = %s AND anchor_id = %s
                """, (token_hash, anchor_id))
                row = cur.fetchone()
                put_pg(pg)
                if row:
                    return {
                        "identity_id": cache_key,
                        "display_name": row[0],
                        "avatar_seed": row[1],
                        "anchor_id": anchor_id,
                        "is_fixed": row[2],
                    }
                else:
                    identity = generate_anonymous_identity(token_hash, anchor_id)
                    # 写入 PG
                    cur.execute("""
                        INSERT INTO anonymous_identities
                            (internal_token_hash, display_name, avatar_seed, anchor_id, is_fixed)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (internal_token_hash, anchor_id) DO NOTHING
                    """, (token_hash, identity.display_name, identity.avatar_seed, anchor_id, identity.is_fixed))
            except Exception as e:
                logger.error(f"匿名身份操作失败: {e}")
                identity = generate_anonymous_identity(token_hash, anchor_id)

            self._identity_cache[cache_key] = identity

        return {
            "identity": {
                "identity_id": identity.identity_id,
                "display_name": identity.display_name,
                "avatar_seed": identity.avatar_seed,
                "anchor_id": identity.anchor_id,
                "is_fixed": identity.is_fixed,
            }
        }

    @timing_decorator
    def check_confidant_eligibility(self, request) -> dict:
        """检查知己资格"""
        user_a = request.user_a_id if hasattr(request, 'user_a_id') else request.get("user_a_id")
        user_b = request.user_b_id if hasattr(request, 'user_b_id') else request.get("user_b_id")
        current_ts = request.current_timestamp if hasattr(request, 'current_timestamp') else time.time()

        state = self._relationship_mgr.get_or_create(user_a, user_b)
        return check_confidant_eligibility(state, current_ts)

    # --------------------------------------------------------
    # UserService (客户端调用)
    # --------------------------------------------------------

    @timing_decorator
    def get_profile(self, request) -> dict:
        """获取用户档案 (从 PostgreSQL)"""
        user_id = request.get("user_id", "") if isinstance(request, dict) else str(request)

        try:
            pg = get_pg()
            cur = pg.cursor()
            cur.execute("""
                SELECT id, credit_score, marker_credit,
                       EXTRACT(EPOCH FROM created_at) as created_ts
                FROM users WHERE id = %s::UUID
            """, (user_id,))
            row = cur.fetchone()

            if row:
                user = {
                    "user_id": str(row[0]),
                    "credit_score": row[1] or 0.5,
                    "marker_credit": row[2] or 0.5,
                    "total_reactions": 0,  # TODO: 从 resonance_vectors 表 COUNT
                    "total_anchors_engaged": 0,
                    "confidant_count": 0,
                    "created_at": int(row[3]) if row[3] else 0,
                }
            else:
                # 新用户
                user = {
                    "user_id": user_id,
                    "credit_score": 0.5,
                    "marker_credit": 0.5,
                    "total_reactions": 0,
                    "total_anchors_engaged": 0,
                    "confidant_count": 0,
                    "created_at": int(time.time()),
                }

            # 统计知己数
            confidant_count = sum(
                1 for r in self._relationship_mgr._relationships.values()
                if (r.user_a == user_id or r.user_b == user_id) and r.is_confidant
            )
            user["confidant_count"] = confidant_count

            # 写入 Redis 缓存 (TTL=5min)
            try:
                redis = get_redis()
                if redis:
                    import json
                    redis.setex(f"user:profile:{user_id}", 300, json.dumps(user))
            except Exception:
                pass

            return user
        except Exception as e:
            logger.error(f"获取用户档案失败: {e}")
            return {
                "user_id": user_id,
                "credit_score": 0.5,
                "marker_credit": 0.5,
                "total_reactions": 0,
                "total_anchors_engaged": 0,
                "confidant_count": 0,
                "created_at": int(time.time()),
            }

    @timing_decorator
    def list_relationships(self, request) -> dict:
        """获取关系列表"""
        user_id = request.get("user_id", "") if isinstance(request, dict) else str(request)
        min_level_name = request.get("min_level", "L1_TRACE_VISIBLE") if isinstance(request, dict) else "L1_TRACE_VISIBLE"

        try:
            min_level = TrustLevel[min_level_name]
        except KeyError:
            min_level = TrustLevel.L1_TRACE_VISIBLE

        relationships = self._relationship_mgr.get_all_relationships(user_id, min_level)

        results = []
        for r in relationships:
            other_user = r.user_b if r.user_a == user_id else r.user_a

            # 获取对方的匿名身份
            other_identity = None
            for key, ident in self._identity_cache.items():
                if key.startswith(f"{other_user}:"):
                    other_identity = ident
                    break

            results.append({
                "other_user": {
                    "display_name": other_identity.display_name if other_identity else "匿名用户",
                    "avatar_seed": other_identity.avatar_seed if other_identity else "default",
                },
                "relationship_score": r.relationship_score_a_to_b if r.user_a == user_id else r.relationship_score_b_to_a,
                "topic_diversity": r.topic_diversity,
                "trust_level": r.trust_level.name,
                "is_confidant": r.is_confidant,
                "last_resonance_at": 0,
            })

        return {"relationships": results}

    @timing_decorator
    def express_confidant_intent(self, request) -> dict:
        """表达知己意向"""
        if isinstance(request, dict):
            user_id = request.get("user_id", "")
            target_hash = request.get("target_user_internal_hash", "")
        else:
            user_id = str(request)
            target_hash = ""

        state = self._relationship_mgr.get_or_create(user_id, target_hash)

        expresser = "a" if state.user_a == user_id else "b"
        state = express_confidant_intent(state, expresser)

        # 写回 PG
        self._save_relationship(user_id, target_hash)

        eligibility = check_confidant_eligibility(state, time.time())

        if state.is_confidant:
            message = "恭喜！你们已成为知己。"
        elif eligibility["eligible"]:
            message = "已记录你的意向。当对方也有同样意向时，系统会通知你们。"
        else:
            message = "已记录你的意向。继续在更多话题上产生共鸣，即可解锁知己关系。"

        return {
            "success": True,
            "matched": state.is_confidant,
            "message": message,
        }

    @timing_decorator
    def list_confidants(self, request) -> dict:
        """获取知己列表"""
        user_id = request.get("user_id", "") if isinstance(request, dict) else str(request)

        confidants = []
        for r in self._relationship_mgr._relationships.values():
            if not r.is_confidant:
                continue
            if r.user_a != user_id and r.user_b != user_id:
                continue

            other = r.user_b if r.user_a == user_id else r.user_a
            other_identity = None
            for key, ident in self._identity_cache.items():
                if key.startswith(f"{other}:"):
                    other_identity = ident
                    break

            confidants.append({
                "confidant_id": str(uuid.uuid4()),
                "fixed_name": other_identity.display_name if other_identity else "知己",
                "fixed_avatar_url": "",
                "relationship_score": r.relationship_score_a_to_b if r.user_a == user_id else r.relationship_score_b_to_a,
                "established_at": 0,
                "last_interaction_at": 0,
            })

        return {"confidants": confidants}

    # --------------------------------------------------------
    # 内部方法
    # --------------------------------------------------------

    def register_user(self, user_id: str, device_fingerprint: str) -> dict:
        """注册/获取用户 (写入 PostgreSQL)"""
        try:
            pg = get_pg()
            cur = pg.cursor()
            # 查看是否已存在
            cur.execute("SELECT id FROM users WHERE id = %s::UUID", (user_id,))
            if not cur.fetchone():
                cur.execute("""
                    INSERT INTO users (id, phone_hash, internal_token, device_fingerprint,
                                       credit_score, marker_credit)
                    VALUES (%s::UUID, %s, %s, %s, 0.5, 0.5)
                """, (user_id, f"hash_{user_id}", user_id, device_fingerprint))
                logger.info(f"新用户注册: {user_id[:16]}...")
        except Exception as e:
            logger.error(f"注册用户失败: {e}")

        return self.get_profile({"user_id": user_id})

    def update_marker_credit(self, marker_hash: str, was_accurate: bool):
        """更新标记者信用 (写入 PostgreSQL)"""
        try:
            pg = get_pg()
            cur = pg.cursor()

            # 获取当前值
            cur.execute("SELECT marker_credit FROM users WHERE internal_token = %s", (marker_hash,))
            row = cur.fetchone()
            current_credit = row[0] if row else 0.5

            # Bayesian 更新
            # 简化: 每次准确 +0.05, 不准确 -0.03, 钳制 [0, 1]
            delta = 0.05 if was_accurate else -0.03
            new_credit = round(max(0.0, min(1.0, current_credit + delta)), 4)

            if row:
                cur.execute("""
                    UPDATE users SET marker_credit = %s, updated_at = NOW()
                    WHERE internal_token = %s
                """, (new_credit, marker_hash))
            else:
                cur.execute("""
                    INSERT INTO users (id, phone_hash, internal_token, device_fingerprint,
                                       marker_credit)
                    VALUES (gen_random_uuid(), %s, %s, 'unknown', %s)
                """, (f"hash_{marker_hash}", marker_hash, new_credit))
            put_pg(pg)
            return True

            # 记录治理决策
            cur.execute("""
                INSERT INTO governance_decisions (content_id, content_type, level, reason)
                VALUES (%s, 'marker', 'credit_update', %s)
            """, (marker_hash, f"was_accurate={was_accurate}, credit={new_credit}"))

        except Exception as e:
            logger.error(f"更新标记者信用失败: {e}")


def main():
    """启动用户引擎服务"""
    config = EngineConfig.from_yaml("user_engine")
    servicer = UserEngineServicer(config)

    print("=" * 60)
    print("  用户引擎服务 (PostgreSQL)")
    print("=" * 60)

    # 启动 gRPC 服务器
    servicer.run()


if __name__ == "__main__":
    main()
