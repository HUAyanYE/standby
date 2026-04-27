"""
阶段 0 技术预研：BERTopic 中文观点聚类效果验证

验证目标：
1. BERTopic 对中文短文本（用户观点）的聚类效果
2. HDBSCAN 的参数敏感性
3. c-TF-IDF 主题词提取的质量
4. 不同 embedding 模型的对比

输入：模拟的用户观点数据集（中文）
输出：聚类效果评估报告
"""

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

# ============================================================
# 模拟数据集：中文用户观点
# ============================================================

SIMULATED_OPINIONS = [
    # 簇 1：孤独
    {"id": "op_001", "text": "深夜加班后独自坐在末班地铁上，窗外的城市灯火通明，但没有一盏灯是为我亮的。那种孤独感不是身边没有人，而是没有人知道你在这里。", "topic": "孤独"},
    {"id": "op_002", "text": "一个人去吃火锅，服务员问几位，说一位的时候对面放了一只小熊。那一刻突然觉得自己好像很可怜，但又好像没什么大不了。", "topic": "孤独"},
    {"id": "op_003", "text": "在大城市生活了五年，每天和几百万人擦肩而过，但能叫出名字的人不超过十个。不是社交能力差，是真的没有机会和一个人建立真正的联系。", "topic": "孤独"},
    {"id": "op_004", "text": "朋友圈里几百个人，发了一条深夜感慨，过了两个小时只有三个人点赞，没有一条评论。不是想要关注，只是觉得好像没人真的在乎。", "topic": "孤独"},
    {"id": "op_005", "text": "我妈打来电话问我最近怎么样，我说挺好的。挂了电话才意识到，我已经很久没有对任何人说过真实的状态了。", "topic": "孤独"},
    {"id": "op_006", "text": "最孤独的时刻不是一个人，而是在人群中突然意识到，我和周围的每一个人都不在同一个频率上。", "topic": "孤独"},
    {"id": "op_007", "text": "搬来新城市三个月了，周末最大的活动就是去超市买菜。不是不想社交，是不知道怎么开始。", "topic": "孤独"},

    # 簇 2：音乐与记忆
    {"id": "op_008", "text": "在车里随机播放到了一首高中时代的老歌，副歌响起的瞬间，想起了那个夏天的操场和那个再也没联系过的人。音乐是时间机器。", "topic": "音乐"},
    {"id": "op_009", "text": "有些歌你不是在听，你是在重访一段记忆。每一个音符都是一扇门，推开就是那个再也回不去的场景。", "topic": "音乐"},
    {"id": "op_010", "text": "深夜一个人戴着耳机听坂本龙一的钢琴曲，窗外在下雨。那一刻时间是静止的，只有音乐和雨声。", "topic": "音乐"},
    {"id": "op_011", "text": "小时候不理解父母为什么总听那些老歌，现在自己开始反复听十年前的歌单了。原来怀旧不是一种选择，是一种必然。", "topic": "音乐"},
    {"id": "op_012", "text": "在异国他乡的街头听到有人在弹中国民谣，站在那里听了整整十分钟。不是因为弹得多好，是因为那个旋律把我带回了家。", "topic": "音乐"},
    {"id": "op_013", "text": "有些歌只适合在特定的天气、特定的心境下听。今天下雨，适合听陈绮贞。", "topic": "音乐"},

    # 簇 3：成长与迷茫
    {"id": "op_014", "text": "二十多岁最大的恐惧不是失败，是不知道自己想要什么。看着同龄人好像都有明确的方向，只有我在原地打转。", "topic": "迷茫"},
    {"id": "op_015", "text": "毕业三年换了两份工作，每一份都做了一年多就厌倦了。不是工作不好，是我好像对什么都提不起长期的热情。", "topic": "迷茫"},
    {"id": "op_016", "text": "父母希望我考公务员，朋友建议我去创业，但没人问过我自己想做什么。最可怕的是，我自己也不知道。", "topic": "迷茫"},
    {"id": "op_017", "text": "三十岁回头看，发现二十岁时的那些'确定'都是假的。真正确定的东西，反而是那些不确定中慢慢长出来的。", "topic": "迷茫"},
    {"id": "op_018", "text": "有时候觉得选择太多反而是诅咒。如果人生只有两条路，可能早就走完了。但面前有无数条路，每一条都在诱惑你，每一条你都不敢选。", "topic": "迷茫"},
    {"id": "op_019", "text": "深夜刷到同龄人的朋友圈，有人结婚了，有人升职了，有人环游世界。关掉手机，还是不知道明天该干嘛。", "topic": "迷茫"},

    # 簇 4：城市生活
    {"id": "op_020", "text": "上海的便利店密度全中国最高，凌晨三点也能买到一杯热咖啡。这大概就是大城市给你的唯一确定性——永远不会没有退路。", "topic": "城市"},
    {"id": "op_021", "text": "每天通勤一个半小时，在地铁里看书、听播客、发呆。这段不属于工作也不属于家的时间，反而是最自由的。", "topic": "城市"},
    {"id": "op_022", "text": "在北京住了三年，最有归属感的时刻不是在出租屋里，而是在楼下的那家面馆。老板已经记住我了，每次都多给一勺辣椒。", "topic": "城市"},
    {"id": "op_023", "text": "大城市的节奏让人没有时间悲伤。上午被领导骂了，下午还有三个会要开。等晚上回到家，那股情绪已经不知道去哪了。", "topic": "城市"},
    {"id": "op_024", "text": "深圳是一个你随时可以重新开始的城市。没有人知道你的过去，也没有人在意你的未来。自由和孤独是同一枚硬币的两面。", "topic": "城市"},
    {"id": "op_025", "text": "周末去了一个从来没有去过的公园，在长椅上坐了一个下午。城市再大，也需要一个安静的角落。", "topic": "城市"},

    # 簇 5：阅读与思考
    {"id": "op_026", "text": "读到加缪的那句话：'在隆冬，我终于知道，我身上有一个不可战胜的夏天。'放下书，坐在窗前想了很久。有些话不是用来理解的，是用来感受的。", "topic": "阅读"},
    {"id": "op_027", "text": "重读《百年孤独》，发现年轻时关注的是魔幻，现在关注的是孤独。同一本书在不同的人生阶段读，完全是两本不同的书。", "topic": "阅读"},
    {"id": "op_028", "text": "在书店看到一个老人坐在角落里读一本旧书，书页已经泛黄了。突然觉得，读书这件事本身，就是一种抵抗。", "topic": "阅读"},
    {"id": "op_029", "text": "最近在读一本关于日本物哀美学的书。以前觉得日本人的情感很压抑，现在理解了——有些美只有在消逝的瞬间才能被感知。", "topic": "阅读"},
    {"id": "op_030", "text": "读完了《活着》，没有哭，但胸口堵了很久。好的文学不是让你流泪，是让你说不出话。", "topic": "阅读"},
    {"id": "op_031", "text": "有人说读书没用，不能赚钱不能升职。但读书让我知道了自己不是一个人在困惑——几百年前的人也想过同样的问题。", "topic": "阅读"},

    # 簇 6：人际关系
    {"id": "op_032", "text": "成年后最难的事是维持友谊。不是不想联系，是真的不知道说什么。上次聊天是半年前，现在发消息好像太突兀了。", "topic": "关系"},
    {"id": "op_033", "text": "最好的朋友结婚了，我坐在台下哭了。不是因为感动，是因为知道从今以后，她是别人的了。", "topic": "关系"},
    {"id": "op_034", "text": "和父母的关系，从对抗到和解到理解，用了将近十年。现在每次回家，反而觉得他们越来越像小孩了。", "topic": "关系"},
    {"id": "op_035", "text": "分手后的第三个月，终于可以听到那首歌不哭了。但经过那家咖啡馆还是会绕路走。身体的记忆比大脑诚实。", "topic": "关系"},
    {"id": "op_036", "text": "同事和朋友的边界越来越模糊。每天相处八小时的人，出了公司大门就像不认识一样。", "topic": "关系"},
    {"id": "op_037", "text": "真正的亲密关系不是时刻在一起，而是即使很久不联系，再见面时也不会尴尬。", "topic": "关系"},
]


def create_output_dir():
    """创建输出目录"""
    results_dir = Path(__file__).parent / "results" / "bertopic"
    results_dir.mkdir(parents=True, exist_ok=True)
    return results_dir


def print_section(title):
    """打印分节标题"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def experiment_1_basic_clustering():
    """
    实验 1：基础聚类效果测试
    
    使用 BERTopic 的标准流程对模拟数据进行聚类，
    验证是否能正确识别预设的话题簇。
    """
    print_section("实验 1：基础聚类效果")
    
    try:
        from bertopic import BERTopic
        from sentence_transformers import SentenceTransformer
        from sklearn.feature_extraction.text import CountVectorizer
        import jieba
    except ImportError as e:
        print(f"❌ 依赖未安装: {e}")
        print("请等待 torch/transformers 安装完成后重试")
        return None
    
    texts = [op["text"] for op in SIMULATED_OPINIONS]
    true_labels = [op["topic"] for op in SIMULATED_OPINIONS]
    ids = [op["id"] for op in SIMULATED_OPINIONS]
    
    print(f"数据集: {len(texts)} 条中文观点")
    print(f"真实话题: {sorted(set(true_labels))}")
    
    # 中文分词的 CountVectorizer
    def jieba_tokenizer(text):
        return list(jieba.cut(text))
    
    vectorizer = CountVectorizer(tokenizer=jieba_tokenizer, token_pattern=None)
    
    # 测试不同 embedding 模型
    models_to_test = [
        "paraphrase-multilingual-MiniLM-L12-v2",  # 轻量多语言
        "shibing624/text2vec-base-chinese",         # 中文专用
    ]
    
    results = []
    
    for model_name in models_to_test:
        print(f"\n--- Embedding 模型: {model_name} ---")
        
        try:
            t0 = time.time()
            
            embedding_model = SentenceTransformer(model_name)
            
            topic_model = BERTopic(
                embedding_model=embedding_model,
                vectorizer_model=vectorizer,
                min_cluster_size=5,
                min_samples=3,
                nr_topics="auto",
                verbose=False,
            )
            
            topics, probs = topic_model.fit_transform(texts)
            
            elapsed = time.time() - t0
            
            # 评估：调整兰德指数 (ARI)
            from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score
            
            # 将真实标签转为数字
            label_map = {label: i for i, label in enumerate(sorted(set(true_labels)))}
            true_numeric = [label_map[l] for l in true_labels]
            
            ari = adjusted_rand_score(true_numeric, topics)
            nmi = normalized_mutual_info_score(true_numeric, topics)
            
            # 主题词
            topic_info = topic_model.get_topic_info()
            n_topics = len([t for t in topic_info["Topic"] if t != -1])
            n_outliers = sum(1 for t in topics if t == -1)
            
            result = {
                "model": model_name,
                "n_topics": n_topics,
                "n_outliers": n_outliers,
                "ari": round(ari, 4),
                "nmi": round(nmi, 4),
                "time_seconds": round(elapsed, 2),
            }
            results.append(result)
            
            print(f"  聚类数: {n_topics} (不含噪音)")
            print(f"  噪音点: {n_outliers}/{len(texts)}")
            print(f"  ARI: {ari:.4f} (1.0 = 完美匹配)")
            print(f"  NMI: {nmi:.4f}")
            print(f"  耗时: {elapsed:.2f}s")
            
            # 打印主题词
            print(f"\n  主题词:")
            for topic_id in range(min(n_topics, 10)):
                words = topic_model.get_topic(topic_id)
                if words:
                    top_words = [w for w, _ in words[:5]]
                    print(f"    Topic {topic_id}: {', '.join(top_words)}")
            
        except Exception as e:
            print(f"  ❌ 模型加载/运行失败: {e}")
            results.append({"model": model_name, "error": str(e)})
    
    return results


def experiment_2_parameter_sensitivity():
    """
    实验 2：HDBSCAN 参数敏感性测试
    
    测试不同 min_cluster_size 和 min_samples 对聚类效果的影响。
    """
    print_section("实验 2：HDBSCAN 参数敏感性")
    
    try:
        from bertopic import BERTopic
        from sentence_transformers import SentenceTransformer
        from sklearn.feature_extraction.text import CountVectorizer
        from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score
        import jieba
    except ImportError as e:
        print(f"❌ 依赖未安装: {e}")
        return None
    
    texts = [op["text"] for op in SIMULATED_OPINIONS]
    true_labels = [op["topic"] for op in SIMULATED_OPINIONS]
    label_map = {label: i for i, label in enumerate(sorted(set(true_labels)))}
    true_numeric = [label_map[l] for l in true_labels]
    
    def jieba_tokenizer(text):
        return list(jieba.cut(text))
    
    vectorizer = CountVectorizer(tokenizer=jieba_tokenizer, token_pattern=None)
    
    # 预计算 embeddings（避免重复计算）
    print("预计算 embeddings...")
    embedding_model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
    embeddings = embedding_model.encode(texts, show_progress_bar=False)
    
    # 参数网格
    param_grid = [
        {"min_cluster_size": 3, "min_samples": 2},
        {"min_cluster_size": 5, "min_samples": 3},
        {"min_cluster_size": 7, "min_samples": 3},
        {"min_cluster_size": 5, "min_samples": 5},
        {"min_cluster_size": 10, "min_samples": 5},
    ]
    
    results = []
    
    for params in param_grid:
        print(f"\n--- min_cluster_size={params['min_cluster_size']}, min_samples={params['min_samples']} ---")
        
        topic_model = BERTopic(
            embedding_model=embedding_model,
            vectorizer_model=vectorizer,
            min_cluster_size=params["min_cluster_size"],
            min_samples=params["min_samples"],
            nr_topics="auto",
            verbose=False,
        )
        
        topics, probs = topic_model.fit_transform(texts, embeddings)
        
        ari = adjusted_rand_score(true_numeric, topics)
        nmi = normalized_mutual_info_score(true_numeric, topics)
        
        topic_info = topic_model.get_topic_info()
        n_topics = len([t for t in topic_info["Topic"] if t != -1])
        n_outliers = sum(1 for t in topics if t == -1)
        
        result = {
            **params,
            "n_topics": n_topics,
            "n_outliers": n_outliers,
            "ari": round(ari, 4),
            "nmi": round(nmi, 4),
        }
        results.append(result)
        
        print(f"  聚类数: {n_topics}, 噪音: {n_outliers}, ARI: {ari:.4f}, NMI: {nmi:.4f}")
    
    # 找最优参数
    best = max(results, key=lambda x: x["ari"])
    print(f"\n✅ 最优参数: min_cluster_size={best['min_cluster_size']}, "
          f"min_samples={best['min_samples']}, ARI={best['ari']}")
    
    return results


def experiment_3_novelty_scoring():
    """
    实验 3：观点增量性 (novelty) 评分验证
    
    验证 novelty = 1 - max(与已有观点的相似度) 是否能
    有效区分"复述"和"增量感悟"。
    """
    print_section("实验 3：观点增量性评分")
    
    try:
        from sentence_transformers import SentenceTransformer
        from sklearn.metrics.pairwise import cosine_similarity
    except ImportError as e:
        print(f"❌ 依赖未安装: {e}")
        return None
    
    # 构造测试用例
    anchor = "深夜独自坐在末班地铁上，窗外灯火通明，但没有一盏灯是为我亮的。"
    
    test_cases = [
        {
            "label": "复述锚点（低 novelty）",
            "text": "是啊，深夜坐地铁确实很孤独，窗外的灯都不属于我。",
        },
        {
            "label": "相似经历（中 novelty）",
            "text": "我也曾在深夜的末班地铁上，一个人看着窗外发呆，觉得整个世界都和我没关系。",
        },
        {
            "label": "全新角度（高 novelty）",
            "text": "孤独不是身边没有人，是没有人知道你在哪里。我有一次在机场候机厅过夜，周围全是人但没有一个人认识我。",
        },
        {
            "label": "完全不相关",
            "text": "今天中午吃的麻辣烫特别好吃，下次还要去那家店。",
        },
    ]
    
    print(f"锚点: {anchor}\n")
    
    model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
    
    anchor_emb = model.encode([anchor])
    case_texts = [c["text"] for c in test_cases]
    case_embs = model.encode(case_texts)
    
    # 计算与锚点的相似度（relevance）
    relevance_scores = cosine_similarity(anchor_emb, case_embs)[0]
    
    # 计算观点间的相似度（用于 novelty）
    pairwise = cosine_similarity(case_embs)
    
    print(f"{'标签':<25} {'relevance':>10} {'预期novelty':>12}")
    print("-" * 50)
    
    results = []
    for i, case in enumerate(test_cases):
        # novelty = 与其他观点的最大相似度的补
        # 这里简化为：与锚点相关的前提下，越不相似于锚点 = novelty 越高
        relevance = relevance_scores[i]
        
        # 简化的 novelty：与锚点不相似 + 自身独特
        anchor_similarity = relevance
        novelty_proxy = max(0, 1 - anchor_similarity) if relevance > 0.3 else 0
        
        print(f"{case['label']:<25} {relevance:>10.4f} {novelty_proxy:>12.4f}")
        
        results.append({
            "label": case["label"],
            "relevance": round(float(relevance), 4),
            "novelty_proxy": round(float(novelty_proxy), 4),
            "text_preview": case["text"][:50],
        })
    
    print("\n📌 关键观察:")
    print("   relevance > 0.3 且 novelty 高 = 高价值增量感悟")
    print("   relevance > 0.3 且 novelty 低 = 复述锚点，低价值")
    print("   relevance < 0.3 = 不相关，不计入共鸣")
    
    return results


def save_results(all_results, output_dir):
    """保存实验结果"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"bertopic_validation_{timestamp}.json"
    
    report = {
        "timestamp": timestamp,
        "dataset_size": len(SIMULATED_OPINIONS),
        "true_topics": sorted(set(op["topic"] for op in SIMULATED_OPINIONS)),
        "experiments": all_results,
    }
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n📊 结果已保存: {output_file}")
    return output_file


def main():
    print_section("Standby AI Engines - 技术预研")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"数据集: {len(SIMULATED_OPINIONS)} 条模拟中文观点")
    print(f"真实话题数: {len(set(op['topic'] for op in SIMULATED_OPINIONS))}")
    
    output_dir = create_output_dir()
    
    all_results = {}
    
    # 实验 1：基础聚类
    r1 = experiment_1_basic_clustering()
    if r1:
        all_results["basic_clustering"] = r1
    
    # 实验 2：参数敏感性
    r2 = experiment_2_parameter_sensitivity()
    if r2:
        all_results["parameter_sensitivity"] = r2
    
    # 实验 3：增量性评分
    r3 = experiment_3_novelty_scoring()
    if r3:
        all_results["novelty_scoring"] = r3
    
    # 保存结果
    if all_results:
        save_results(all_results, output_dir)
    
    print_section("预研完成")
    print("待评估项:")
    print("  1. ARI > 0.6 → 聚类效果可用")
    print("  2. 噪音点 < 20% → HDBSCAN 参数合理")
    print("  3. novelty 能区分复述和增量 → 共鸣公式可行")
    print("  4. 聚类耗时 < 5s (37条数据) → 扩展性可接受")


if __name__ == "__main__":
    main()
