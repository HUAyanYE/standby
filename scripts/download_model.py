from sentence_transformers import SentenceTransformer
import os

model_name = "BAAI/bge-base-zh-v1.5"
cache_dir = "/models"

print(f"Downloading model {model_name}...")
m = SentenceTransformer(model_name, cache_folder=cache_dir)
print(f"Model downloaded. Dimension: {m.get_sentence_embedding_dimension()}")
