# API 网关实现计划 — 生产级设计

## Context

项目需要一个 Rust/Axum API 网关作为系统的统一 HTTP 入口。网关暴露 REST/JSON API 给 Flutter 客户端，内部通过 gRPC 调用 4 个 Python 引擎。安全要求：JWT + 设备指纹绑定、速率限制、证书固定。

当前状态：网关完全缺失（旧代码已删），Python 引擎使用轻量级 stubs（无真实 protobuf 序列化），proto 定义文件已就绪。

---

## 架构设计

```
Flutter App (Dio HTTP)
    │
    │  HTTPS + JWT + 设备指纹签名
    ▼
┌─────────────────────────────────────────┐
│  API Gateway (Rust/Axum :8080)          │
│                                         │
│  Middleware 栈 (从外到内):                │
│  1. TLS 终止                            │
│  2. 请求日志 (tracing)                  │
│  3. 速率限制 (per-device)               │
│  4. 设备认证 (X-Device-Id + 签名)       │
│  5. JWT 验证                            │
│  6. 请求体校验                           │
│                                         │
│  路由层:                                 │
│  /api/v1/anchors/*     → AnchorEngine   │
│  /api/v1/reactions/*   → ResonanceEngine│
│  /api/v1/governance/*  → GovernanceEngine│
│  /api/v1/context/*     → ContextEngine  │
│  /api/v1/auth/*        → 本地认证逻辑    │
│  /health               → 健康检查       │
│                                         │
│  Engine Clients (tonic gRPC):           │
│  ├── anchor:8090                        │
│  ├── resonance:8091                     │
│  ├── governance:8092                    │
│  └── context:8094                       │
└─────────────────────────────────────────┘
```

---

## 文件结构

```
src/gateway/
├── Cargo.toml
├── Dockerfile
├── build.rs                    # protobuf 代码生成
├── src/
│   ├── main.rs                 # 入口: 初始化 + 启动
│   ├── config.rs               # 配置加载 (环境变量)
│   ├── error.rs                # 统一错误类型
│   ├── proto/
│   │   └── mod.rs              # include!(generated protobuf)
│   ├── engine_clients/
│   │   ├── mod.rs              # EngineClients 聚合
│   │   ├── anchor.rs           # AnchorEngine gRPC client wrapper
│   │   ├── resonance.rs        # ResonanceEngine gRPC client wrapper
│   │   ├── governance.rs       # GovernanceEngine gRPC client wrapper
│   │   └── context.rs          # ContextEngine gRPC client wrapper
│   ├── middleware/
│   │   ├── mod.rs
│   │   ├── device_auth.rs      # 设备指纹认证
│   │   ├── jwt.rs              # JWT 验证
│   │   ├── rate_limit.rs       # 速率限制
│   │   └── request_log.rs      # 请求日志
│   ├── routes/
│   │   ├── mod.rs              # 路由注册
│   │   ├── health.rs           # /health
│   │   ├── auth.rs             # /api/v1/auth/*
│   │   ├── anchors.rs          # /api/v1/anchors/*
│   │   ├── reactions.rs        # /api/v1/reactions/*
│   │   ├── governance.rs       # /api/v1/governance/*
│   │   └── context.rs          # /api/v1/context/*
│   └── models/
│       ├── mod.rs
│       ├── auth.rs             # JWT claims, 登录请求/响应
│       ├── anchor.rs           # REST 锚点模型
│       ├── reaction.rs         # REST 反应模型
│       ├── governance.rs       # REST 治理模型
│       └── context.rs          # REST 情境模型
```

---

## 实现步骤

### Step 1: 项目骨架 + Cargo.toml + build.rs

**Cargo.toml 依赖:**
- `axum` 0.7 — HTTP 框架
- `tokio` 1 — 异步运行时
- `tonic` 0.12 — gRPC 客户端
- `prost` 0.13 — protobuf 序列化
- `serde` + `serde_json` — JSON 序列化
- `jsonwebtoken` 9 — JWT 签发/验证
- `tower` + `tower-http` — 中间件 (cors, trace, timeout)
- `tracing` + `tracing-subscriber` — 日志
- `uuid` — 请求 ID
- `dashmap` — 并发速率限制存储
- `chrono` — 时间处理
- `hmac` + `sha2` — 请求签名验证
- `thiserror` — 错误类型

**build.rs:** 使用 tonic-build 从 `src/proto/engines.proto` 和 `src/proto/common.proto` 生成 Rust gRPC 客户端代码。

### Step 2: 配置 + 错误类型

**config.rs:** 从环境变量加载配置
- `GATEWAY_PORT` (默认 8080)
- `JWT_SECRET` (必须)
- `JWT_EXPIRY_HOURS` (默认 24)
- `ENGINE_ANCHOR_URL` (默认 http://localhost:8090)
- `ENGINE_RESONANCE_URL` (默认 http://localhost:8091)
- `ENGINE_GOVERNANCE_URL` (默认 http://localhost:8092)
- `ENGINE_CONTEXT_URL` (默认 http://localhost:8094)
- `RATE_LIMIT_PER_MINUTE` (默认 60)
- `DEVICE_SIGNATURE_HEADER` (默认 X-Device-Signature)
- `DEVICE_ID_HEADER` (默认 X-Device-Id)

**error.rs:** 统一 API 错误响应格式
```json
{ "error": { "code": "UNAUTHORIZED", "message": "..." } }
```

### Step 3: Engine Clients (gRPC 客户端封装)

每个引擎一个模块，封装 tonic channel + 方法调用。

**关键设计:**
- `EngineClients` 结构体聚合所有 4 个客户端
- 使用 `tonic::transport::Channel` 连接池
- 每个方法接受 Rust 结构体，内部转为 protobuf 请求
- 返回值从 protobuf 响应转为 Rust 结构体
- 连接重试 + 超时处理

### Step 4: 中间件层

**device_auth.rs:**
- 从 `X-Device-Id` 头提取设备 ID
- 从 `X-Device-Signature` 头提取签名
- 签名算法: HMAC-SHA256(device_secret, method + path + timestamp + body_hash)
- device_secret 从 JWT 登录时绑定，后续请求携带
- 时间戳窗口: ±5 分钟防重放
- 拒绝: 无有效设备认证 → 401

**jwt.rs:**
- 从 `Authorization: Bearer <token>` 提取 JWT
- 验证签名 + 过期时间
- Claims 包含: sub(user_id), device_id, iat, exp
- 白名单路由: /health, /api/v1/auth/login, /api/v1/auth/register
- 拒绝: 无效/过期 JWT → 401

**rate_limit.rs:**
- 基于 device_id 的滑动窗口速率限制
- 使用 DashMap 存储 per-device 计数器
- 默认 60 请求/分钟
- 超限返回 429 + Retry-After 头

**request_log.rs:**
- 记录: 请求 ID、方法、路径、状态码、耗时、设备 ID
- 使用 tracing 结构化日志

### Step 5: 路由 + Handler

**REST API 设计:**

```
POST   /api/v1/auth/register         → 注册 (设备指纹 → JWT)
POST   /api/v1/auth/login            → 登录 (设备指纹 → JWT)
POST   /api/v1/auth/refresh          → 刷新 token

POST   /api/v1/anchors               → GenerateAnchor
GET    /api/v1/anchors                → ListAnchors
GET    /api/v1/anchors/:id            → GetAnchorMetadata
GET    /api/v1/anchors/:id/vector     → GetAnchorVector
POST   /api/v1/anchors/:id/evaluate   → EvaluateAnchorQuality
GET    /api/v1/anchors/:id/memory     → GetGroupMemory
GET    /api/v1/anchors/:id/chain      → GetFeelingChain

POST   /api/v1/reactions              → ProcessReaction
POST   /api/v1/reactions/batch        → ProcessBatch
GET    /api/v1/reactions              → ListReactions
GET    /api/v1/reactions/distribution/:anchor_id → GetReactionDistribution

GET    /api/v1/relationships/:user_id → FindResonancePairs
GET    /api/v1/relationships/score    → GetRelationshipScore (query: user_a, user_b)

POST   /api/v1/governance/evaluate    → EvaluateContent
POST   /api/v1/governance/anomaly     → DetectAnomaly
GET    /api/v1/governance/credibility/:marker_hash → CheckMarkCredibility

POST   /api/v1/context                → SubmitContextState
GET    /api/v1/context/weights        → GetContextualWeights

POST   /api/v1/encode                 → EncodeText
```

**auth.rs handler:**
- register: 验证设备指纹 → 写入 users 表 → 签发 JWT + device_secret
- login: 验证设备指纹 → 查询 users 表 → 签发 JWT
- refresh: 验证当前 JWT → 签发新 JWT

### Step 6: Python 引擎 protobuf 修复

使用 grpcio-tools 重新生成 Python protobuf stubs，替换当前的轻量级实现。
- 安装 grpcio-tools 到 requirements.txt
- 运行 protoc 生成 engines_pb2.py 和 engines_pb2_grpc.py
- 确保引擎的 gRPC 服务器能正确序列化/反序列化

### Step 7: Dockerfile + docker-compose 集成

**Dockerfile:**
```dockerfile
FROM rust:1.75-slim as builder
WORKDIR /app
COPY . .
RUN cargo build --release -p standby-gateway

FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y ca-certificates && rm -rf /var/lib/apt/lists/*
COPY --from=builder /app/target/release/standby-gateway /usr/local/bin/
EXPOSE 8080
CMD ["standby-gateway"]
```

**docker-compose.yml:** 取消注释 api-gateway，更新环境变量。

---

## 关键文件清单

| 文件 | 操作 | 说明 |
|------|------|------|
| `src/gateway/Cargo.toml` | 新建 | 项目依赖 |
| `src/gateway/build.rs` | 新建 | protobuf 代码生成 |
| `src/gateway/src/main.rs` | 新建 | 入口 |
| `src/gateway/src/config.rs` | 新建 | 配置 |
| `src/gateway/src/error.rs` | 新建 | 错误类型 |
| `src/gateway/src/proto/mod.rs` | 新建 | protobuf 生成代码引用 |
| `src/gateway/src/engine_clients/*.rs` | 新建 | 4 个 gRPC 客户端封装 |
| `src/gateway/src/middleware/*.rs` | 新建 | 4 个中间件 |
| `src/gateway/src/routes/*.rs` | 新建 | 6 个路由模块 |
| `src/gateway/src/models/*.rs` | 新建 | REST 模型 |
| `src/gateway/Dockerfile` | 新建 | Docker 镜像 |
| `docker-compose.yml` | 修改 | 取消注释 + 更新配置 |
| `.env.example` | 修改 | 添加网关环境变量 |
| `src/engines-rust/Cargo.toml` | 修改 | 添加 gateway workspace member |
| `engines/requirements.txt` | 修改 | 添加 grpcio-tools |

---

## 验证方式

1. `cargo build -p standby-gateway` — 编译通过
2. `docker compose up api-gateway` — 容器启动
3. `curl http://localhost:8080/health` — 健康检查返回 200
4. `curl -X POST http://localhost:8080/api/v1/auth/register -d '{"device_fingerprint":"test"}'` — 获取 JWT
5. `curl -H "Authorization: Bearer <jwt>" http://localhost:8080/api/v1/anchors` — 带认证访问
6. `curl http://localhost:8080/api/v1/anchors` — 无认证返回 401
