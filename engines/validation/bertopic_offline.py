"""
阶段 0 技术预研：BERTopic 聚类效果验证（离线版）

使用 TF-IDF 替代 sentence-transformers 做 embedding，
在无网络环境下验证聚类算法的核心逻辑。

验证目标：
1. HDBSCAN + TF-IDF 对中文短文本的聚类效果
2. 参数敏感性（min_cluster_size, min_samples）
3. 增量性（novelty）评分逻辑验证
"""

import json
import time
from datetime import datetime
from pathlib import Path

import jieba
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score
from sklearn.metrics.pairwise import cosine_similarity

# ============================================================
# 数据集
# ============================================================

DATA = [
    # 孤独
    {"id": "01", "text": "深夜加班后独自坐在末班地铁上，窗外的城市灯火通明，但没有一盏灯是为我亮的。那种孤独感不是身边没有人，而是没有人知道你在这里。", "topic": "孤独"},
    {"id": "02", "text": "一个人去吃火锅，服务员问几位，说一位的时候对面放了一只小熊。那一刻突然觉得自己好像很可怜，但又好像没什么大不了。", "topic": "孤独"},
    {"id": "03", "text": "在大城市生活了五年，每天和几百万人擦肩而过，但能叫出名字的人不超过十个。不是社交能力差，是真的没有机会建立真正的联系。", "topic": "孤独"},
    {"id": "04", "text": "朋友圈里几百个人，发了一条深夜感慨，过了两个小时只有三个人点赞，没有一条评论。", "topic": "孤独"},
    {"id": "05", "text": "最孤独的时刻不是一个人，而是在人群中突然意识到，我和周围的每一个人都不在同一个频率上。", "topic": "孤独"},
    {"id": "06", "text": "搬来新城市三个月了，周末最大的活动就是去超市买菜。不是不想社交，是不知道怎么开始。", "topic": "孤独"},
    {"id": "07", "text": "我妈打来电话问我最近怎么样，我说挺好的。挂了电话才意识到，我已经很久没有对任何人说过真实的状态了。", "topic": "孤独"},

    # 音乐
    {"id": "08", "text": "在车里随机播放到了一首高中时代的老歌，副歌响起的瞬间，想起了那个夏天的操场。音乐是时间机器。", "topic": "音乐"},
    {"id": "09", "text": "有些歌你不是在听，你是在重访一段记忆。每一个音符都是一扇门，推开就是那个再也回不去的场景。", "topic": "音乐"},
    {"id": "10", "text": "深夜一个人戴着耳机听坂本龙一的钢琴曲，窗外在下雨。那一刻时间是静止的，只有音乐和雨声。", "topic": "音乐"},
    {"id": "11", "text": "小时候不理解父母为什么总听那些老歌，现在自己开始反复听十年前的歌单了。原来怀旧不是一种选择，是一种必然。", "topic": "音乐"},
    {"id": "12", "text": "在异国他乡的街头听到有人在弹中国民谣，站在那里听了整整十分钟。是因为那个旋律把我带回了家。", "topic": "音乐"},
    {"id": "13", "text": "有些歌只适合在特定的天气、特定的心境下听。今天下雨，适合听陈绮贞。", "topic": "音乐"},

    # 迷茫
    {"id": "14", "text": "二十多岁最大的恐惧不是失败，是不知道自己想要什么。看着同龄人好像都有明确的方向，只有我在原地打转。", "topic": "迷茫"},
    {"id": "15", "text": "毕业三年换了两份工作，每一份都做了一年多就厌倦了。是我好像对什么都提不起长期的热情。", "topic": "迷茫"},
    {"id": "16", "text": "父母希望我考公务员，朋友建议我去创业，但没人问过我自己想做什么。最可怕的是，我自己也不知道。", "topic": "迷茫"},
    {"id": "17", "text": "三十岁回头看，发现二十岁时的那些确定都是假的。真正确定的东西，是那些不确定中慢慢长出来的。", "topic": "迷茫"},
    {"id": "18", "text": "有时候觉得选择太多反而是诅咒。面前有无数条路，每一条都在诱惑你，每一条你都不敢选。", "topic": "迷茫"},
    {"id": "19", "text": "深夜刷到同龄人的朋友圈，有人结婚了，有人升职了，有人环游世界。关掉手机，还是不知道明天该干嘛。", "topic": "迷茫"},

    # 城市
    {"id": "20", "text": "上海的便利店密度全中国最高，凌晨三点也能买到一杯热咖啡。这大概就是大城市给你的确定性。", "topic": "城市"},
    {"id": "21", "text": "每天通勤一个半小时，在地铁里看书、听播客、发呆。这段不属于工作也不属于家的时间，反而是最自由的。", "topic": "城市"},
    {"id": "22", "text": "在北京住了三年，最有归属感的时刻不是在出租屋里，而是在楼下的那家面馆。老板已经记住我了。", "topic": "城市"},
    {"id": "23", "text": "大城市的节奏让人没有时间悲伤。上午被领导骂了，下午还有三个会要开。等晚上回到家，那股情绪已经不知道去哪了。", "topic": "城市"},
    {"id": "24", "text": "深圳是一个你随时可以重新开始的城市。没有人知道你的过去，也没有人在意你的未来。", "topic": "城市"},
    {"id": "25", "text": "周末去了一个从来没有去过的公园，在长椅上坐了一个下午。城市再大，也需要一个安静的角落。", "topic": "城市"},

    # 阅读
    {"id": "26", "text": "读到加缪的那句话：在隆冬，我终于知道，我身上有一个不可战胜的夏天。放下书想了很久。", "topic": "阅读"},
    {"id": "27", "text": "重读百年孤独，发现年轻时关注的是魔幻，现在关注的是孤独。同一本书在不同的人生阶段读，完全不同。", "topic": "阅读"},
    {"id": "28", "text": "在书店看到一个老人坐在角落里读一本旧书，书页已经泛黄了。读书这件事本身，就是一种抵抗。", "topic": "阅读"},
    {"id": "29", "text": "最近在读一本关于日本物哀美学的书。有些美只有在消逝的瞬间才能被感知。", "topic": "阅读"},
    {"id": "30", "text": "读完了活着，没有哭，但胸口堵了很久。好的文学不是让你流泪，是让你说不出话。", "topic": "阅读"},
    {"id": "31", "text": "有人说读书没用，不能赚钱不能升职。但读书让我知道了自己不是一个人在困惑。", "topic": "阅读"},

    # 关系
    {"id": "32", "text": "成年后最难的事是维持友谊。不是不想联系，是真的不知道说什么。上次聊天是半年前。", "topic": "关系"},
    {"id": "33", "text": "最好的朋友结婚了，我坐在台下哭了。不是因为感动，是因为知道从今以后她是别人的了。", "topic": "关系"},
    {"id": "34", "text": "和父母的关系，从对抗到和解到理解，用了将近十年。现在每次回家反而觉得他们越来越像小孩了。", "topic": "关系"},
    {"id": "35", "text": "分手后的第三个月，终于可以听到那首歌不哭了。但经过那家咖啡馆还是会绕路走。", "topic": "关系"},
    {"id": "36", "text": "同事和朋友的边界越来越模糊。每天相处八小时的人，出了公司大门就像不认识一样。", "topic": "关系"},
    {"id": "37", "text": "真正的亲密关系不是时刻在一起，而是即使很久不联系，再见面时也不会尴尬。", "topic": "关系"},
]


def jieba_tokenizer(text):
    return list(jieba.cut(text))


def build_tfidf_embeddings(texts):
    """用 TF-IDF 构建文本向量"""
    # 对中文分词后再做 TF-IDF
    segmented = [" ".join(jieba_tokenizer(t)) for t in texts]
    
    vectorizer = TfidfVectorizer(
        max_features=500,
        token_pattern=r"(?u)\b\w+\b",  # 匹配分词后的词
    )
    embeddings = vectorizer.fit_transform(segmented).toarray()
    return embeddings, vectorizer


def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def test_clustering():
    """实验 1：基础聚类 + 参数敏感性"""
    print_section("实验 1 & 2：聚类效果 + 参数敏感性")
    
    from bertopic import BERTopic
    import hdbscan
    
    texts = [d["text"] for d in DATA]
    true_labels = [d["topic"] for d in DATA]
    label_map = {l: i for i, l in enumerate(sorted(set(true_labels)))}
    true_numeric = [label_map[l] for l in true_labels]
    
    print(f"数据集: {len(texts)} 条")
    print(f"真实话题: {sorted(set(true_labels))}")
    
    # 构建 TF-IDF embeddings
    print("\n构建 TF-IDF embeddings...")
    embeddings, vectorizer = build_tfidf_embeddings(texts)
    print(f"  向量维度: {embeddings.shape}")
    
    # 参数网格
    param_grid = [
        {"min_cluster_size": 3, "min_samples": 2},
        {"min_cluster_size": 4, "min_samples": 2},
        {"min_cluster_size": 5, "min_samples": 3},
        {"min_cluster_size": 6, "min_samples": 3},
        {"min_cluster_size": 7, "min_samples": 3},
        {"min_cluster_size": 8, "min_samples": 4},
    ]
    
    results = []
    
    for params in param_grid:
        # 直接用 HDBSCAN（跳过 BERTopic 的 embedding 层）
        clusterer = hdbscan.HDBSCAN(
            min_cluster_size=params["min_cluster_size"],
            min_samples=params["min_samples"],
            metric="euclidean",
        )
        topics = clusterer.fit_predict(embeddings)
        
        ari = adjusted_rand_score(true_numeric, topics)
        nmi = normalized_mutual_info_score(true_numeric, topics)
        
        n_clusters = len(set(topics) - {-1})
        n_outliers = sum(1 for t in topics if t == -1)
        
        result = {
            **params,
            "n_clusters": n_clusters,
            "n_outliers": n_outliers,
            "ari": round(ari, 4),
            "nmi": round(nmi, 4),
        }
        results.append(result)
        
        print(f"  mcs={params['min_cluster_size']}, ms={params['min_samples']}"
              f" → 簇={n_clusters}, 噪音={n_outliers}, ARI={ari:.4f}, NMI={nmi:.4f}")
    
    best = max(results, key=lambda x: x["ari"])
    print(f"\n✅ 最优: mcs={best['min_cluster_size']}, ms={best['min_samples']}, ARI={best['ari']}")
    
    # 用最优参数展示聚类结果
    print(f"\n聚类结果 vs 真实标签:")
    clusterer = hdbscan.HDBSCAN(
        min_cluster_size=best["min_cluster_size"],
        min_samples=best["min_samples"],
        metric="euclidean",
    )
    topics = clusterer.fit_predict(embeddings)
    
    # 展示每个簇的内容
    df = pd.DataFrame({
        "id": [d["id"] for d in DATA],
        "text": [d["text"][:40] + "..." for d in DATA],
        "true_topic": true_labels,
        "cluster": topics,
    })
    
    for cluster_id in sorted(set(topics)):
        members = df[df["cluster"] == cluster_id]
        if cluster_id == -1:
            print(f"\n  噪音点 ({len(members)} 条):")
        else:
            topic_dist = members["true_topic"].value_counts()
            dominant = topic_dist.index[0]
            purity = topic_dist.iloc[0] / len(members)
            print(f"\n  簇 {cluster_id} ({len(members)} 条, 主导话题={dominant}, 纯度={purity:.0%}):")
        for _, row in members.iterrows():
            print(f"    [{row['true_topic']}] {row['id']}: {row['text']}")
    
    return results, best


def test_novelty():
    """实验 3：增量性评分验证"""
    print_section("实验 3：观点增量性 (novelty) 评分")
    
    anchor = "深夜独自坐在末班地铁上，窗外灯火通明，但没有一盏灯是为我亮的。"
    
    test_cases = [
        {"label": "复述锚点", "text": "是啊，深夜坐地铁确实很孤独，窗外的灯都不属于我。", "expected_novelty": "低"},
        {"label": "相似经历", "text": "我也曾在深夜的末班地铁上，一个人看着窗外发呆，觉得整个世界都和我没关系。", "expected_novelty": "中"},
        {"label": "全新角度", "text": "孤独不是身边没有人，是没有人知道你在哪里。有一次在机场候机厅过夜，周围全是人但没有一个人认识我。", "expected_novelty": "高"},
        {"label": "不相关", "text": "今天中午吃的麻辣烫特别好吃，下次还要去那家店。", "expected_novelty": "N/A"},
    ]
    
    print(f"锚点: {anchor}\n")
    
    # 用 TF-IDF 计算相似度
    all_texts = [anchor] + [c["text"] for c in test_cases]
    segmented = [" ".join(jieba_tokenizer(t)) for t in all_texts]
    
    vectorizer = TfidfVectorizer(max_features=200, token_pattern=r"(?u)\b\w+\b")
    tfidf_matrix = vectorizer.fit_transform(segmented).toarray()
    
    anchor_vec = tfidf_matrix[0:1]
    case_vecs = tfidf_matrix[1:]
    
    # relevance: 与锚点的相似度
    relevance = cosine_similarity(anchor_vec, case_vecs)[0]
    
    # novelty: 在已有观点中，与最相似观点的距离
    # 简化：novelty = 1 - max(与锚点的相似度, 与其他case的平均相似度)
    pairwise = cosine_similarity(case_vecs)
    
    print(f"{'标签':<15} {'relevance':>10} {'novelty':>8} {'预期':>6} {'验证':>6}")
    print("-" * 55)
    
    results = []
    for i, case in enumerate(test_cases):
        rel = relevance[i]
        
        # novelty: 与锚点和已有观点都不相似 = 高 novelty
        max_sim_to_others = max(
            pairwise[i][j] for j in range(len(test_cases)) if j != i
        ) if len(test_cases) > 1 else 0
        
        # 与锚点相似度高 且 与其他观点也相似 = 复述（低 novelty）
        # 与锚点相关但与其他观点不相似 = 新视角（高 novelty）
        if rel < 0.3:
            novelty = 0  # 不相关
        else:
            novelty = round(max(0, 1 - max(rel, max_sim_to_others)), 4)
        
        # 验证是否符合预期
        if case["expected_novelty"] == "低":
            ok = "✅" if novelty < 0.5 else "❌"
        elif case["expected_novelty"] == "高":
            ok = "✅" if novelty > 0.3 else "❌"
        elif case["expected_novelty"] == "中":
            ok = "✅" if 0.2 < novelty < 0.7 else "⚠️"
        else:
            ok = "✅"  # 不相关
        
        print(f"{case['label']:<15} {rel:>10.4f} {novelty:>8.4f} {case['expected_novelty']:>6} {ok:>6}")
        
        results.append({
            "label": case["label"],
            "relevance": round(float(rel), 4),
            "novelty": float(novelty),
            "expected": case["expected_novelty"],
        })
    
    print(f"\n📌 关键公式:")
    print(f"   relevance > 0.3 AND novelty > 0.3 → 高价值增量感悟")
    print(f"   relevance > 0.3 AND novelty < 0.3 → 复述，低价值")
    print(f"   relevance < 0.3 → 不相关，不计入")
    
    return results


def main():
    print_section("Standby AI Engines - 技术预研 (离线版)")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"环境: 无网络，使用 TF-IDF 替代 sentence-transformers")
    
    all_results = {}
    
    # 实验 1 & 2
    clustering_results, best_params = test_clustering()
    all_results["clustering"] = {
        "param_grid": clustering_results,
        "best": best_params,
    }
    
    # 实验 3
    novelty_results = test_novelty()
    all_results["novelty"] = novelty_results
    
    # 保存
    results_dir = Path(__file__).parent / "results" / "bertopic"
    results_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = results_dir / f"offline_validation_{timestamp}.json"
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    
    print(f"\n📊 结果已保存: {output_file}")
    
    # 总结
    print_section("预研结论")
    
    ari = best_params["ari"]
    if ari > 0.6:
        print(f"✅ 聚类效果: ARI={ari} (> 0.6, 可用)")
    elif ari > 0.4:
        print(f"⚠️ 聚类效果: ARI={ari} (0.4-0.6, 需要调参或更好的 embedding)")
    else:
        print(f"❌ 聚类效果: ARI={ari} (< 0.4, TF-IDF 不够，需要语义 embedding)")
    
    print(f"  最优参数: min_cluster_size={best_params['min_cluster_size']}, "
          f"min_samples={best_params['min_samples']}")
    print(f"  噪音点: {best_params['n_outliers']}/{len(DATA)}")
    print(f"\n⚠️ 注意: 当前使用 TF-IDF (离线)，有网络后需用 BGE 语义 embedding 复验")
    print(f"  预期语义 embedding 的 ARI 会显著高于 TF-IDF")


if __name__ == "__main__":
    main()
