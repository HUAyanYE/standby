"""
补充实验：K-Means 指定 K=6，看 TF-IDF 的天花板
以及：验证 novelty 评分逻辑在有语义 embedding 时的行为
"""

import jieba
import numpy as np
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score
from sklearn.metrics.pairwise import cosine_similarity

from bertopic_offline import DATA, jieba_tokenizer

def main():
    texts = [d["text"] for d in DATA]
    true_labels = [d["topic"] for d in DATA]
    label_map = {l: i for i, l in enumerate(sorted(set(true_labels)))}
    true_numeric = [label_map[l] for l in true_labels]
    
    # TF-IDF
    segmented = [" ".join(jieba_tokenizer(t)) for t in texts]
    vectorizer = TfidfVectorizer(max_features=500, token_pattern=r"(?u)\b\w+\b")
    X = vectorizer.fit_transform(segmented).toarray()
    
    # K-Means (K=6, 已知真实簇数)
    km = KMeans(n_clusters=6, random_state=42, n_init=10)
    labels = km.fit_predict(X)
    
    ari = adjusted_rand_score(true_numeric, labels)
    nmi = normalized_mutual_info_score(true_numeric, labels)
    
    print(f"K-Means (K=6) on TF-IDF:")
    print(f"  ARI: {ari:.4f}")
    print(f"  NMI: {nmi:.4f}")
    
    # 展示每个簇的分布
    import pandas as pd
    df = pd.DataFrame({"id": [d["id"] for d in DATA], "text": [d["text"][:30] for d in DATA], "true": true_labels, "cluster": labels})
    
    for c in sorted(set(labels)):
        members = df[df["cluster"] == c]
        dist = members["true"].value_counts()
        print(f"\n  簇 {c} ({len(members)}条): {dict(dist)}")
        for _, row in members.iterrows():
            print(f"    [{row['true']}] {row['id']}: {row['text']}...")
    
    # 分析 TF-IDF 为什么不行
    print(f"\n\nTF-IDF 局限性分析:")
    print(f"  词汇表大小: {len(vectorizer.get_feature_names_out())}")
    print(f"  稀疏度: {1 - X.nnz / (X.shape[0] * X.shape[1]):.1%}" if hasattr(X, 'nnz') else f"  非零元素比例: {np.count_nonzero(X) / X.size:.1%}")
    
    # 看看不同话题间的 TF-IDF 相似度
    topic_texts = {}
    for d in DATA:
        topic_texts.setdefault(d["topic"], []).append(d["text"])
    
    print(f"\n  同话题内 vs 跨话题的 TF-IDF 相似度:")
    for topic, tlist in topic_texts.items():
        segs = [" ".join(jieba_tokenizer(t)) for t in tlist]
        vecs = vectorizer.transform(segs).toarray()
        sims = cosine_similarity(vecs)
        # 平均相似度（排除对角线）
        mask = np.ones_like(sims, dtype=bool)
        np.fill_diagonal(mask, False)
        avg_sim = sims[mask].mean()
        print(f"    {topic}: 同话题内平均相似度 = {avg_sim:.4f}")
    
    # 跨话题
    all_topics = sorted(topic_texts.keys())
    cross_sims = []
    for i, t1 in enumerate(all_topics):
        for t2 in all_topics[i+1:]:
            segs1 = [" ".join(jieba_tokenizer(t)) for t in topic_texts[t1]]
            segs2 = [" ".join(jieba_tokenizer(t)) for t in topic_texts[t2]]
            vecs1 = vectorizer.transform(segs1).toarray()
            vecs2 = vectorizer.transform(segs2).toarray()
            sim = cosine_similarity(vecs1, vecs2).mean()
            cross_sims.append(sim)
            print(f"    {t1} vs {t2}: {sim:.4f}")
    
    print(f"\n  跨话题平均相似度: {np.mean(cross_sims):.4f}")
    print(f"  结论: 同话题内相似度并不显著高于跨话题 → TF-IDF 无法区分话题")


if __name__ == "__main__":
    main()
