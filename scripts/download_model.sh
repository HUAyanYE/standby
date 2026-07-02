#!/bin/bash
export HF_ENDPOINT=https://hf-mirror.com
pip3 install sentence-transformers -i https://pypi.tuna.tsinghua.edu.cn/simple
python3 -c "
import os
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
from sentence_transformers import SentenceTransformer
m = SentenceTransformer('BAAI/bge-base-zh-v1.5', cache_folder='/mnt/d/LocalRepository/standby/engines/shared/models')
print('Model downloaded, dimension:', m.get_sentence_embedding_dimension())
"
