#!/bin/bash

echo "🚀 启动带用户认证的AI求职助手系统"
echo "============================================"

# 获取项目根目录
PROJECT_ROOT=$(pwd)

# 设置环境变量
export TAVILY_API_KEY=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

# 检查虚拟环境
if [ ! -d ".venv" ]; then
    echo "❌ 虚拟环境不存在，请先运行 python -m venv .venv"
    exit 1
fi

# 激活Python虚拟环境
source .venv/bin/activate

# 启动用户认证服务器
echo "🔐 启动用户认证服务器..."
python auth_server.py &
AUTH_PID=$!
echo $AUTH_PID > .auth.pid

# 等待认证服务器启动
echo "⏳ 等待认证服务器启动..."
sleep 3

# 启动Memory MCP服务器
echo "🧠 启动Memory MCP服务器..."
bash start_memory_mcp.sh &
MEMORY_PID=$!

# 等待Memory服务器启动
sleep 2

# 进入NeMo目录并启动后端服务
echo "📡 启动后端AI服务..."
cd "$PROJECT_ROOT/NeMo-Agent-Toolkit"
source .venv/bin/activate
aiq serve --config_file ../configs/hackathon_config.yml --host 0.0.0.0 --port 8001 &
BACKEND_PID=$!
echo $BACKEND_PID > .backend.pid

# 等待后端启动
echo "⏳ 等待后端AI服务启动..."
sleep 10

# 启动前端服务
echo "🎨 启动前端服务..."
cd "$PROJECT_ROOT/external/aiqtoolkit-opensource-ui"
npm run dev &
FRONTEND_PID=$!
echo $FRONTEND_PID > .frontend.pid

# 返回项目根目录
cd "$PROJECT_ROOT"

echo ""
echo "✅ 系统启动完成！"
echo ""
echo "🌐 访问地址:"
echo "   用户登录: http://localhost:8080/login.html"
echo "   用户面板: http://localhost:8080/dashboard.html"
echo "   AI对话:  http://localhost:3000"
echo "   认证API: http://localhost:8001"
echo "   后端API: http://localhost:8001/docs"
echo ""
echo "📝 使用流程:"
echo "   1. 访问登录页面注册/登录账户"
echo "   2. 登录成功后进入用户面板"
echo "   3. 点击'开始求职咨询'使用AI助手"
echo "   4. 所有对话记录将保存到您的个人记忆库"
echo ""
echo "🛑 停止服务: 按 Ctrl+C 或运行 ./stop_with_auth.sh"
echo ""

# 启动简单的HTTP服务器来提供静态文件
echo "🌐 启动静态文件服务器..."
python -m http.server 8080 &
STATIC_PID=$!
echo $STATIC_PID > .static.pid

# 等待用户中断
wait