# 🌌 Standby / 心物

> **在 AI 时代，一切都可伪造，唯有共鸣无法伪造。**

![Flutter](https://img.shields.io/badge/Flutter-3.x-02569B?logo=flutter)
![Rust](https://img.shields.io/badge/Rust-1.75+-000000?logo=rust)
![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python)
![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)

---

## 一句话定位

**人 → 事物 → 感受 → 人** — 别的产品是「人→内容→人」，Standby 多了一个「心物」，一切都不一样了。

## 它是什么

- AI 可以写一首关于孤独的诗，但它不会真的孤独——**你的感受是不可伪造的**
- Standby 不是社交平台、不是内容平台、不是通讯工具
- 它是**让人重新敢于表达真实自我的安全空间**
- 通过「心物」表达感受，通过「共鸣」发现知己
- 关系不是添加的，是自然涌现的

---

## 技术栈

| 层 | 技术 |
|---|------|
| 客户端 UI | Flutter (Dart) |
| 客户端核心 | Rust（端侧推理、安全、加密） |
| API 网关 | Rust (Axum) |
| AI 引擎 | Python (gRPC + NATS) |
| 数据库 | PostgreSQL + pgvector |
| 缓存 & 消息 | Dragonfly / NATS JetStream |
| 对象存储 | MinIO |

---

## 快速开始

```bash
# 克隆仓库
git clone git@github.com:HUAyanYE/standby.git
cd standby

# 启动后端服务
./start.sh dev

# 启动客户端
cd standby_app && flutter run
```

| 服务 | 地址 |
|------|------|
| API 网关 | `http://localhost:8080` (待实现) |
| PostgreSQL | `localhost:5432` |
| Dragonfly | `localhost:6379` |
| NATS | `localhost:4222` |
| MinIO | `http://localhost:9000` |

---

## 项目结构

```
standby/
├── src/
│   └── engines-rust/      # Rust 引擎算法库（shared / resonance / governance / anchor_replay）
├── engines/               # Python AI 引擎微服务（anchor / resonance / governance / context）
├── standby_app/           # Flutter 客户端
├── docs/                  # 产品文档（理念 / PRD / 架构 / Flutter设计 / 加密设计）
├── research/              # 探索性研究
└── docker-compose.yml
```

---

## 文档

| # | 文档 | 内容 |
|---|------|------|
| 1 | [产品理念说明书](docs/1-产品理念说明书.md) | 核心理念与产品定位 |
| 2 | [PRD 文档](docs/2-PRD文档.md) | 产品需求文档 |
| 3 | [技术架构指南](docs/3-技术架构指南.md) | 技术选型与架构设计 |
| 4 | [Flutter 设计方案](docs/4-Flutter设计方案.md) | 客户端设计方案 |

> 详细文档见 [`docs/`](docs/) 目录。

---

## 安全设计

Standby 的安全不是"加了一层防护"，而是**让攻击在架构层面就难以组织**。用户身份与表达内容完全解耦——采用匿名身份 + 设备指纹绑定，服务端无法关联用户与内容（盲服务器架构）。通信全程端到端加密，关系通过共鸣自然涌现而非主动添加。这套设计的核心思想是：隐私不是靠承诺保护的，是靠架构保证的。

---

## License

[MIT](LICENSE)

---

<div align="center">
Made with ❤️ by Standby Team
</div>
