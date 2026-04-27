# ============================================================
# Standby API 网关 — Dockerfile (Rust)
# ============================================================
# 构建上下文: 项目根目录

# 构建阶段
FROM rust:slim AS builder

WORKDIR /app

# 安装 protobuf 编译器 - 使用阿里云镜像源
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources && \
    apt-get update && apt-get install -y protobuf-compiler && rm -rf /var/lib/apt/lists/*

# 复制依赖文件 (利用 Docker 缓存)
COPY src/gateway/Cargo.toml src/gateway/Cargo.lock* ./
RUN mkdir src && echo "fn main() {}" > src/main.rs
RUN cargo build --release || true
RUN rm -rf src

# 复制 cargo 配置 (cache bust: 2026-04-15-v2)
ARG CACHE_BUST=0
COPY src/gateway/.cargo/ .cargo/

# 复制源代码和 proto 文件
# build.rs 用 "../proto" 引用 proto, 从 /app/ 看就是 /proto
COPY src/proto/ /proto/
COPY src/gateway/src/ src/
COPY src/gateway/build.rs ./

# 构建
RUN cargo build --release

# 运行阶段
FROM debian:bookworm-slim

RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources && \
    apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    wget \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 从构建阶段复制二进制
COPY --from=builder /app/target/release/standby-gateway /app/standby-gateway

# 默认配置
ENV GATEWAY_PORT=8080
ENV RUST_LOG=standby_gateway=info,tower_http=info

EXPOSE 8080

HEALTHCHECK --interval=10s --timeout=5s --retries=3 \
    CMD wget -q --spider http://localhost:8080/health || exit 1

CMD ["/app/standby-gateway"]
