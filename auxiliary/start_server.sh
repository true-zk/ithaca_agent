#!/bin/bash

# Ithaca Local Server Startup Script
echo "🚀 Starting Ithaca Local Policy Server..."
echo "📍 Server will run on: http://localhost:8001"
echo ""

# 检查Python是否可用
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found. Please install Python3."
    exit 1
fi

# 进入项目目录
cd "$(dirname "$0")/.."

# 启动服务器
echo "🔄 Starting server..."
python3 auxiliary/localserver.py
