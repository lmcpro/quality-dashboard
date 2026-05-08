#!/bin/bash
# 本地部署脚本

set -e

echo "🚀 质量可视化平台部署脚本"
echo "============================"

# 检查 Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装，请先安装 Docker"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose 未安装，请先安装 Docker Compose"
    exit 1
fi

# 显示版本信息
echo ""
echo "📋 版本信息:"
if [ -f version.txt ]; then
    cat version.txt
else
    echo "分支: $(git branch --show-current 2>/dev/null || echo 'unknown')"
    echo "提交: $(git rev-parse --short HEAD 2>/dev/null || echo 'unknown')"
fi

# 构建并启动
echo ""
echo "🔨 构建 Docker 镜像..."
docker-compose build

echo ""
echo "▶️  启动服务..."
docker-compose up -d

echo ""
echo "✅ 部署完成！"
echo ""
echo "📊 服务地址:"
echo "  - Streamlit: http://localhost:8501"
echo ""
echo "📝 常用命令:"
echo "  - 查看日志: docker-compose logs -f"
echo "  - 停止服务: docker-compose down"
echo "  - 重启服务: docker-compose restart"
echo "  - 更新代码: git pull && docker-compose up -d --build"
