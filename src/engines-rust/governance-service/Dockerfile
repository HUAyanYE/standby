# ============================================================
# Standby Governance Rust Service — 多阶段构建
# ============================================================

# Stage 1: 构建
FROM rust:1.75-slim as builder

WORKDIR /app

# 复制 workspace 文件
COPY src/engines-rust/Cargo.toml src/engines-rust/Cargo.lock* src/engines-rust/

# 复制源代码
COPY src/engines-rust/shared/ src/engines-rust/shared/
COPY src/engines-rust/governance/ src/engines-rust/governance/
COPY src/engines-rust/governance-service/ src/engines-rust/governance-service/

# 构建
RUN cd src/engines-rust && cargo build --release -p standby-governance-service

# Stage 2: 运行
FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y ca-certificates && rm -rf /var/lib/apt/lists/*

COPY --from=builder /app/src/engines-rust/target/release/standby-governance-service /usr/local/bin/

EXPOSE 8096

CMD ["standby-governance-service"]
