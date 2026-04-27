#!/bin/bash
# ============================================================
# Standby 后端 — 快速启动脚本
# ============================================================
# 用法: ./start.sh [dev|prod]
# ============================================================

set -e

MODE="${1:-dev}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 颜色
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info() { echo -e "${GREEN}[standby]${NC} $1"; }
warn() { echo -e "${YELLOW}[standby]${NC} $1"; }

cd "${SCRIPT_DIR}"

# 检查 Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装"
    exit 1
fi

if ! docker compose version &> /dev/null 2>&1; then
    if ! command -v docker-compose &> /dev/null; then
        echo "❌ Docker Compose 未安装"
        exit 1
    fi
    COMPOSE_CMD="docker-compose"
else
    COMPOSE_CMD="docker compose"
fi

# 环境文件
if [ ! -f .env ]; then
    info "创建 .env 文件..."
    cp .env.example .env
    warn "请编辑 .env 文件配置实际参数"
fi

case "${MODE}" in
    dev)
        info "启动开发环境..."
        info "启动基础服务 (PostgreSQL, MongoDB, Dragonfly, NATS)..."
        ${COMPOSE_CMD} up -d postgres mongodb dragonfly nats
        
        info "等待基础服务就绪..."
        sleep 5
        
        info "启动 AI 引擎..."
        ${COMPOSE_CMD} up -d resonance-engine anchor-engine governance-engine
        
        info "启动 API 网关..."
        ${COMPOSE_CMD} up -d api-gateway
        
        info ""
        info "✅ 开发环境已启动！"
        info ""
        info "服务地址:"
        info "  API 网关:      http://localhost:8080"
        info "  健康检查:      http://localhost:8080/health"
        info "  PostgreSQL:    localhost:5432"
        info "  MongoDB:       localhost:27017"
        info "  Dragonfly:     localhost:6379"
        info "  NATS:          localhost:4222 (监控: http://localhost:8222)"
        info ""
        info "查看日志: ${COMPOSE_CMD} logs -f"
        info "停止服务: ${COMPOSE_CMD} down"
        ;;
    
    prod)
        warn "生产模式尚未配置, 请使用 dev 模式"
        exit 1
        ;;
    
    stop)
        info "停止所有服务..."
        ${COMPOSE_CMD} down
        info "✅ 已停止"
        ;;
    
    status)
        ${COMPOSE_CMD} ps
        ;;
    
    logs)
        ${COMPOSE_CMD} logs -f "${@:2}"
        ;;
    
    *)
        echo "用法: $0 [dev|stop|status|logs]"
        exit 1
        ;;
esac
