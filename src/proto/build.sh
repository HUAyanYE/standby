#!/bin/bash
# ============================================================
# Standby — Protobuf 代码生成脚本
# ============================================================
# 用法: ./src/proto/build.sh [python|rust|all]
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
PROTO_DIR="${SCRIPT_DIR}"
PYTHON_OUT="${SCRIPT_DIR}/generated/python"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info() { echo -e "${GREEN}[proto]${NC} $1"; }
warn() { echo -e "${YELLOW}[proto]${NC} $1"; }

TARGET="${1:-all}"

# ============================================================
# Python 生成
# ============================================================
generate_python() {
    info "生成 Python protobuf/gRPC stubs..."

    # 检查工具
    if ! command -v python3 &> /dev/null; then
        warn "python3 未安装，跳过 Python 生成"
        return
    fi

    # 检查 grpcio-tools
    if ! python3 -m grpc_tools.protoc --version &> /dev/null 2>&1; then
        warn "grpcio-tools 未安装，使用手工维护的 stubs"
        warn "安装: pip install grpcio-tools"
        info "当前 stubs 位于: ${PYTHON_OUT}/"
        return
    fi

    mkdir -p "${PYTHON_OUT}"

    # 生成 Python stubs
    python3 -m grpc_tools.protoc \
        -I="${PROTO_DIR}" \
        --python_out="${PYTHON_OUT}" \
        --grpc_python_out="${PYTHON_OUT}" \
        "${PROTO_DIR}/common.proto" \
        "${PROTO_DIR}/engines.proto"

    info "✅ Python stubs 已生成到 ${PYTHON_OUT}/"
}

# ============================================================
# Rust 生成
# ============================================================
generate_rust() {
    info "生成 Rust protobuf/gRPC stubs..."

    # 检查工具
    if ! command -v protoc &> /dev/null; then
        warn "protoc 未安装，跳过 Rust 生成"
        warn "安装: https://grpc.io/docs/protoc-installation/"
        return
    fi

    RUST_OUT="${SCRIPT_DIR}/generated/rust"
    mkdir -p "${RUST_OUT}"

    # 使用 tonic-build (如果在 Cargo 构建中)
    info "Rust stubs 通过 cargo build 时的 build.rs 自动生成"
    info "参见 src/engines-rust/resonance-service/build.rs"
}

# ============================================================
# 主逻辑
# ============================================================
case "${TARGET}" in
    python)
        generate_python
        ;;
    rust)
        generate_rust
        ;;
    all)
        generate_python
        generate_rust
        ;;
    *)
        echo "用法: $0 [python|rust|all]"
        exit 1
        ;;
esac

info "完成!"
