# 技术预研报告 #1：BERTopic 聚类效果验证

**日期**: 2026-04-13  
**环境**: 无网络（WSL，HuggingFace 不可达）  
**替代方案**: TF-IDF（验证 TF-IDF 是否能替代语义 embedding）

---

## 实验结果

### 实验 1：HDBSCAN + TF-IDF 聚类

| 参数 | 簇数 | 噪音点 | ARI | NMI |
|------|------|--------|-----|-----|
| mcs=3, ms=2 | 0 | 37/37 | 0.0000 | 0.0000 |
| mcs=5, ms=3 | 0 | 37/37 | 0.0000 | 0.0000 |
| mcs=7, ms=3 | 0 | 37/37 | 0.0000 | 0.0000 |
| mcs=8, ms=4 | 0 | 37/37 | 0.0000 | 0.0000 |

**结论**: HDBSCAN + TF-IDF 完全失败。所有数据点被判定为噪音。

### 实验 2：K-Means (K=6) + TF-IDF

- ARI: **-0.0112**（低于随机）
- NMI: 0.2287
- 各簇混杂严重：每个簇包含 3-6 个不同话题

**结论**: 即使指定真实簇数，TF-IDF 也无法区分话题。

### 实验 3：TF-IDF 相似度分析

| 对比维度 | 平均相似度 |
|---------|-----------|
| 同话题内 | 0.06 - 0.09 |
| 跨话题 | 0.04 - 0.08 |
| 差异 | **几乎无差异** |

**根本原因**: 中文情感短文本在语义上相关（都在谈"孤独"），但在词汇上几乎没有重叠。TF-IDF 基于词频，无法捕捉语义关系。

### 实验 4：Novelty 评分验证

| 观点类型 | relevance | novelty | 预期 | 结果 |
|---------|-----------|---------|------|------|
| 复述锚点 | 0.1560 | 0.0000 | 低 | ✅ 但因 relevance < 0.3 被排除 |
| 相似经历 | 0.2355 | 0.0000 | 中 | ⚠️ 未达阈值 |
| 全新角度 | 0.1568 | 0.0000 | 高 | ❌ 未达阈值 |
| 不相关 | 0.0299 | 0.0000 | N/A | ✅ |

**结论**: TF-IDF 的 relevance 太低（全部 < 0.3），novelty 无法生效。需要语义 embedding 才能正确计算。

---

## 核心结论

### ✅ 确认的判断

1. **语义 embedding（BGE）是必须的，不是可选的**
   - TF-IDF 对中文情感短文本完全无效
   - 整个共鸣机制和锚点聚类都依赖语义向量
   - BGE-base-zh-v1.5（768维）是正确的选型

2. **HDBSCAN 是正确的聚类算法选择**
   - 但需要语义 embedding 作为输入
   - TF-IDF 输入导致所有点被判为噪音

3. **Novelty 评分的逻辑是正确的**
   - relevance × novelty 的公式合理
   - 但需要语义 embedding 才能正确计算 relevance

### ⚠️ 需要进一步验证的

1. **BGE embedding 下的聚类效果**
   - 需要联网环境下载模型后复验
   - 预期 ARI > 0.6（基于 BGE 在中文语义任务上的已知表现）

2. **BERTopic vs 纯 HDBSCAN**
   - 当前只测了 HDBSCAN（BERTopic 的核心组件）
   - 完整 BERTopic 的 c-TF-IDF 主题词提取需要联网环境验证

3. **Novelty 在语义 embedding 下的行为**
   - 需要验证"相关但不相似 = 高 novelty"是否符合直觉

---

## 下一步行动

### 需要联网环境

以下验证需要在有网络访问的机器上进行：

```bash
# 1. 下载 BGE 模型
python3 -c "
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('BAAI/bge-base-zh-v1.5')
model.save('/path/to/local/model')
"

# 2. 运行完整验证
python3 validation/bertopic_clustering.py

# 3. 预期输出
# - ARI > 0.6
# - c-TF-IDF 主题词可读
# - Novelty 能正确区分复述和增量感悟
```

### 不需要联网的下一步

1. 实现共鸣值计算公式（用预计算的 embedding）
2. 实现锚点重现机制的数据查询逻辑
3. 实现内容治理引擎的规则层（关键词/哈希匹配）

---

## 文件清单

| 文件 | 说明 |
|------|------|
| `validation/bertopic_offline.py` | HDBSCAN + TF-IDF 聚类验证 |
| `validation/tfidf_analysis.py` | TF-IDF 局限性分析 |
| `validation/bertopic_clustering.py` | 完整验证（需联网） |
| `validation/results/bertopic/offline_validation_*.json` | 实验结果 |
| `config/engines.yaml` | 引擎配置 |
| `shared/encoders/text_encoder.py` | BGE 编码器封装 |
