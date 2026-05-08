#!/bin/bash

# 质量可视化平台启动脚本

echo "🚀 启动质量可视化平台..."
echo ""

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ 未找到Python3，请先安装Python3"
    exit 1
fi

# 检查依赖
if ! python3 -c "import streamlit" 2>/dev/null; then
    echo "📦 安装依赖..."
    pip3 install -r requirements.txt
fi

# 启动应用
echo "🌐 正在启动服务..."
echo "   浏览器将自动打开 http://localhost:8501"
echo ""

streamlit run main.py --server.port=8501 --server.address=localhost
