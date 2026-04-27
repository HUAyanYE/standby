"""
端侧 ONNX 模型导出与性能基准

将 BGE-small-zh-v1.5 从 PyTorch 导出为 ONNX 格式，
并对比 PyTorch vs ONNX Runtime 的推理性能。

依赖：
  pip install onnx onnxruntime

使用：
  python3 onnx_export.py              # 导出 + 基准测试
  python3 onnx_export.py --export     # 仅导出
  python3 onnx_export.py --benchmark  # 仅基准测试
"""

import argparse
import os
import sys
import time
from pathlib import Path

import numpy as np
import torch
from transformers import AutoTokenizer, AutoModel

# ============================================================
# 配置
# ============================================================

MODELS_DIR = Path(__file__).parent.parent / "shared" / "models"
BGE_SMALL_DIR = MODELS_DIR / "bge-small-zh-v1.5"
ONNX_OUTPUT_DIR = MODELS_DIR / "bge-small-zh-v1.5-onnx"

TEST_SENTENCES = [
    "深夜独自坐在末班地铁上，窗外灯火通明，但没有一盏灯是为我亮的。",
    "孤独不是身边没有人，是没有人知道你在哪里。",
    "地铁的孤独不是因为没人，是因为你在移动中。",
    "我不觉得这是孤独，这只是大城市生活的常态。",
    "春天来了，万物复苏。",
    "今天和十年前的自己重逢了。",
    "秋天的第一片叶子落下了。",
    "一个人吃饭、一个人看电影、一个人旅行。",
    "城市里的每个人都是孤岛。",
    "深夜的便利店是流浪灵魂的避风港。",
]


# ============================================================
# 模型导出
# ============================================================

def export_to_onnx(
    model_dir: Path,
    output_dir: Path,
    max_length: int = 128,
) -> Path:
    """将 BGE-small 导出为 ONNX 格式
    
    使用 torch.onnx.export 直接导出（不依赖 optimum）
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    onnx_path = output_dir / "model.onnx"
    
    print(f"📦 加载模型: {model_dir}")
    tokenizer = AutoTokenizer.from_pretrained(str(model_dir))
    model = AutoModel.from_pretrained(str(model_dir))
    model.eval()
    
    # 构造示例输入
    dummy_text = "示例文本"
    dummy_inputs = tokenizer(
        dummy_text,
        return_tensors="pt",
        padding="max_length",
        max_length=max_length,
        truncation=True,
    )
    
    # 导出参数
    input_names = ["input_ids", "attention_mask"]
    output_names = ["last_hidden_state"]
    dynamic_axes = {
        "input_ids": {0: "batch_size", 1: "sequence"},
        "attention_mask": {0: "batch_size", 1: "sequence"},
        "last_hidden_state": {0: "batch_size", 1: "sequence"},
    }
    
    print(f"🔄 导出 ONNX → {onnx_path}")
    print(f"   max_length={max_length}")
    
    torch.onnx.export(
        model,
        (
            dummy_inputs["input_ids"],
            dummy_inputs["attention_mask"],
        ),
        str(onnx_path),
        input_names=input_names,
        output_names=output_names,
        dynamic_axes=dynamic_axes,
        opset_version=14,
        do_constant_folding=True,
    )
    
    # 复制 tokenizer 文件（ONNX Runtime 需要）
    import shutil
    for fname in ["vocab.txt", "tokenizer_config.json", "special_tokens_map.json"]:
        src = model_dir / fname
        if src.exists():
            shutil.copy2(src, output_dir / fname)
            print(f"   复制 {fname}")
    
    # 检查文件大小
    size_mb = onnx_path.stat().st_size / (1024 * 1024)
    print(f"✅ 导出完成: {onnx_path} ({size_mb:.1f} MB)")
    
    return onnx_path


def optimize_onnx(onnx_path: Path) -> Path:
    """ONNX 模型优化（融合算子）"""
    try:
        import onnx
        from onnxruntime.transformers import optimizer
        
        opt_path = onnx_path.parent / "model_optimized.onnx"
        
        print(f"🔧 优化 ONNX 模型...")
        opt_model = optimizer.optimize_model(
            str(onnx_path),
            model_type="bert",
            optimization_options={
                "enable_gelu": True,
                "enable_layer_norm": True,
                "enable_attention": True,
            },
        )
        opt_model.convert_float_to_float16()
        opt_model.save_model_to_file(str(opt_path))
        
        size_mb = opt_path.stat().st_size / (1024 * 1024)
        print(f"✅ 优化完成: {opt_path} ({size_mb:.1f} MB, FP16)")
        
        return opt_path
    except ImportError:
        print("⚠️  onnxruntime.transformers 不可用，跳过优化")
        return onnx_path


# ============================================================
# 性能基准
# ============================================================

class PyTorchEncoder:
    """PyTorch 编码器"""
    
    def __init__(self, model_dir: Path):
        self.tokenizer = AutoTokenizer.from_pretrained(str(model_dir))
        self.model = AutoModel.from_pretrained(str(model_dir))
        self.model.eval()
    
    def encode(self, texts: list[str], max_length: int = 128) -> np.ndarray:
        """编码文本 → embedding"""
        encoded = self.tokenizer(
            texts,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=max_length,
        )
        
        with torch.no_grad():
            outputs = self.model(**encoded)
            # CLS token embedding + L2 归一化
            embeddings = outputs.last_hidden_state[:, 0, :]
            embeddings = torch.nn.functional.normalize(embeddings, p=2, dim=1)
        
        return embeddings.numpy()


class ONNXEncoder:
    """ONNX Runtime 编码器"""
    
    def __init__(self, onnx_path: Path, model_dir: Path):
        import onnxruntime as ort
        
        self.tokenizer = AutoTokenizer.from_pretrained(str(model_dir))
        
        # 会话配置（优化推理速度）
        sess_options = ort.SessionOptions()
        sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        sess_options.intra_op_num_threads = 4
        
        self.session = ort.InferenceSession(
            str(onnx_path),
            sess_options=sess_options,
            providers=["CPUExecutionProvider"],
        )
    
    def encode(self, texts: list[str], max_length: int = 128) -> np.ndarray:
        """编码文本 → embedding"""
        encoded = self.tokenizer(
            texts,
            return_tensors="np",
            padding=True,
            truncation=True,
            max_length=max_length,
        )
        
        outputs = self.session.run(
            None,
            {
                "input_ids": encoded["input_ids"].astype(np.int64),
                "attention_mask": encoded["attention_mask"].astype(np.int64),
            },
        )
        
        # CLS token + L2 归一化
        embeddings = outputs[0][:, 0, :]
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        embeddings = embeddings / norms
        
        return embeddings


def run_benchmark(
    model_dir: Path,
    onnx_path: Path,
    sentences: list[str],
    warmup: int = 3,
    iterations: int = 10,
    batch_sizes: list[int] = None,
) -> dict:
    """运行性能基准测试"""
    if batch_sizes is None:
        batch_sizes = [1, 4, 16]
    
    results = {}
    
    # --- PyTorch 基准 ---
    print("\n📊 PyTorch 推理基准")
    pt_encoder = PyTorchEncoder(model_dir)
    
    pt_results = {}
    for bs in batch_sizes:
        batch = sentences[:bs]
        
        # Warmup
        for _ in range(warmup):
            pt_encoder.encode(batch)
        
        # 计时
        times = []
        for _ in range(iterations):
            start = time.perf_counter()
            pt_encoder.encode(batch)
            elapsed = time.perf_counter() - start
            times.append(elapsed)
        
        avg_ms = np.mean(times) * 1000
        std_ms = np.std(times) * 1000
        per_item = avg_ms / bs
        
        pt_results[bs] = {"avg_ms": avg_ms, "std_ms": std_ms, "per_item_ms": per_item}
        print(f"  batch={bs:>2}: {avg_ms:>8.1f}ms ± {std_ms:>5.1f}ms  ({per_item:>6.1f}ms/条)")
    
    results["pytorch"] = pt_results
    
    # --- ONNX 基准 ---
    print("\n📊 ONNX Runtime 推理基准")
    
    try:
        import onnxruntime as ort
        onnx_encoder = ONNXEncoder(onnx_path, model_dir)
        
        onnx_results = {}
        for bs in batch_sizes:
            batch = sentences[:bs]
            
            # Warmup
            for _ in range(warmup):
                onnx_encoder.encode(batch)
            
            # 计时
            times = []
            for _ in range(iterations):
                start = time.perf_counter()
                onnx_encoder.encode(batch)
                elapsed = time.perf_counter() - start
                times.append(elapsed)
            
            avg_ms = np.mean(times) * 1000
            std_ms = np.std(times) * 1000
            per_item = avg_ms / bs
            
            onnx_results[bs] = {"avg_ms": avg_ms, "std_ms": std_ms, "per_item_ms": per_item}
            print(f"  batch={bs:>2}: {avg_ms:>8.1f}ms ± {std_ms:>5.1f}ms  ({per_item:>6.1f}ms/条)")
        
        results["onnx"] = onnx_results
        
        # --- 加速比 ---
        print("\n📊 加速比（ONNX vs PyTorch）")
        for bs in batch_sizes:
            pt = pt_results[bs]["per_item_ms"]
            ox = onnx_results[bs]["per_item_ms"]
            speedup = pt / ox
            print(f"  batch={bs:>2}: {speedup:.2f}x")
        
        results["speedup"] = {
            bs: pt_results[bs]["per_item_ms"] / onnx_results[bs]["per_item_ms"]
            for bs in batch_sizes
        }
    
    except ImportError:
        print("  ⚠️  onnxruntime 未安装，跳过 ONNX 基准")
        results["onnx"] = None
        results["speedup"] = None
    
    # --- 文件大小对比 ---
    print("\n📊 模型大小")
    pt_size = sum(f.stat().st_size for f in model_dir.rglob("*") if f.is_file()) / (1024 * 1024)
    onnx_size = onnx_path.stat().st_size / (1024 * 1024) if onnx_path.exists() else 0
    
    print(f"  PyTorch:  {pt_size:.1f} MB (含 tokenizer)")
    print(f"  ONNX:     {onnx_size:.1f} MB (仅模型)")
    print(f"  压缩比:    {pt_size / onnx_size:.1f}x" if onnx_size > 0 else "  压缩比: N/A")
    
    results["sizes"] = {"pytorch_mb": pt_size, "onnx_mb": onnx_size}
    
    # --- 相似度验证 ---
    print("\n📊 相似度验证（PyTorch vs ONNX 输出一致性）")
    try:
        import onnxruntime as ort
        pt_emb = pt_encoder.encode(sentences[:5])
        onnx_emb = onnx_encoder.encode(sentences[:5])
        
        # 逐条余弦相似度
        for i in range(5):
            cos_sim = np.dot(pt_emb[i], onnx_emb[i])
            print(f"  句子 {i+1}: 余弦相似度 = {cos_sim:.6f}")
        
        avg_sim = np.mean([np.dot(pt_emb[i], onnx_emb[i]) for i in range(5)])
        print(f"  平均相似度: {avg_sim:.6f} {'✅' if avg_sim > 0.99 else '⚠️'}")
        results["similarity_check"] = avg_sim
    except (ImportError, NameError):
        print("  ⚠️  跳过")
        results["similarity_check"] = None
    
    return results


# ============================================================
# 主入口
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="BGE-small ONNX 导出与基准测试")
    parser.add_argument("--export", action="store_true", help="仅导出 ONNX")
    parser.add_argument("--benchmark", action="store_true", help="仅基准测试")
    parser.add_argument("--optimize", action="store_true", help="优化 ONNX 模型")
    parser.add_argument("--max-length", type=int, default=128, help="最大序列长度")
    args = parser.parse_args()
    
    do_export = args.export or not args.benchmark
    do_benchmark = args.benchmark or not args.export
    
    onnx_path = ONNX_OUTPUT_DIR / "model.onnx"
    
    # 导出
    if do_export:
        if not BGE_SMALL_DIR.exists():
            print(f"❌ 模型目录不存在: {BGE_SMALL_DIR}")
            print(f"   请先下载 bge-small-zh-v1.5 模型")
            sys.exit(1)
        
        onnx_path = export_to_onnx(BGE_SMALL_DIR, ONNX_OUTPUT_DIR, args.max_length)
        
        if args.optimize:
            onnx_path = optimize_onnx(onnx_path)
    
    # 基准测试
    if do_benchmark:
        if not onnx_path.exists():
            print(f"❌ ONNX 模型不存在: {onnx_path}")
            print(f"   请先运行导出: python3 {__file__} --export")
            sys.exit(1)
        
        if not BGE_SMALL_DIR.exists():
            print(f"❌ 模型目录不存在: {BGE_SMALL_DIR}")
            sys.exit(1)
        
        print(f"\n{'='*60}")
        print(f"  BGE-small-zh-v1.5 推理性能基准")
        print(f"{'='*60}")
        
        results = run_benchmark(
            model_dir=BGE_SMALL_DIR,
            onnx_path=onnx_path,
            sentences=TEST_SENTENCES,
            batch_sizes=[1, 4, 16],
        )
        
        # 保存结果
        import json
        result_path = ONNX_OUTPUT_DIR / "benchmark_results.json"
        # Convert numpy types for JSON serialization
        def convert(obj):
            if isinstance(obj, (np.float32, np.float64)):
                return float(obj)
            if isinstance(obj, (np.int32, np.int64)):
                return int(obj)
            return obj
        
        serializable = json.loads(json.dumps(results, default=convert))
        with open(result_path, "w") as f:
            json.dump(serializable, f, indent=2)
        print(f"\n📄 结果保存: {result_path}")
    
    print(f"\n✅ 完成")


if __name__ == "__main__":
    main()
