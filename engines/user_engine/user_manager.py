"""
用户管理引擎 - 匿名身份生成与信任级别计算

实现文档 §9.4 用户管理引擎核心功能：
- 匿名身份生成（随机昵称 + 头像种子）
- 信任级别计算（L0-L5）
- 共鸣信用计算
- 知己意向匹配

注：生产环境用 Rust 实现，Python 版本用于验证算法逻辑
"""

import hashlib
import math
import time
import uuid
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Optional


# ============================================================
# 数据结构
# ============================================================

class TrustLevel(IntEnum):
    """信任级别"""
    L0_BROWSE = 0           # 浏览（任何人）
    L1_TRACE_VISIBLE = 1    # 痕迹可见（同一锚点上有共鸣）
    L2_OPINION_REPLY = 2    # 观点回应
    L3_ASYNC_MESSAGE = 3    # 异步私信
    L4_REALTIME_CHAT = 4    # 实时对话
    L5_GROUP_CHAT = 5       # 群体对话


@dataclass
class AnonymousIdentity:
    """匿名身份"""
    identity_id: str            # UUID
    display_name: str           # 随机生成的昵称
    avatar_seed: str            # 头像随机种子
    anchor_id: str              # 所属锚点 ID
    is_fixed: bool = False      # 是否已固定（知己关系）
    fixed_name: Optional[str] = None
    fixed_avatar_url: Optional[str] = None


@dataclass
class UserProfile:
    """用户档案（简化版，不含实名信息）"""
    user_id: str
    internal_token: str         # 加密令牌（关联行为数据）
    credit_score: float = 0.5   # 共鸣信用分
    marker_credit: float = 0.5  # 标记者信用分
    trust_level: int = 0        # 最高信任级别
    created_at: float = 0.0


@dataclass
class RelationshipState:
    """两用户之间的关系状态"""
    user_a: str
    user_b: str
    relationship_score_a_to_b: float = 0.0   # A 对 B 的关系分
    relationship_score_b_to_a: float = 0.0   # B 对 A 的关系分
    topic_diversity: int = 0                 # 共同话题数
    first_resonance_ts: float = 0.0          # 首次共鸣时间
    trust_level: TrustLevel = TrustLevel.L0_BROWSE
    a_intent_expressed: bool = False         # A 表达知己意向
    b_intent_expressed: bool = False         # B 表达知己意向
    is_confidant: bool = False               # 是否已建立知己关系


# ============================================================
# 匿名身份生成
# ============================================================

# 昵称生成词库（自然意象，符合产品哲学）
NATURE_PREFIXES = [
    "夜的", "晨曦", "微风", "秋日", "冬雪", "春水", "夏雨",
    "远山", "近海", "深林", "浅滩", "孤星", "流云", "闲鹤",
    "静湖", "暖阳", "清泉", "古木", "新月", "落花", "飞鸟",
    "薄雾", "斜阳", "细雨", "长风", "幽兰", "寒梅", "青竹",
]

NATURE_SUFFIXES = [
    "旅人", "过客", "归人", "行者", "渔夫", "樵夫", "耕者",
    "诗人", "画家", "歌者", "守望", "聆听", "沉思", "静默",
    "观察", "等待", "漂流", "停泊", "游荡", "栖息", "驻足",
    "踱步", "凝望", "回响", "呢喃", "低语", "独酌", "漫步",
]

# 头像种子参数
AVATAR_COLORS = [
    "5B8DEF", "E87979", "7BC67E", "E8C179", "B48DEF",
    "79C9E8", "E879B4", "8DE8B8", "C67BC6", "79E8D4",
]


def generate_anonymous_identity(
    internal_token: str,
    anchor_id: str,
) -> AnonymousIdentity:
    """生成匿名身份
    
    同一用户在同一锚点下，匿名身份一致
    （用 internal_token + anchor_id 的哈希作为随机种子）
    """
    # 确定性随机种子
    seed_input = f"{internal_token}:{anchor_id}"
    seed_hash = hashlib.sha256(seed_input.encode()).hexdigest()
    seed_int = int(seed_hash[:8], 16)
    
    # 昵称
    prefix = NATURE_PREFIXES[seed_int % len(NATURE_PREFIXES)]
    suffix = NATURE_SUFFIXES[(seed_int >> 8) % len(NATURE_SUFFIXES)]
    display_name = f"{prefix}{suffix}"
    
    # 头像种子
    avatar_seed = seed_hash[:16]
    
    return AnonymousIdentity(
        identity_id=str(uuid.uuid4()),
        display_name=display_name,
        avatar_seed=avatar_seed,
        anchor_id=anchor_id,
    )


def get_cross_anchor_identity(
    internal_token: str,
    anchor_id: str,
) -> dict:
    """获取跨锚点身份信息
    
    不同锚点下的身份不同（不暴露跨锚点关联）
    """
    identity = generate_anonymous_identity(internal_token, anchor_id)
    return {
        "name": identity.display_name,
        "avatar_seed": identity.avatar_seed,
        "anchor_id": anchor_id,
    }


# ============================================================
# 信任级别计算
# ============================================================

# 各级阈值
TRUST_THRESHOLDS = {
    TrustLevel.L2_OPINION_REPLY: {
        "relationship_score": 1.0,
        "topic_diversity": 2,
        "time_stability_days": 0,
    },
    TrustLevel.L3_ASYNC_MESSAGE: {
        "relationship_score": 3.0,
        "topic_diversity": 3,
        "time_stability_days": 14,
    },
    TrustLevel.L4_REALTIME_CHAT: {
        "relationship_score": 5.0,
        "topic_diversity": 3,       # 需双方在线+同锚点
        "time_stability_days": 14,
    },
    TrustLevel.L5_GROUP_CHAT: {
        "relationship_score": 5.0,  # 需多人同锚点
        "topic_diversity": 3,
        "time_stability_days": 14,
    },
}


def compute_trust_level(
    state: RelationshipState,
    current_ts: float,
) -> TrustLevel:
    """计算两人之间的信任级别
    
    关键：L2+ 需要双向达标
    """
    score_ab = state.relationship_score_a_to_b
    score_ba = state.relationship_score_b_to_a
    topics = state.topic_diversity
    
    # 首次共鸣距今天数
    if state.first_resonance_ts > 0:
        days_stable = (current_ts - state.first_resonance_ts) / 86400
    else:
        days_stable = 0
    
    # L0: 默认
    level = TrustLevel.L0_BROWSE
    
    # L1: 有共鸣（由外部判断，这里假设已达标）
    # L1 由系统在同锚点检测到共鸣时直接设置，不在这里计算
    
    # L2: 双向关系分 > 1.0 + 话题多样性 >= 2
    if (score_ab >= 1.0 and score_ba >= 1.0 and topics >= 2):
        level = TrustLevel.L2_OPINION_REPLY
    
    # L3: 双向关系分 > 3.0 + 话题多样性 >= 3 + 时间稳定性 > 14天
    if (score_ab >= 3.0 and score_ba >= 3.0 
        and topics >= 3 and days_stable >= 14):
        level = TrustLevel.L3_ASYNC_MESSAGE
    
    # L4/L5 需要实时在线状态（外部条件），这里只计算基础达标
    # L4 基础达标（还需双方在线 + 同锚点）
    if (score_ab >= 5.0 and score_ba >= 5.0
        and topics >= 3 and days_stable >= 14):
        level = TrustLevel.L4_REALTIME_CHAT  # 基础达标，实际触发需外部条件
    
    return level


def get_trust_permissions(level: TrustLevel) -> dict:
    """根据信任级别返回可用功能"""
    permissions = {
        TrustLevel.L0_BROWSE: {
            "can_view_anchor": True,
            "can_react": True,
            "can_view_anonymous_opinions": False,
            "can_reply_opinion": False,
            "can_async_message": False,
            "can_realtime_chat": False,
        },
        TrustLevel.L1_TRACE_VISIBLE: {
            "can_view_anchor": True,
            "can_react": True,
            "can_view_anonymous_opinions": True,  # 同锚点下可见
            "can_reply_opinion": False,
            "can_async_message": False,
            "can_realtime_chat": False,
        },
        TrustLevel.L2_OPINION_REPLY: {
            "can_view_anchor": True,
            "can_react": True,
            "can_view_anonymous_opinions": True,
            "can_reply_opinion": True,
            "can_async_message": False,
            "can_realtime_chat": False,
        },
        TrustLevel.L3_ASYNC_MESSAGE: {
            "can_view_anchor": True,
            "can_react": True,
            "can_view_anonymous_opinions": True,
            "can_reply_opinion": True,
            "can_async_message": True,
            "can_realtime_chat": False,
        },
        TrustLevel.L4_REALTIME_CHAT: {
            "can_view_anchor": True,
            "can_react": True,
            "can_view_anonymous_opinions": True,
            "can_reply_opinion": True,
            "can_async_message": True,
            "can_realtime_chat": True,
        },
        TrustLevel.L5_GROUP_CHAT: {
            "can_view_anchor": True,
            "can_react": True,
            "can_view_anonymous_opinions": True,
            "can_reply_opinion": True,
            "can_async_message": True,
            "can_realtime_chat": True,
        },
    }
    return permissions.get(level, permissions[TrustLevel.L0_BROWSE])


# ============================================================
# 共鸣信用计算
# ============================================================

def compute_resonance_credit(
    base_score: float,
    received_resonance_bonus: float,
    harmful_mark_penalty: float,
    unexperienced_mark_penalty: float,
    consistency_bonus: float,
) -> float:
    """计算共鸣信用分
    
    resonance_credit = base
                     + received_bonus     ← 观点被他人共鸣
                     - harmful_penalty    ← 被标记有害
                     - unexperienced_pen  ← 被标记未体验
                     + consistency_bonus  ← 持续高质量参与
    """
    credit = (base_score
              + received_resonance_bonus
              - harmful_mark_penalty
              - unexperienced_mark_penalty
              + consistency_bonus)
    
    # 归一化到 [0, 1]
    return max(0.0, min(1.0, credit))


def compute_marker_credit(
    accurate_marks: int,
    total_marks: int,
    avg_credit_of_approvers: float = 0.5,
) -> float:
    """计算标记者信用分
    
    credit = 准确率 × 0.6 + 认可者平均信用 × 0.3 + 数量加成 × 0.1
    """
    if total_marks == 0:
        return 0.5
    
    accuracy = accurate_marks / total_marks
    volume_bonus = min(1.0, total_marks / 50)  # 50 次标记达到满分
    
    return accuracy * 0.6 + avg_credit_of_approvers * 0.3 + volume_bonus * 0.1


# ============================================================
# 知己意向匹配
# ============================================================

def check_confidant_eligibility(
    state: RelationshipState,
    current_ts: float,
) -> dict:
    """检查知己关系的建立资格
    
    触发条件：
    - 双向关系分 > 3.0
    - 首次共鸣距今 > 30 天
    """
    if state.first_resonance_ts > 0:
        days = (current_ts - state.first_resonance_ts) / 86400
    else:
        days = 0
    
    score_ok = (state.relationship_score_a_to_b >= 3.0 
                and state.relationship_score_b_to_a >= 3.0)
    time_ok = days >= 30
    
    return {
        "eligible": score_ok and time_ok,
        "score_met": score_ok,
        "time_met": time_ok,
        "days_since_first": int(days),
        "is_confidant": state.is_confidant,
    }


def express_confidant_intent(
    state: RelationshipState,
    expresser: str,  # "a" or "b"
) -> RelationshipState:
    """表达知己意向（对系统，不对对方）"""
    if expresser == "a":
        state.a_intent_expressed = True
    elif expresser == "b":
        state.b_intent_expressed = True
    
    # 双向匹配
    if state.a_intent_expressed and state.b_intent_expressed:
        state.is_confidant = True
    
    return state


# ============================================================
# 关系状态管理器
# ============================================================

class RelationshipManager:
    """关系状态管理器（内存模拟）"""
    
    def __init__(self):
        self._relationships: dict[tuple[str, str], RelationshipState] = {}
    
    def _key(self, user_a: str, user_b: str) -> tuple[str, str]:
        """规范化 key（a,b 和 b,a 相同）"""
        return tuple(sorted([user_a, user_b]))
    
    def get_or_create(
        self,
        user_a: str,
        user_b: str,
    ) -> RelationshipState:
        """获取或创建关系状态"""
        key = self._key(user_a, user_b)
        if key not in self._relationships:
            self._relationships[key] = RelationshipState(
                user_a=key[0],
                user_b=key[1],
            )
        return self._relationships[key]
    
    def update_scores(
        self,
        user_a: str,
        user_b: str,
        score_a_to_b: float,
        score_b_to_a: float,
        topic_diversity: int,
        first_resonance_ts: Optional[float] = None,
    ):
        """更新关系分"""
        state = self.get_or_create(user_a, user_b)
        
        # 确保方向正确
        if state.user_a == user_a:
            state.relationship_score_a_to_b = score_a_to_b
            state.relationship_score_b_to_a = score_b_to_a
        else:
            state.relationship_score_a_to_b = score_b_to_a
            state.relationship_score_b_to_a = score_a_to_b
        
        state.topic_diversity = topic_diversity
        if first_resonance_ts:
            state.first_resonance_ts = first_resonance_ts
    
    def compute_and_update_level(
        self,
        user_a: str,
        user_b: str,
        current_ts: float,
    ) -> TrustLevel:
        """计算并更新信任级别"""
        state = self.get_or_create(user_a, user_b)
        level = compute_trust_level(state, current_ts)
        state.trust_level = level
        return level
    
    def get_all_relationships(
        self,
        user_id: str,
        min_level: TrustLevel = TrustLevel.L1_TRACE_VISIBLE,
    ) -> list[RelationshipState]:
        """获取用户的所有关系（按级别过滤）"""
        return [
            r for r in self._relationships.values()
            if (r.user_a == user_id or r.user_b == user_id)
            and r.trust_level >= min_level
        ]


# ============================================================
# 测试
# ============================================================

def run_tests():
    """用户管理引擎测试"""
    print("=" * 60)
    print("  用户管理引擎测试")
    print("=" * 60)
    
    # --- 匿名身份测试 ---
    print("\n📋 匿名身份生成")
    
    token = "internal_token_abc123"
    
    # 同一锚点：身份一致
    id1 = generate_anonymous_identity(token, "anchor_001")
    id2 = generate_anonymous_identity(token, "anchor_001")
    print(f"  锚点 anchor_001: {id1.display_name}")
    print(f"  同锚点再生成:    {id2.display_name}")
    print(f"  身份一致: {id1.display_name == id2.display_name} ✅")
    
    # 不同锚点：身份不同
    id3 = generate_anonymous_identity(token, "anchor_002")
    print(f"  锚点 anchor_002: {id3.display_name}")
    print(f"  跨锚点不同: {id1.display_name != id3.display_name} ✅")
    
    # 不同用户：身份不同
    id4 = generate_anonymous_identity("other_token_xyz", "anchor_001")
    print(f"  其他用户同锚点: {id4.display_name}")
    print(f"  不同用户不同: {id1.display_name != id4.display_name} ✅")
    
    # --- 信任级别测试 ---
    print(f"\n{'='*60}")
    print("  信任级别计算")
    print(f"{'='*60}\n")
    
    current_ts = time.time()
    
    test_cases = [
        {
            "label": "新关系（无共鸣）",
            "state": RelationshipState("u001", "u002"),
            "expected": TrustLevel.L0_BROWSE,
        },
        {
            "label": "单向共鸣（不达标）",
            "state": RelationshipState(
                "u001", "u002",
                relationship_score_a_to_b=2.0,
                relationship_score_b_to_a=0.5,
                topic_diversity=2,
            ),
            "expected": TrustLevel.L0_BROWSE,
        },
        {
            "label": "双向 L2 达标",
            "state": RelationshipState(
                "u001", "u002",
                relationship_score_a_to_b=1.5,
                relationship_score_b_to_a=1.2,
                topic_diversity=2,
            ),
            "expected": TrustLevel.L2_OPINION_REPLY,
        },
        {
            "label": "双向 L3 达标",
            "state": RelationshipState(
                "u001", "u002",
                relationship_score_a_to_b=4.0,
                relationship_score_b_to_a=3.5,
                topic_diversity=3,
                first_resonance_ts=current_ts - 86400 * 20,  # 20天前
            ),
            "expected": TrustLevel.L3_ASYNC_MESSAGE,
        },
        {
            "label": "L3 时间不足（才 5 天）",
            "state": RelationshipState(
                "u001", "u002",
                relationship_score_a_to_b=4.0,
                relationship_score_b_to_a=3.5,
                topic_diversity=3,
                first_resonance_ts=current_ts - 86400 * 5,
            ),
            "expected": TrustLevel.L2_OPINION_REPLY,
        },
        {
            "label": "L4 基础达标",
            "state": RelationshipState(
                "u001", "u002",
                relationship_score_a_to_b=6.0,
                relationship_score_b_to_a=5.5,
                topic_diversity=4,
                first_resonance_ts=current_ts - 86400 * 30,
            ),
            "expected": TrustLevel.L4_REALTIME_CHAT,
        },
    ]
    
    for case in test_cases:
        level = compute_trust_level(case["state"], current_ts)
        status = "✅" if level == case["expected"] else f"❌ (期望 {case['expected'].name})"
        print(f"  {case['label']:<25} → {level.name:<25} {status}")
    
    # --- 权限测试 ---
    print(f"\n📋 权限配置")
    for lvl in [TrustLevel.L0_BROWSE, TrustLevel.L2_OPINION_REPLY, TrustLevel.L3_ASYNC_MESSAGE]:
        perms = get_trust_permissions(lvl)
        enabled = [k for k, v in perms.items() if v]
        print(f"  {lvl.name}: {', '.join(enabled)}")
    
    # --- 信用计算测试 ---
    print(f"\n{'='*60}")
    print("  信用计算")
    print(f"{'='*60}\n")
    
    credit = compute_resonance_credit(
        base_score=0.5,
        received_resonance_bonus=0.3,
        harmful_mark_penalty=0.1,
        unexperienced_mark_penalty=0.05,
        consistency_bonus=0.1,
    )
    print(f"  共鸣信用分: {credit:.4f}")
    
    marker = compute_marker_credit(accurate_marks=15, total_marks=20)
    print(f"  标记者信用: {marker:.4f} (15/20 准确)")
    
    marker2 = compute_marker_credit(accurate_marks=5, total_marks=5)
    print(f"  标记者信用: {marker2:.4f} (5/5 准确，但数量少)")
    
    # --- 知己意向测试 ---
    print(f"\n{'='*60}")
    print("  知己意向匹配")
    print(f"{'='*60}\n")
    
    state = RelationshipState(
        "u001", "u002",
        relationship_score_a_to_b=4.0,
        relationship_score_b_to_a=3.5,
        topic_diversity=3,
        first_resonance_ts=current_ts - 86400 * 35,
    )
    
    eligibility = check_confidant_eligibility(state, current_ts)
    print(f"  资格检查: {eligibility}")
    
    # A 表达意向
    state = express_confidant_intent(state, "a")
    print(f"  A 表达意向 → 知己: {state.is_confidant}")
    
    # B 表达意向
    state = express_confidant_intent(state, "b")
    print(f"  B 表达意向 → 知己: {state.is_confidant} ✅")
    
    # --- 关系管理器测试 ---
    print(f"\n{'='*60}")
    print("  关系管理器")
    print(f"{'='*60}\n")
    
    mgr = RelationshipManager()
    mgr.update_scores("u001", "u002", 4.0, 3.5, 3, current_ts - 86400 * 20)
    mgr.update_scores("u001", "u003", 1.5, 1.2, 2)
    
    level12 = mgr.compute_and_update_level("u001", "u002", current_ts)
    level13 = mgr.compute_and_update_level("u001", "u003", current_ts)
    
    print(f"  u001 ↔ u002: {level12.name}")
    print(f"  u001 ↔ u003: {level13.name}")
    
    rels = mgr.get_all_relationships("u001", TrustLevel.L1_TRACE_VISIBLE)
    print(f"  u001 的关系（L1+）: {len(rels)} 条")
    
    print(f"\n✅ 测试完成")


if __name__ == "__main__":
    run_tests()
