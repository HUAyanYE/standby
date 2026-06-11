# ============================================================
# Standby API Gateway — 多阶段构建
# ============================================================

# Stage 1: 构建
FROM rust:1.88-slim as builder

WORKDIR /app

# 安装 protobuf 编译器 (tonic-build 需要)
RUN apt-get update && apt-get install -y protobuf-compiler && rm -rf /var/lib/apt/lists/*

# 复制 workspace 文件
COPY src/engines-rust/Cargo.toml src/engines-rust/Cargo.lock* src/engines-rust/
COPY src/gateway/Cargo.toml src/gateway/

# 复制源代码
COPY src/engines-rust/ src/engines-rust/
COPY src/gateway/ src/gateway/
COPY src/proto/ src/proto/

# 构建网关
RUN cd src/gateway && cargo build --release --bin standby-gateway

# Stage 2: 运行
FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y ca-certificates && rm -rf /var/lib/apt/lists/*

COPY --from=builder /app/src/gateway/target/release/standby-gateway /usr/local/bin/

EXPOSE 8080

CMD ["standby-gateway"]
