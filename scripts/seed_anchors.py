#!/usr/bin/env python3
"""
种子数据脚本 — 注册锚点 + 提交反应

用法:
  cd /mnt/d/Hermes/standby
  python3 scripts/seed_anchors.py
"""

import sys
import time
from pathlib import Path

# 路径设置
ROOT = Path(__file__).parent.parent
PROTO_DIR = ROOT / "src" / "proto" / "generated" / "python"
ENGINES_DIR = ROOT / "engines"

sys.path.insert(0, str(PROTO_DIR))
sys.path.insert(0, str(ENGINES_DIR))

import grpc
from engines import engines_pb2, engines_pb2_grpc
from common import common_pb2

ANCHOR_ENGINE_ADDR = "localhost:8090"
RESONANCE_ENGINE_ADDR = "localhost:8091"

# ── 种子锚点数据 ──────────────────────────────────────────────
SEED_ANCHORS = [
    {
        "text": "记得有一次在老家的院子里，奶奶教我包饺子。她的手很粗糙，但包出来的饺子褶子特别整齐。我总是包不好，馅料从缝隙里漏出来。奶奶笑着说：'慢慢来，急不得。'那天的阳光透过葡萄架洒下来，院子里飘着面粉的香味。现在想起来，那不只是在学包饺子，是在学一种耐心。",
        "topics": ["童年", "家人", "食物", "耐心"],
        "source_type": "memory",
    },
    {
        "text": "大学毕业那天，我们几个室友在宿舍楼顶喝了一夜的酒。有人哭了，有人笑了，有人说以后一定要再见。其实大家心里都知道，有些人可能这辈子都不会再见了。那种感觉很奇怪，明明还在一起，却已经开始怀念。第二天退宿的时候，我回头看了一眼空荡荡的房间，突然觉得四年好短。",
        "topics": ["毕业", "离别", "友情", "时间"],
        "source_type": "memory",
    },
    {
        "text": "有一次加班到凌晨两点，走在回家的路上，整个城市都安静了。路灯把影子拉得很长，便利店的灯光显得特别温暖。我突然在想，这样的生活到底是为了什么？不是抱怨，是真的在思考。也许答案不在终点，而在每一个这样的深夜里，我还在坚持走回家的路上。",
        "topics": ["深夜", "思考", "城市", "坚持"],
        "source_type": "reflection",
    },
    {
        "text": "去年冬天回老家，发现小时候经常去的那条小河已经干涸了。河床上长满了杂草，曾经捉鱼摸虾的地方变成了一片荒地。旁边修了一条水泥路，方便是方便了，但总觉得少了什么。也许每一代人都有自己记忆中的那条河，它不只是一条河，是回不去的时光。",
        "topics": ["故乡", "变迁", "记忆", "时间"],
        "source_type": "observation",
    },
    {
        "text": "今天在地铁上看到一个老爷爷在教小孙女认字。小女孩指着广告牌上的字一个一个念，念错了老爷爷就耐心纠正。周围的人都戴着耳机看手机，只有他们两个沉浸在自己的世界里。那一刻我觉得，真正的教育可能不是在学校里，而是在这些日常的瞬间。",
        "topics": ["教育", "日常", "亲情", "观察"],
        "source_type": "observation",
    },
]


def register_anchor(stub, anchor_data: dict) -> str:
    """通过 gRPC 注册锚点"""
    request = engines_pb2.GenerateAnchorRequest(
        source_texts=[anchor_data["text"]],
        topic_hints=anchor_data["topics"],
        source_type=anchor_data.get("source_type", "user_content"),
    )
    response = stub.GenerateAnchor(request)
    if response.success:
        return response.anchor.anchor_id
    else:
        print(f"  ⚠️ 注册失败: {response.rejection_reason}")
        return None


EMOTION_WORD_MAP = {
    "同感": common_pb2.EMPATHY,
    "触发": common_pb2.TRIGGER,
    "启发": common_pb2.INSIGHT,
    "震撼": common_pb2.SHOCK,
    "": common_pb2.EMOTION_WORD_UNSPECIFIED,
}


def submit_reaction(stub, user_id: str, anchor_id: str,
                    reaction_type: str, emotion_word: str,
                    trace_text: str) -> bool:
    """通过 gRPC 提交反应"""
    request = engines_pb2.ProcessReactionRequest(
        user_id=user_id,
        anchor_id=anchor_id,
        reaction_type=getattr(common_pb2, reaction_type, 0),
        emotion_word=EMOTION_WORD_MAP.get(emotion_word, common_pb2.EMOTION_WORD_UNSPECIFIED),
        opinion_text=trace_text,
    )
    response = stub.ProcessReaction(request)
    return response.success


def main():
    print("=" * 60)
    print("🌱 Standby 种子数据注入")
    print("=" * 60)

    # 连接引擎
    channel_anchor = grpc.insecure_channel(ANCHOR_ENGINE_ADDR)
    channel_resonance = grpc.insecure_channel(RESONANCE_ENGINE_ADDR)
    anchor_stub = engines_pb2_grpc.AnchorEngineStub(channel_anchor)
    resonance_stub = engines_pb2_grpc.ResonanceEngineStub(channel_resonance)

    # ── Step 1: 注册锚点 ──────────────────────────────────────
    print("\n📌 注册种子锚点...")
    anchor_ids = []
    for i, anchor_data in enumerate(SEED_ANCHORS, 1):
        print(f"\n  [{i}/{len(SEED_ANCHORS)}] {anchor_data['text'][:40]}...")
        anchor_id = register_anchor(anchor_stub, anchor_data)
        if anchor_id:
            anchor_ids.append(anchor_id)
            print(f"  ✅ {anchor_id} (质量评估通过)")
        else:
            print(f"  ❌ 注册失败")
        time.sleep(0.5)  # 避免过快

    print(f"\n  成功注册: {len(anchor_ids)}/{len(SEED_ANCHORS)}")

    # ── Step 2: 提交反应 ──────────────────────────────────────
    print("\n💬 提交种子反应...")
    reactions = [
        # 用户1 的反应
        {"user_id": "user_alpha_001", "anchor_idx": 0,
         "reaction_type": "RESONANCE", "emotion_word": "同感",
         "trace_text": "我奶奶也是这样教我的，她的手法我到现在还记得。"},
        {"user_id": "user_alpha_001", "anchor_idx": 1,
         "reaction_type": "RESONANCE", "emotion_word": "触发",
         "trace_text": "毕业那天我也哭了，真的有些人再也没见过。"},
        {"user_id": "user_alpha_001", "anchor_idx": 2,
         "reaction_type": "RESONANCE", "emotion_word": "启发",
         "trace_text": "原来不只是我一个人在深夜思考这些。"},

        # 用户2 的反应
        {"user_id": "user_alpha_002", "anchor_idx": 0,
         "reaction_type": "RESONANCE", "emotion_word": "震撼",
         "trace_text": "这条河我也见过，变化太大了。"},
        {"user_id": "user_alpha_002", "anchor_idx": 3,
         "reaction_type": "RESONANCE", "emotion_word": "同感",
         "trace_text": "小时候的河边夏天是最美好的记忆。"},
        {"user_id": "user_alpha_002", "anchor_idx": 4,
         "reaction_type": "RESONANCE", "emotion_word": "触发",
         "trace_text": "地铁上的那一幕让我想起了自己的爷爷。"},

        # 用户3 的反应 (少量)
        {"user_id": "user_alpha_003", "anchor_idx": 0,
         "reaction_type": "NEUTRAL", "emotion_word": "",
         "trace_text": "挺好的故事。"},
        {"user_id": "user_alpha_003", "anchor_idx": 2,
         "reaction_type": "RESONANCE", "emotion_word": "启发",
         "trace_text": "深夜思考确实是一种奢侈。"},
    ]

    success_count = 0
    for i, r in enumerate(reactions, 1):
        anchor_id = anchor_ids[r["anchor_idx"]] if r["anchor_idx"] < len(anchor_ids) else None
        if not anchor_id:
            print(f"  [{i}] ⚠️ 锚点索引 {r['anchor_idx']} 不存在，跳过")
            continue

        print(f"  [{i}/{len(reactions)}] {r['user_id']} → {r['emotion_word'] or r['reaction_type']}...")
        ok = submit_reaction(
            resonance_stub,
            r["user_id"], anchor_id,
            r["reaction_type"], r["emotion_word"],
            r["trace_text"],
        )
        if ok:
            success_count += 1
            print(f"  ✅")
        else:
            print(f"  ❌ 提交失败")
        time.sleep(0.3)

    print(f"\n  成功提交: {success_count}/{len(reactions)}")

    # ── 总结 ──────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print(f"🎉 种子数据注入完成!")
    print(f"   锚点: {len(anchor_ids)} 个")
    print(f"   反应: {success_count} 条")
    print(f"\n   测试用户: user_alpha_001, user_alpha_002, user_alpha_003")
    print(f"   锚点 ID: {', '.join(anchor_ids[:3])}...")
    print("=" * 60)


if __name__ == "__main__":
    main()
