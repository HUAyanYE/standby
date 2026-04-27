#!/bin/bash
# ============================================================
# Protobuf 代码生成脚本
# ============================================================
# 用法: ./generate.sh [language]
# 支持: go, rust, python, all
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROTO_DIR="${SCRIPT_DIR}"
OUTPUT_DIR="${SCRIPT_DIR}/generated"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() { echo -e "${GREEN}[proto-gen]${NC} $1"; }
warn() { echo -e "${YELLOW}[proto-gen]${NC} $1"; }
err() { echo -e "${RED}[proto-gen]${NC} $1"; }

# 检查依赖
check_deps() {
    if ! command -v protoc &> /dev/null; then
        err "protoc 未安装。请安装 Protocol Buffers 编译器。"
        exit 1
    fi
    log "protoc 版本: $(protoc --version)"
}

# 清理输出目录
clean_output() {
    rm -rf "${OUTPUT_DIR}"
    mkdir -p "${OUTPUT_DIR}"/{go,rust,python}
}

# Go 代码生成
gen_go() {
    log "生成 Go 代码..."
    
    if ! command -v protoc-gen-go &> /dev/null; then
        warn "protoc-gen-go 未安装，跳过 Go 生成"
        warn "安装: go install google.golang.org/protobuf/cmd/protoc-gen-go@latest"
        warn "       go install google.golang.org/grpc/cmd/protoc-gen-go-grpc@latest"
        return
    fi
    
    mkdir -p "${OUTPUT_DIR}/go"
    
    protoc \
        --proto_path="${PROTO_DIR}" \
        --go_out="${OUTPUT_DIR}/go" \
        --go_opt=paths=source_relative \
        --go-grpc_out="${OUTPUT_DIR}/go" \
        --go-grpc_opt=paths=source_relative \
        common/common.proto \
        gateway/gateway.proto \
        engines/engines.proto \
        nats/events.proto
    
    log "Go 代码生成完成 → ${OUTPUT_DIR}/go/"
}

# Rust 代码生成
gen_rust() {
    log "生成 Rust 代码..."
    
    if ! command -v protoc-gen-prost &> /dev/null; then
        warn "protoc-gen-prost 未安装，跳过 Rust 生成"
        warn "安装: cargo install protoc-gen-prost"
        return
    fi
    
    mkdir -p "${OUTPUT_DIR}/rust/src"
    
    protoc \
        --proto_path="${PROTO_DIR}" \
        --prost_out="${OUTPUT_DIR}/rust/src" \
        common/common.proto \
        gateway/gateway.proto \
        engines/engines.proto \
        nats/events.proto
    
    log "Rust 代码生成完成 → ${OUTPUT_DIR}/rust/src/"
}

# Python 代码生成
gen_python() {
    log "生成 Python 代码..."
    
    mkdir -p "${OUTPUT_DIR}/python"
    
    # 生成 protobuf 消息类
    protoc \
        --proto_path="${PROTO_DIR}" \
        --python_out="${OUTPUT_DIR}/python" \
        common/common.proto \
        gateway/gateway.proto \
        engines/engines.proto \
        nats/events.proto
    
    # 生成 gRPC 存根 (需要 grpcio-tools)
    if python3 -c "import grpc_tools" 2>/dev/null; then
        protoc \
            --proto_path="${PROTO_DIR}" \
            --python_out="${OUTPUT_DIR}/python" \
            --grpc_python_out="${OUTPUT_DIR}/python" \
            gateway/gateway.proto \
            engines/engines.proto
        log "Python gRPC 存根生成完成"
    else
        warn "grpcio-tools 未安装，跳过 Python gRPC 存根"
        warn "安装: pip install grpcio-tools"
    fi
    
    # 生成 __init__.py
    touch "${OUTPUT_DIR}/python/__init__.py"
    
    log "Python 代码生成完成 → ${OUTPUT_DIR}/python/"
}

# 主逻辑
main() {
    local lang="${1:-all}"
    
    check_deps
    clean_output
    
    case "${lang}" in
        go)
            gen_go
            ;;
        rust)
            gen_rust
            ;;
        python)
            gen_python
            ;;
        all)
            gen_go
            gen_rust
            gen_python
            ;;
        *)
            err "不支持的语言: ${lang}"
            echo "用法: $0 [go|rust|python|all]"
            exit 1
            ;;
    esac
    
    log "生成完成！输出目录: ${OUTPUT_DIR}"
    echo ""
    echo "目录结构:"
    tree "${OUTPUT_DIR}" 2>/dev/null || find "${OUTPUT_DIR}" -type f | sort
}

main "$@"
