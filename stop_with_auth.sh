#!/bin/bash

echo "🛑 停止带用户认证的AI求职助手系统"
echo "========================================"

# 停止认证服务器
if [ -f ".auth.pid" ]; then
    AUTH_PID=$(cat .auth.pid)
    if kill -0 $AUTH_PID 2>/dev/null; then
        echo "🔐 停止用户认证服务器..."
        kill $AUTH_PID
        rm .auth.pid
    fi
fi

# 停止静态文件服务器
if [ -f ".static.pid" ]; then
    STATIC_PID=$(cat .static.pid)
    if kill -0 $STATIC_PID 2>/dev/null; then
        echo "🌐 停止静态文件服务器..."
        kill $STATIC_PID
        rm .static.pid
    fi
fi

# 停止前端服务器
if [ -f ".frontend.pid" ]; then
    FRONTEND_PID=$(cat .frontend.pid)
    if kill -0 $FRONTEND_PID 2>/dev/null; then
        echo "🎨 停止前端服务器..."
        kill $FRONTEND_PID
        rm .frontend.pid
    fi
fi

# 停止后端服务器
if [ -f "NeMo-Agent-Toolkit/.backend.pid" ]; then
    BACKEND_PID=$(cat NeMo-Agent-Toolkit/.backend.pid)
    if kill -0 $BACKEND_PID 2>/dev/null; then
        echo "📡 停止后端AI服务器..."
        kill $BACKEND_PID
        rm NeMo-Agent-Toolkit/.backend.pid
    fi
fi

# 停止Memory MCP服务器
echo "🧠 停止Memory MCP服务器..."
pkill -f "memory_mcp_server.py" 2>/dev/null || true

# 停止Tavily MCP服务器
echo "🔍 停止Tavily MCP服务器..."
pkill -f "tavily_mcp_server.py" 2>/dev/null || true

# 清理其他可能的进程
echo "🧹 清理其他相关进程..."
pkill -f "aiq serve" 2>/dev/null || true
pkill -f "npm run dev" 2>/dev/null || true
pkill -f "python -m http.server" 2>/dev/null || true

echo "✅ 所有服务已停止"