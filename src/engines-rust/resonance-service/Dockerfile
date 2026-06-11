# ============================================================
# Standby Resonance Rust Service — 多阶段构建
# ============================================================

# Stage 1: 构建
FROM rust:1.88-slim as builder

WORKDIR /app

# 复制整个 workspace
COPY src/engines-rust/ src/engines-rust/

# 构建
RUN cd src/engines-rust && cargo build --release -p standby-resonance-service

# Stage 2: 运行
FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y ca-certificates curl && rm -rf /var/lib/apt/lists/*

COPY --from=builder /app/src/engines-rust/target/release/standby-resonance-service /usr/local/bin/

EXPOSE 8095

CMD ["standby-resonance-service"]
