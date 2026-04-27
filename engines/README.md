# Standby AI Engines

五个 AI 引擎的技术实现 — 通过 gRPC 提供服务，NATS 进行异步通信。

## 引擎列表

| 引擎 | 目录 | 端口 | 职责 |
|------|------|------|------|
| Anchor Engine | `anchor_engine/` | :8090 | 锚点管理、质量评估、季节性重播 |
| Resonance Engine | `resonance_engine/` | :8091 | 共鸣值计算、关系分数 |
| Governance Engine | `governance_engine/` | :8092 | 内容治理、异常检测、信用评估 |
| User Engine | `user_engine/` | :8093 | 信任等级、匿名身份、知己关系 |
| Context Engine | `context_engine/` | :8094 | 情境感知、话题权重 |

## 目录结构

```
engines/
├── anchor_engine/           # 锚点引擎 (service.py + anchor_replay*.py)
├── resonance_engine/        # 共鸣引擎 (service.py + resonance_calculator*.py)
├── governance_engine/       # 治理引擎 (service.py + rule_governance*.py)
├── user_engine/             # 用户引擎 (service.py + user_manager.py)
├── context_engine/          # 情境引擎 (service.py)
├── shared/                  # 共享基础设施
│   ├── db.py                # PostgreSQL + MongoDB 连接
│   ├── engine_base.py       # 引擎基类
│   ├── nats_client.py       # NATS 客户端
│   └── encoders/text_encoder.py  # BGE 文本编码器
├── config/engines.yaml      # 引擎配置
├── tests/                   # 单元测试 (51 个, 全部通过)
├── validation/              # 技术验证脚本
└── requirements.txt         # Python 依赖
```

## 测试

```bash
cd engines
python3 -m pytest tests/ -v    # 51 passed ✅
```

## 配置

引擎参数在 `config/engines.yaml` 中集中管理，支持热切换算法实现。

## 共享模块

- **db.py**: PostgreSQL (psycopg2) + MongoDB (pymongo) 连接管理，自动重连
- **engine_base.py**: gRPC 引擎基类，提供生命周期管理、健康检查、日志
- **nats_client.py**: NATS JetStream 客户端，支持事件优先级和流配置
- **text_encoder.py**: BGE 文本编码器，支持云端 (768d) 和端侧 (512d) 模式
