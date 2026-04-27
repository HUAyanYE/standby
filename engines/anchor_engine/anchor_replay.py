"""
锚点重现引擎 - 锚点数据查询与筛选

实现文档 §9.1 锚点重现机制：
- 季节性回归、周年回归、经典内容循环
- 群体记忆数据聚合（MongoDB 聚合查询）
- 衰减筛选与查询历史管理
"""

import math
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


# ============================================================
# 数据结构
# ============================================================

class ReplayTrigger(Enum):
    """重现触发类型"""
    SEASONAL = "seasonal"           # 季节性回归
    ANNIVERSARY = "anniversary"     # 周年回归
    SOCIAL_EVENT = "social_event"   # 社会事件关联
    CLASSIC_CYCLE = "classic_cycle" # 经典内容循环
    GROUP_MEMORY = "group_memory"   # 群体记忆信号触发


@dataclass
class HistoricalReaction:
    """历史反应记录（匿名聚合）"""
    reaction_type: str              # "共鸣" | "反对"
    opinion_text: str               # 观点文字（已匿名化）
    timestamp: float                # 时间戳
    resonance_count: int = 0        # 该观点获得的共鸣数（用于筛选代表性观点）


@dataclass
class GroupMemoryData:
    """群体记忆数据（MongoDB 聚合查询结果）"""
    anchor_id: str
    total_reactions: int            # 历史反应总数
    resonance_count: int            # 共鸣次数
    opposition_count: int           # 反对次数
    representative_opinions: list[dict]  # 代表性观点（按共鸣数筛选）
    time_trend: Optional[dict] = None    # 时间维度变化趋势
    user_own_history: Optional[dict] = None  # 当前用户的历史反应（如有）


@dataclass
class ReplayCandidate:
    """重现候选锚点"""
    anchor_id: str
    anchor_text: str
    topics: list[str]
    trigger_type: ReplayTrigger
    trigger_score: float            # 触发优先级分数
    last_shown_ts: float = 0.0      # 上次展示时间
    show_count: int = 0             # 历史展示次数
    group_memory: Optional[GroupMemoryData] = None


@dataclass
class QueryHistoryEntry:
    """查询历史记录"""
    anchor_id: str
    timestamp: float
    user_id: str


# ============================================================
# 季节性计算
# ============================================================

# 季节 → 锚点主题关键词映射
SEASON_KEYWORDS = {
    "spring": ["春天", "花开", "新生", "希望", "开学", "三月", "四月", "植树"],
    "summer": ["夏天", "毕业", "旅行", "海边", "蝉鸣", "空调", "西瓜"],
    "autumn": ["秋天", "落叶", "收获", "中秋", "十一", "枫叶", "金黄"],
    "winter": ["冬天", "雪", "新年", "春节", "寒冷", "年末", "围巾", "火锅"],
}


def get_current_season(month: int) -> str:
    """根据月份判断季节（北半球）"""
    if month in (3, 4, 5):
        return "spring"
    elif month in (6, 7, 8):
        return "summer"
    elif month in (9, 10, 11):
        return "autumn"
    else:
        return "winter"


def seasonal_relevance(anchor_topics: list[str], current_season: str) -> float:
    """计算锚点与当前季节的相关性 [0, 1]"""
    keywords = SEASON_KEYWORDS.get(current_season, [])
    if not keywords:
        return 0.0
    
    match_count = sum(1 for t in anchor_topics if any(k in t for k in keywords))
    return min(1.0, match_count / 2)  # 匹配 2 个关键词即满分


# ============================================================
# 时间衰减与展示间隔
# ============================================================

def time_decay(days_since_last_show: float, half_life_days: float = 30.0) -> float:
    """时间衰减：距上次展示越久，优先级越高
    
    用半衰期控制——上次展示后 30 天衰减到 0.5
    """
    if days_since_last_show <= 0:
        return 0.0  # 刚展示过，不重现
    return 1.0 - math.pow(0.5, days_since_last_show / half_life_days)


def show_frequency_penalty(show_count: int) -> float:
    """展示频率惩罚：展示越多，优先级越低"""
    return 1.0 / (1 + 0.3 * show_count)


# ============================================================
# 触发优先级计算
# ============================================================

def compute_trigger_score(
    candidate: ReplayCandidate,
    current_ts: float,
) -> float:
    """计算重现候选的触发优先级
    
    trigger_score = f(触发类型, 时间衰减, 展示频率, 季节相关性)
    """
    days_since = (current_ts - candidate.last_shown_ts) / 86400
    
    # 时间衰减
    decay = time_decay(days_since)
    
    # 展示频率惩罚
    freq_penalty = show_frequency_penalty(candidate.show_count)
    
    # 触发类型权重
    trigger_weights = {
        ReplayTrigger.SEASONAL: 1.5,      # 季节性优先
        ReplayTrigger.ANNIVERSARY: 1.3,   # 周年次之
        ReplayTrigger.SOCIAL_EVENT: 1.4,  # 社会事件
        ReplayTrigger.CLASSIC_CYCLE: 1.0, # 经典循环
        ReplayTrigger.GROUP_MEMORY: 1.2,  # 群体记忆
    }
    trigger_weight = trigger_weights.get(candidate.trigger_type, 1.0)
    
    # 季节加成（季节性触发时）
    season_bonus = 1.0
    if candidate.trigger_type == ReplayTrigger.SEASONAL:
        current_month = time.localtime(current_ts).tm_mon
        season = get_current_season(current_month)
        season_bonus = 1.0 + seasonal_relevance(candidate.topics, season)
    
    return decay * freq_penalty * trigger_weight * season_bonus


# ============================================================
# 群体记忆数据聚合（MongoDB 查询接口）
# ============================================================

class GroupMemoryQueryInterface:
    """群体记忆数据查询接口
    
    生产环境对接 MongoDB，开发/测试环境用内存模拟
    """
    
    def __init__(self):
        # 内存模拟（开发用）
        self._reaction_store: dict[str, list[dict]] = {}
    
    def add_reaction(self, anchor_id: str, reaction: dict):
        """添加反应记录（模拟用）"""
        if anchor_id not in self._reaction_store:
            self._reaction_store[anchor_id] = []
        self._reaction_store[anchor_id].append(reaction)
    
    def query_group_memory(
        self,
        anchor_id: str,
        user_id: Optional[str] = None,
        min_resonance_count: int = 3,
        top_k_opinions: int = 3,
    ) -> GroupMemoryData:
        """查询锚点的群体记忆数据
        
        MongoDB 聚合查询等价逻辑：
        1. db.reactions.aggregate([{ $match: { anchor_id } },
                                   { $group: { _id: "$reaction_type", count: { $sum: 1 } } }])
        2. db.reactions.find({ anchor_id, reaction_type: "共鸣" })
                        .sort({ "opinion_resonance_count": -1 }).limit(top_k)
        3. db.reactions.find({ anchor_id, user_id })  // 用户自己的历史
        """
        reactions = self._reaction_store.get(anchor_id, [])
        
        # 统计反应分布
        resonance_count = sum(1 for r in reactions if r.get("reaction_type") == "共鸣")
        opposition_count = sum(1 for r in reactions if r.get("reaction_type") == "反对")
        
        # 筛选代表性观点（有文字 + 按共鸣数排序）
        opinions_with_text = [
            r for r in reactions
            if r.get("reaction_type") == "共鸣" and r.get("opinion_text")
        ]
        # 按获得的共鸣数排序
        opinions_with_text.sort(key=lambda x: x.get("resonance_count", 0), reverse=True)
        
        representative = [
            {
                "opinion_text": r["opinion_text"][:100],  # 截断展示
                "resonance_count": r.get("resonance_count", 0),
                "timestamp": r.get("timestamp", 0),
            }
            for r in opinions_with_text[:top_k_opinions]
        ]
        
        # 用户自己的历史
        user_own = None
        if user_id:
            own_reactions = [r for r in reactions if r.get("user_id") == user_id]
            if own_reactions:
                user_own = {
                    "count": len(own_reactions),
                    "last_reaction_type": own_reactions[-1].get("reaction_type"),
                    "has_opinion": any(r.get("opinion_text") for r in own_reactions),
                }
        
        return GroupMemoryData(
            anchor_id=anchor_id,
            total_reactions=len(reactions),
            resonance_count=resonance_count,
            opposition_count=opposition_count,
            representative_opinions=representative,
            user_own_history=user_own,
        )


# ============================================================
# 查询历史管理
# ============================================================

class QueryHistory:
    """锚点查询历史管理
    
    防止短期内重复展示同一锚点
    """
    
    def __init__(self, min_interval_hours: float = 72.0):
        self._history: list[QueryHistoryEntry] = []
        self.min_interval = min_interval_hours * 3600  # 转秒
    
    def add(self, anchor_id: str, user_id: str, timestamp: float):
        """记录一次锚点展示"""
        self._history.append(QueryHistoryEntry(
            anchor_id=anchor_id,
            timestamp=timestamp,
            user_id=user_id,
        ))
    
    def was_recently_shown(
        self,
        anchor_id: str,
        user_id: str,
        current_ts: float,
    ) -> bool:
        """检查该锚点是否最近展示过"""
        for entry in reversed(self._history):
            if entry.anchor_id == anchor_id and entry.user_id == user_id:
                return (current_ts - entry.timestamp) < self.min_interval
        return False
    
    def get_last_show_time(
        self,
        anchor_id: str,
        user_id: str,
    ) -> float:
        """获取上次展示时间"""
        for entry in reversed(self._history):
            if entry.anchor_id == anchor_id and entry.user_id == user_id:
                return entry.timestamp
        return 0.0
    
    def get_show_count(
        self,
        anchor_id: str,
        user_id: str,
    ) -> int:
        """获取展示次数"""
        return sum(
            1 for e in self._history
            if e.anchor_id == anchor_id and e.user_id == user_id
        )


# ============================================================
# 锚点重现引擎
# ============================================================

class AnchorReplayEngine:
    """锚点重现引擎主类
    
    职责：
    1. 从候选池中筛选可重现的锚点
    2. 按触发优先级排序
    3. 附带群体记忆数据
    4. 管理查询历史，避免重复展示
    """
    
    def __init__(
        self,
        memory_query: Optional[GroupMemoryQueryInterface] = None,
        min_interval_hours: float = 72.0,
    ):
        self.memory_query = memory_query or GroupMemoryQueryInterface()
        self.query_history = QueryHistory(min_interval_hours)
    
    def select_replay_anchors(
        self,
        candidates: list[ReplayCandidate],
        user_id: str,
        current_ts: float,
        top_k: int = 5,
    ) -> list[ReplayCandidate]:
        """筛选并排序重现锚点
        
        步骤：
        1. 过滤最近展示过的锚点
        2. 计算触发优先级
        3. 按优先级排序
        4. 返回 top_k
        5. 记录查询历史
        """
        scored = []
        
        for candidate in candidates:
            # 跳过最近展示过的
            if self.query_history.was_recently_shown(
                candidate.anchor_id, user_id, current_ts
            ):
                continue
            
            # 填充历史展示信息
            candidate.last_shown_ts = self.query_history.get_last_show_time(
                candidate.anchor_id, user_id
            )
            candidate.show_count = self.query_history.get_show_count(
                candidate.anchor_id, user_id
            )
            
            # 计算触发优先级
            candidate.trigger_score = compute_trigger_score(candidate, current_ts)
            
            # 查询群体记忆数据
            candidate.group_memory = self.memory_query.query_group_memory(
                candidate.anchor_id, user_id
            )
            
            scored.append(candidate)
        
        # 按触发优先级降序
        scored.sort(key=lambda c: c.trigger_score, reverse=True)
        
        # 记录查询历史
        for candidate in scored[:top_k]:
            self.query_history.add(candidate.anchor_id, user_id, current_ts)
        
        return scored[:top_k]
    
    def format_group_memory_display(
        self,
        group_memory: GroupMemoryData,
        anchor_text: str,
    ) -> str:
        """格式化群体记忆展示
        
        返回终端友好的文本格式（对应 PRD 中的 UI 原型）
        """
        lines = []
        lines.append(f"┌{'─'*55}┐")
        lines.append(f"│  {anchor_text[:50]}{'...' if len(anchor_text)>50 else ''}")
        lines.append(f"├{'─'*55}┤")
        lines.append(f"│  🕰 群体记忆")
        lines.append(f"│")
        
        if group_memory.resonance_count > 0:
            lines.append(f"│  过去，{group_memory.resonance_count} 人对这个锚点产生了共鸣")
        else:
            lines.append(f"│  这是一个全新的锚点")
        
        if group_memory.representative_opinions:
            lines.append(f"│  代表性观点：")
            for i, op in enumerate(group_memory.representative_opinions):
                text = op["opinion_text"][:40]
                count = op["resonance_count"]
                lines.append(f'│    "{text}..." ——获得 {count} 次共鸣')
        
        lines.append(f"│")
        
        if group_memory.user_own_history:
            own = group_memory.user_own_history
            if own["has_opinion"]:
                lines.append(f"│  你之前也在这里留下过观点")
            else:
                lines.append(f"│  你之前也在这里有过共鸣")
        
        lines.append(f"│")
        lines.append(f"│  [写写你现在的感受]")
        lines.append(f"└{'─'*55}┘")
        
        return "\n".join(lines)


# ============================================================
# 测试
# ============================================================

def run_tests():
    """锚点重现引擎测试"""
    print("=" * 60)
    print("  锚点重现引擎测试")
    print("=" * 60)
    
    # --- 季节性计算测试 ---
    print("\n📋 季节性计算")
    for month in [1, 4, 7, 10]:
        season = get_current_season(month)
        print(f"  月份 {month} → 季节: {season}")
    
    autumn_topics = ["秋天", "落叶", "城市"]
    print(f"  秋天主题 {autumn_topics} 与秋季相关性: {seasonal_relevance(autumn_topics, 'autumn'):.2f}")
    spring_topics = ["春天", "花朵"]
    print(f"  春天主题 {spring_topics} 与秋季相关性: {seasonal_relevance(spring_topics, 'autumn'):.2f}")
    
    # --- 时间衰减测试 ---
    print("\n📋 时间衰减")
    for days in [0, 7, 14, 30, 60, 90]:
        decay = time_decay(days)
        print(f"  {days:>3} 天后衰减: {decay:.4f}")
    
    # --- 展示频率惩罚测试 ---
    print("\n📋 展示频率惩罚")
    for count in [0, 1, 3, 5, 10]:
        penalty = show_frequency_penalty(count)
        print(f"  展示 {count:>2} 次: 惩罚 = {penalty:.4f}")
    
    # --- 完整流程测试 ---
    print(f"\n{'='*60}")
    print("  完整重现流程测试")
    print(f"{'='*60}\n")
    
    # 初始化
    memory_query = GroupMemoryQueryInterface()
    engine = AnchorReplayEngine(memory_query=memory_query, min_interval_hours=1)
    
    # 模拟历史反应数据
    memory_query.add_reaction("a001", {
        "user_id": "u100", "reaction_type": "共鸣",
        "opinion_text": "深夜的地铁像一个移动的棺材，载着疲惫的灵魂回家。",
        "resonance_count": 12, "timestamp": time.time() - 86400 * 30,
    })
    memory_query.add_reaction("a001", {
        "user_id": "u101", "reaction_type": "共鸣",
        "opinion_text": "地铁上的孤独，是一种被包围的孤独。",
        "resonance_count": 8, "timestamp": time.time() - 86400 * 25,
    })
    memory_query.add_reaction("a001", {
        "user_id": "u102", "reaction_type": "反对",
        "opinion_text": "这不算孤独，这只是通勤。",
        "resonance_count": 2, "timestamp": time.time() - 86400 * 20,
    })
    
    memory_query.add_reaction("a002", {
        "user_id": "u100", "reaction_type": "共鸣",
        "opinion_text": "秋风扫落叶，像时间扫过青春。",
        "resonance_count": 15, "timestamp": time.time() - 86400 * 365,  # 一年前
    })
    
    # 构建候选
    candidates = [
        ReplayCandidate(
            anchor_id="a001",
            anchor_text="深夜独自坐在末班地铁上，窗外灯火通明，但没有一盏灯是为我亮的。",
            topics=["孤独", "城市", "地铁"],
            trigger_type=ReplayTrigger.CLASSIC_CYCLE,
            trigger_score=0,
        ),
        ReplayCandidate(
            anchor_id="a002",
            anchor_text="秋天来了，第一片叶子落下的时候，我突然想起了去年的自己。",
            topics=["秋天", "落叶", "回忆", "时间"],
            trigger_type=ReplayTrigger.SEASONAL,
            trigger_score=0,
        ),
        ReplayCandidate(
            anchor_id="a003",
            anchor_text="今天和十年前的自己重逢了。",
            topics=["时间", "成长"],
            trigger_type=ReplayTrigger.ANNIVERSARY,
            trigger_score=0,
        ),
    ]
    
    # 当前时间（秋季）
    current_ts = time.mktime(time.strptime("2026-10-15", "%Y-%m-%d"))
    
    # 筛选
    results = engine.select_replay_anchors(candidates, "u_target", current_ts, top_k=3)
    
    print(f"筛选结果（按触发优先级排序）：\n")
    for i, r in enumerate(results):
        gm = r.group_memory
        print(f"  #{i+1} [{r.trigger_type.value}] {r.anchor_text[:40]}...")
        print(f"      触发优先级: {r.trigger_score:.4f}")
        print(f"      历史反应: {gm.total_reactions} (共鸣 {gm.resonance_count}, 反对 {gm.opposition_count})")
        print()
    
    # 展示群体记忆格式
    if results:
        best = results[0]
        print("群体记忆展示格式：\n")
        print(engine.format_group_memory_display(best.group_memory, best.anchor_text))
    
    # 查询历史测试
    print(f"\n📋 查询历史")
    print(f"  锚点 a001 最近展示过: {engine.query_history.was_recently_shown('a001', 'u_target', current_ts)}")
    print(f"  锚点 a001 展示次数: {engine.query_history.get_show_count('a001', 'u_target')}")
    
    # 再次查询（应被过滤）
    results2 = engine.select_replay_anchors(candidates, "u_target", current_ts + 60, top_k=3)
    print(f"  立即再查询返回数量: {len(results2)} (应为 {len(results) - 1}，a001 被过滤)")
    
    print(f"\n✅ 测试完成")


if __name__ == "__main__":
    run_tests()
