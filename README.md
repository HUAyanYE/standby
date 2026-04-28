# 🌌 Standby / 心物

> **在 AI 时代，一切都可伪造，唯有共鸣无法伪造。**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Flutter](https://img.shields.io/badge/Flutter-3.x-02569B?logo=flutter)](https://flutter.dev)
[![Rust](https://img.shields.io/badge/Rust-1.75+-000000?logo=rust)](https://www.rust-lang.org)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python)](https://www.python.org)

---

## ✨ 产品理念

**AI 可以写一首关于孤独的诗，但它不会真的孤独。**

Standby 不是社交平台、不是内容平台、不是通讯工具——它是**让人重新敢于表达真实自我的安全空间**。

| 平台 | 核心问题 | 优化目标 |
|------|---------|---------|
| 微信 | 你认识谁 | 关系维护 |
| 抖音 | 你看什么内容 | 参与度 |
| 小红书 | 你想成为什么样的人 | 生活方式 |
| **Standby** | **你感受到了什么** | **共鸣** |

**核心路径：** 人 → 事物 → 感受 → 人（多了一个「心物」，一切都不一样了）

---

## 🏗️ 技术架构

```
┌─────────────────────────────────────────────────────────────┐
│                       客户端层                                │
│  Flutter (Dart) ←→ flutter_rust_bridge ←→ Rust 核心层       │
│  UI渲染/交互     FFI桥接                 端侧推理/安全/加密    │
├─────────────────────────────────────────────────────────────┤
│                       后端服务层                              │
│  Rust API Gateway ←→ Python AI Engines (gRPC + NATS)        │
├─────────────────────────────────────────────────────────────┤
│                       数据层                                  │
│  PostgreSQL + pgvector │ Qdrant │ Dragonfly │ MinIO          │
└─────────────────────────────────────────────────────────────┘
```

### 技术栈

| 层 | 技术 |
|---|------|
| 客户端 UI | Flutter (Dart) |
| 客户端核心 | Rust（端侧推理、安全、加密） |
| API 网关 | Rust (Axum) |
| AI 引擎 | Python (gRPC + NATS) |
| 主数据库 | PostgreSQL + pgvector |
| 向量数据库 | Qdrant |
| 缓存 | Dragonfly (Redis 兼容) |
| 消息总线 | NATS JetStream |
| 对象存储 | MinIO |

---

## 🧠 AI 引擎

| 引擎 | 端口 | 职责 |
|------|------|------|
| **Anchor Engine** | :8090 | 锚点管理、质量评估、季节性重播 |
| **Resonance Engine** | :8091 | 共鸣值计算、关系分数 |
| **Governance Engine** | :8092 | 内容治理、异常检测、信用评估 |
| **User Engine** | :8093 | 信任等级、匿名身份、知己关系 |
| **Context Engine** | :8094 | 情境感知、话题权重 |

---

## 📁 项目结构

```
standby/
├── src/
│   ├── gateway/           # Rust API 网关
│   ├── proto/             # Protobuf 定义
│   └── client/            # Rust 客户端库
├── engines/               # Python AI 引擎
│   ├── anchor_engine/     # 锚点引擎
│   ├── resonance_engine/  # 共鸣引擎
│   ├── governance_engine/ # 治理引擎
│   ├── user_engine/       # 用户引擎
│   ├── context_engine/    # 情境引擎
│   └── shared/            # 共享基础设施
├── engines-rust/          # Rust 引擎实现
├── standby_app/           # Flutter 客户端
├── docs/                  # 产品文档
├── scripts/               # 工具脚本
├── tests/                 # 端到端测试
└── docker-compose.yml     # 容器编排
```

---

## 🚀 快速开始

### 前置要求

- Docker & Docker Compose
- Flutter SDK（客户端开发）
- Rust toolchain（网关开发）
- Python 3.11+（引擎开发）

### 启动后端服务

```bash
# 克隆仓库
git clone git@github.com:HUAyanYE/standby.git
cd standby

# 启动开发环境
./start.sh dev

# 查看服务状态
./start.sh status

# 查看日志
./start.sh logs

# 停止服务
./start.sh stop
```

### 服务地址

| 服务 | 地址 |
|------|------|
| API 网关 | http://localhost:8080 |
| 健康检查 | http://localhost:8080/health |
| PostgreSQL | localhost:5432 |
| Qdrant | localhost:6333 |
| Dragonfly | localhost:6379 |
| NATS | localhost:4222 |
| MinIO | http://localhost:9000 |

---

## 🧪 测试

```bash
# 运行引擎单元测试
cd engines
python3 -m pytest tests/ -v

# 运行端到端测试
cd tests
python3 e2e_test.py
```

---

## 📚 文档

| 文档 | 描述 |
|------|------|
| [产品理念说明书](docs/1-产品理念说明书.md) | 核心理念与产品定位 |
| [PRD 文档](docs/2-PRD文档.md) | 产品需求文档 |
| [技术架构指南](docs/3-技术架构指南.md) | 技术选型与架构设计 |
| [Flutter 设计方案](docs/4-Flutter设计方案.md) | 客户端设计 |
| [思想融合分析](docs/5-思想融合分析.md) | 产品哲学 |
| [HANDBOOK](docs/HANDBOOK.md) | 项目手册 |

---

## 🔒 安全设计

- **完全匿名**：用户身份与内容解耦
- **设备绑定**：设备指纹 + 硬件身份
- **端到端加密**：通信全程加密
- **盲服务器**：服务端无法关联用户与内容
- **架构安全**：攻击在结构层面不可行

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

## 📄 License

MIT License

---

<div align="center">

**[产品理念](docs/1-产品理念说明书.md)** · **[技术架构](docs/3-技术架构指南.md)** · **[HANDBOOK](docs/HANDBOOK.md)**

Made with ❤️ by Standby Team

</div>
