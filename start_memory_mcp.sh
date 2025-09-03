#!/bin/bash

# 启动Memory MCP服务器
echo "启动Memory MCP服务器..."

# 获取当前目录
CURRENT_DIR=$(pwd)

# 激活虚拟环境（如果使用虚拟环境）
if [ -d ".venv" ]; then
    echo "激活虚拟环境..."
    source .venv/bin/activate
fi

# 启动Memory MCP服务器
python memory_mcp_server.py