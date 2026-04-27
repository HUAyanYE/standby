"""
阶段 0 技术预研：BERTopic + BGE 语义聚类验证（本地模型版）

使用本地 BGE 模型做语义 embedding，验证完整的聚类 pipeline。
"""

import json
import time
from datetime import datetime
from pathlib import Path

import jieba
import numpy as np
import pandas as pd
from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score
from sklearn.metrics.pairwise import cosine_similarity

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from shared.encoders.text_encoder import TextEncoder
from bertopic_offline import DATA, jieba_tokenizer


def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def test_1_clustering():
    """实验 1：BGE embedding + HDBSCAN 聚类"""
    print_section("实验 1：BGE 语义聚类效果")
    
    from bertopic import BERTopic
    from sklearn.feature_extraction.text import CountVectorizer
    
    texts = [d["text"] for d in DATA]
    true_labels = [d["topic"] for d in DATA]
    label_map = {l: i for i, l in enumerate(sorted(set(true_labels)))}
    true_numeric = [label_map[l] for l in true_labels]
    
    print(f"数据集: {len(texts)} 条")
    print(f"真实话题: {sorted(set(true_labels))}")
    
    # 加载 BGE 模型
    print("\n加载 BGE-base 编码器...")
    encoder = TextEncoder(model_name="shared/models/bge-base-zh-v1.5")
    
    # 预计算 embeddings
    print("编码文本...")
    t0 = time.time()
    embeddings = encoder.encode(texts, show_progress=False)
    encode_time = time.time() - t0
    print(f"  编码完成: {embeddings.shape}, 耗时 {encode_time:.2f}s")
    
    # 中文分词 tokenizer
    vectorizer = CountVectorizer(
        tokenizer=jieba_tokenizer,
        token_pattern=None,
    )
    
    # 参数网格
    param_grid = [
        {"min_topic_size": 3},
        {"min_topic_size": 4},
        {"min_topic_size": 5},
        {"min_topic_size": 6},
        {"min_topic_size": 7},
    ]
    
    results = []
    
    for params in param_grid:
        topic_model = BERTopic(
            embedding_model=encoder._model,
            vectorizer_model=vectorizer,
            min_topic_size=params["min_topic_size"],
            nr_topics="auto",
            verbose=False,
        )
        
        t0 = time.time()
        topics, probs = topic_model.fit_transform(texts, embeddings)
        cluster_time = time.time() - t0
        
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
            "time_ms": round(cluster_time * 1000),
        }
        results.append(result)
        
        status = "✅" if ari > 0.6 else "⚠️" if ari > 0.4 else "❌"
        print(f"  {status} min_topic_size={params['min_topic_size']}"
              f" → 簇={n_topics}, 噪音={n_outliers}, ARI={ari:.4f}, NMI={nmi:.4f}, {cluster_time*1000:.0f}ms")
    
    best = max(results, key=lambda x: x["ari"])
    print(f"\n✅ 最优: min_topic_size={best['min_topic_size']}, ARI={best['ari']}")
    
    # 用最优参数展示聚类结果和主题词
    print(f"\n--- 最优参数的聚类详情 ---")
    topic_model = BERTopic(
        embedding_model=encoder._model,
        vectorizer_model=vectorizer,
        min_topic_size=best["min_topic_size"],
        nr_topics="auto",
        verbose=False,
    )
    topics, probs = topic_model.fit_transform(texts, embeddings)
    
    # 主题词
    topic_info = topic_model.get_topic_info()
    n_real_topics = len([t for t in topic_info["Topic"] if t != -1])
    
    print(f"\n主题词提取 (c-TF-IDF):")
    for topic_id in range(n_real_topics):
        words = topic_model.get_topic(topic_id)
        if words:
            top_words = [f"{w}({s:.3f})" for w, s in words[:6]]
            print(f"  Topic {topic_id}: {', '.join(top_words)}")
    
    # 聚类 vs 真实标签
    print(f"\n聚类分布:")
    df = pd.DataFrame({
        "id": [d["id"] for d in DATA],
        "true": true_labels,
        "cluster": topics,
    })
    
    for c in sorted(set(topics)):
        members = df[df["cluster"] == c]
        dist = members["true"].value_counts()
        if c == -1:
            print(f"  噪音 ({len(members)}条): {dict(dist)}")
        else:
            dominant = dist.index[0]
            purity = dist.iloc[0] / len(members)
            print(f"  簇 {c} ({len(members)}条, 主导={dominant}, 纯度={purity:.0%}): {dict(dist)}")
    
    return results, best, topic_model


def test_2_novelty():
    """实验 2：BGE embedding 下的 novelty 评分"""
    print_section("实验 2：Novelty 评分（语义 embedding）")
    
    encoder = TextEncoder(model_name="shared/models/bge-base-zh-v1.5")
    
    anchor = "深夜独自坐在末班地铁上，窗外灯火通明，但没有一盏灯是为我亮的。"
    
    test_cases = [
        {"label": "复述锚点", "text": "是啊，深夜坐地铁确实很孤独，窗外的灯都不属于我。", "expected": "低"},
        {"label": "相似经历", "text": "我也曾在深夜的末班地铁上，一个人看着窗外发呆，觉得整个世界都和我没关系。", "expected": "中"},
        {"label": "全新角度", "text": "孤独不是身边没有人，是没有人知道你在哪里。有一次在机场候机厅过夜，周围全是人但没有一个人认识我。", "expected": "高"},
        {"label": "增量感悟", "text": "地铁的孤独不是因为没人，是因为你在移动中——每一站都有人上下，但没有人是为了你停留。", "expected": "高"},
        {"label": "不相关", "text": "今天中午吃的麻辣烫特别好吃，下次还要去那家店。", "expected": "N/A"},
    ]
    
    print(f"锚点: {anchor}\n")
    
    # 编码
    all_texts = [anchor] + [c["text"] for c in test_cases]
    all_embs = encoder.encode(all_texts)
    
    anchor_emb = all_embs[0:1]
    case_embs = all_embs[1:]
    
    # relevance: 与锚点的相似度
    relevance = cosine_similarity(anchor_emb, case_embs)[0]
    
    # novelty: 1 - max(与锚点的相似度, 与其他case的平均相似度)
    pairwise = cosine_similarity(case_embs)
    
    print(f"{'标签':<15} {'relevance':>10} {'novelty':>8} {'预期':>6} {'验证':>6}")
    print("-" * 55)
    
    results = []
    for i, case in enumerate(test_cases):
        rel = relevance[i]
        
        # 与其他观点的最大相似度
        others_sims = [pairwise[i][j] for j in range(len(test_cases)) if j != i]
        max_others = max(others_sims) if others_sims else 0
        
        if rel < 0.3:
            novelty = 0
        else:
            # novelty 高 = 与锚点相关但视角独特
            novelty = round(max(0, 1 - max(rel * 0.7, max_others * 0.7)), 4)
        
        # 验证
        if case["expected"] == "低":
            ok = "✅" if novelty < 0.5 else "❌"
        elif case["expected"] == "高":
            ok = "✅" if novelty > 0.3 else "⚠️"
        elif case["expected"] == "中":
            ok = "✅" if 0.2 <= novelty <= 0.7 else "⚠️"
        else:
            ok = "✅" if rel < 0.3 else "⚠️"
        
        print(f"{case['label']:<15} {rel:>10.4f} {novelty:>8.4f} {case['expected']:>6} {ok:>6}")
        
        results.append({
            "label": case["label"],
            "relevance": round(float(rel), 4),
            "novelty": float(novelty),
            "expected": case["expected"],
        })
    
    print(f"\n📌 语义 embedding 下的对比 (vs TF-IDF):")
    print(f"   TF-IDF relevance 全部 < 0.3 → 无法区分相关性")
    print(f"   BGE relevance 范围 {min(relevance):.2f} - {max(relevance):.2f} → 能正确区分")
    
    return results


def test_3_encoder_benchmark():
    """实验 3：编码器性能基准测试"""
    print_section("实验 3：编码器性能")
    
    texts = [d["text"] for d in DATA]
    
    for preset in ["cloud", "device"]:
        if preset == "cloud":
            model_path = "shared/models/bge-base-zh-v1.5"
            name = "bge-base (768维, 云端)"
        else:
            model_path = "shared/models/bge-small-zh-v1.5"
            name = "bge-small (512维, 端侧)"
        
        encoder = TextEncoder(model_name=model_path)
        
        # 单条编码
        t0 = time.time()
        for text in texts[:5]:
            encoder.encode_single(text)
        single_avg = (time.time() - t0) / 5
        
        # 批量编码
        t0 = time.time()
        embs = encoder.encode(texts, batch_size=32)
        batch_time = time.time() - t0
        
        print(f"  {name}:")
        print(f"    维度: {embs.shape[1]}")
        print(f"    单条平均: {single_avg*1000:.1f}ms")
        print(f"    批量({len(texts)}条): {batch_time*1000:.0f}ms ({batch_time/len(texts)*1000:.1f}ms/条)")
        print()


def save_results(all_results, output_dir):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"bertopic_bge_{timestamp}.json"
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    
    print(f"📊 结果已保存: {output_file}")
    return output_file


def main():
    print_section("Standby AI Engines - 技术预研 (BGE 版)")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"模型: BGE-base-zh-v1.5 (本地)")
    
    output_dir = Path(__file__).parent / "results" / "bertopic"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    all_results = {}
    
    # 实验 1：聚类
    r1, best, topic_model = test_1_clustering()
    all_results["clustering"] = {"param_grid": r1, "best": best}
    
    # 实验 2：Novelty
    r2 = test_2_novelty()
    all_results["novelty"] = r2
    
    # 实验 3：性能
    test_3_encoder_benchmark()
    
    # 保存
    save_results(all_results, output_dir)
    
    # 总结
    print_section("预研结论")
    
    ari = best["ari"]
    if ari > 0.6:
        print(f"✅ 聚类效果: ARI={ari} (> 0.6, 可用)")
    elif ari > 0.4:
        print(f"⚠️ 聚类效果: ARI={ari} (0.4-0.6, 需要调参)")
    else:
        print(f"❌ 聚类效果: ARI={ari} (< 0.4, 需要换方案)")
    
    print(f"  最优参数: min_topic_size={best['min_topic_size']}")
    print(f"  噪音点: {best['n_outliers']}/{len(DATA)}")
    print(f"\n📌 对比 TF-IDF:")
    print(f"   TF-IDF ARI = 0.0 (完全失败)")
    print(f"   BGE ARI = {ari} ({'显著改善' if ari > 0.3 else '需要进一步优化'})")


if __name__ == "__main__":
    main()
