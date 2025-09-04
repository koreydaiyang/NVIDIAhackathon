# NVIDIA NeMo Agent Toolkit AI对话机器人

> 🏆 **黑客松项目** - 基于NVIDIA官方NeMo Agent Toolkit构建的智能对话机器人，展示AI Agent的强大功能

![AI对话机器人界面](docs/ui_screenshot.png)

## 🎯 项目简介

本项目是为推广NVIDIA NeMo Agent Toolkit而开发的AI对话机器人示例，完全基于NVIDIA官方技术栈构建。系统集成了实时网络搜索、时间查询等功能，支持用户自定义OpenAI兼容的API接口，是学习和体验AI Agent技术的完美起点。

### ✨ 核心特性

- 🤖 **官方架构**: 100%使用NVIDIA官方NeMo Agent Toolkit
- 🌐 **实时搜索**: 集成Tavily API，支持实时网络搜索
- ⏰ **时间查询**: 获取当前日期和时间信息
- 🔧 **灵活配置**: 支持任何OpenAI兼容的API接口
- 🎨 **现代界面**: 官方UI，支持实时对话和流式响应
- 🚀 **一键部署**: 跨平台安装脚本，支持Windows/Linux/macOS

## 🏗️ 技术架构

### 前端
- **框架**: Next.js 14 + TypeScript
- **UI库**: 官方[NeMo-Agent-Toolkit-UI](https://github.com/NVIDIA/NeMo-Agent-Toolkit-UI)
- **特性**: 实时聊天、主题切换、历史记录

### 后端
- **核心**: [NVIDIA NeMo Agent Toolkit (AIQ)](https://github.com/NVIDIA/NeMo-Agent-Toolkit/tree/develop)
- **工作流**: React Agent
- **工具**: Tavily搜索、时间查询

### 模型支持
- **默认**: Qwen模型
- **兼容**: 任何OpenAI格式的API
- **自定义**: 用户可配置API密钥、模型名称、base_url

## 🚀 快速开始

### 📋 环境要求

- **Python**: 3.12+
- **Node.js**: 18+
- **Git**: 最新版本
- **操作系统**: Windows 10+/macOS 10.15+/Ubuntu 20.04+

### ⚡ 一键安装

#### 克隆项目
```bash
git clone https://github.com/HeKun-NVIDIA/hackathon_aiqtoolkit.git
cd hackathon_aiqtoolkit
```
### 🔑 配置API密钥

安装完成后，您需要配置以下API密钥：

#### 1. Tavily搜索API密钥
在`install.sh`文件中185行左右，将Your API Key替换成你自己的Tavily API Key 来保证搜索功能正常
```bash
# 设置环境变量
export TAVILY_API_KEY=your-tavily-api-key-here
```

**获取Tavily API密钥**：
1. 访问 [Tavily官网](https://tavily.com/)
2. 注册账户并获取免费API密钥
3. 将密钥添加到环境变量中

#### 2. 大模型API密钥

编辑配置文件，将API key设置为环境变量：

```yaml
llms:
  # 默认使用Bailian API (用户可修改)
  default_llm:
    _type: openai
    model_name: "qwen-plus"
    api_key: "${BAILIAN_API_KEY}"
    base_url: "https://dashscope.aliyuncs.com/compatible-mode/v1"
    temperature: 0.7
    max_tokens: 2048
```

**支持的API提供商**：
- **阿里云百炼平台Qwen系列**: `https://bailian.console.aliyun.com/?tab=model#/model-market`
- **其他**: 任何OpenAI兼容的API

#### Linux/macOS
```bash
# 运行安装脚本
chmod +x install.sh
./install.sh
```

#### Windows
```powershell
# 运行安装脚本
install.bat
```



### 🎮 启动系统

```bash
# 启动服务
cd NeMo-Agent-Toolkit
./start.sh

# 停止服务
./stop.sh
```

### 🌐 访问地址

- **前端界面**: http://localhost:3000
- **API文档**: http://localhost:8001/docs
- **健康检查**: http://localhost:8001/health

## 🧪 功能测试

### 网络搜索测试
```
用户: 北京今天的天气怎么样，气温是多少？
AI: 今天北京天气晴朗，气温在18℃至31℃之间，当前温度约30℃，西南风3级，相对湿度43%，空气质量良好，体感温度舒适。白天最高气温可达31℃，夜间最低18℃，全天无降水，紫外线较强，建议做好防晒措施。
```

### 时间查询测试
```
用户: 现在几点了？
AI: 现在是晚上11点17分。
```

### 公司信息搜索测试
```
用户: 帮我介绍一下NVIDIA Agent Intelligence Toolkit
AI: [搜索并介绍NVIDIA AIQ工具包的详细信息]
```

## 📁 项目结构

```
nvidia-nemo-agent-toolkit-hackathon/
├── configs/                    # 配置文件
│   └── hackathon_config.yml   # 主配置文件
├── external/                   # 外部模块
│   └── aiqtoolkit-opensource-ui/  # 官方UI
├── docs/                       # 文档和截图
│   └── ui_screenshot.png      # 界面截图
├── src/                        # 源代码
├── install.sh                  # Linux/macOS安装脚本
├── install.bat                 # Windows安装脚本
├── start.sh                    # 启动脚本
├── stop.sh                     # 停止脚本
└── README.md                   # 说明文档
```

## ⚙️ 高级配置

### 自定义工具

在配置文件中添加新工具：

```yaml
functions:
  your_custom_tool:
    _type: your_tool_type
    description: "工具描述"
    # 其他配置参数
```

### 自定义工作流

```yaml
workflow:
  _type: react_agent
  tool_names:
    - internet_search
    - current_datetime
    - your_custom_tool
  llm_name: default_llm
  verbose: true
```

### 调试模式

```bash
# 启用详细日志
aiq serve --config_file configs/hackathon_config.yml --verbose
```

## 🐛 故障排除

### 常见问题

#### 1. 端口占用
```bash
# 检查端口占用
netstat -tlnp | grep :8001

# 使用不同端口
aiq serve --port 8002
```

#### 2. API密钥错误
- 检查 `configs/hackathon_config.yml` 中的API密钥配置
- 确认环境变量 `TAVILY_API_KEY` 已正确设置
- 验证API密钥的有效性和权限

#### 3. 依赖安装失败
```bash
# 清理缓存重新安装
uv cache clean
uv pip install -e . --force-reinstall
```

#### 4. 前端无法连接后端
- 检查后端是否正常启动（访问 http://localhost:8001/health）
- 确认端口配置正确
- 检查防火墙设置

### 日志查看

```bash
# 查看后端日志
tail -f logs/aiq.log

# 查看前端日志
cd external/aiqtoolkit-opensource-ui
npm run dev -- --verbose
```

## 📚 相关资源

### 官方文档
- [NVIDIA NeMo Agent Toolkit](https://github.com/NVIDIA/NeMo-Agent-Toolkit)
- [官方文档](https://docs.nvidia.com/nemo-agent-toolkit/)
- [NeMo Agent Toolkit UI](https://github.com/NVIDIA/NeMo-Agent-Toolkit-UI)

### API文档
- [Tavily API文档](https://docs.tavily.com/)
- [阿里云百炼平台](https://bailian.console.aliyun.com/?tab=doc#/doc)
- [OpenAI API文档](https://platform.openai.com/docs/)

### 学习资源
- [AI Agent开发指南](https://docs.nvidia.com/nemo-agent-toolkit/user-guide/)
- [React Agent工作流](https://docs.nvidia.com/nemo-agent-toolkit/workflows/react-agent/)
- [MCP协议文档](https://docs.nvidia.com/nemo-agent-toolkit/mcp/)

## 🏆 黑客松信息

本项目专为推广NVIDIA NeMo Agent Toolkit技术而开发，旨在：

- 🎯 **展示AI Agent能力**: 通过实际应用展示NVIDIA NeMo Agent Toolkit的强大功能
- 🚀 **降低学习门槛**: 提供完整的示例代码和详细文档，帮助开发者快速上手
- 🌟 **促进技术交流**: 为AI Agent技术爱好者提供学习和交流的平台
- 💡 **激发创新思维**: 鼓励开发者基于此项目创建更多创新应用

### 技术亮点

- ✅ **完全官方架构**: 严格遵循NVIDIA官方技术规范
- ✅ **生产级质量**: 包含完整的错误处理、日志记录和监控
- ✅ **易于扩展**: 模块化设计，支持快速添加新功能
- ✅ **跨平台支持**: 一套代码，多平台运行



---

**🎯 我们自己探索AI Agent的无限可能！**

> 本项目展示了NVIDIA NeMo Agent Toolkit在实际应用中的强大能力，为AI Agent技术的普及化和发展贡献力量。无论您是AI初学者还是资深开发者，都能从这个项目中获得有价值的学习体验。


# AI Toolkit Hackathon Project

## API Keys Configuration

为了安全起见，所有API keys现在统一管理在一个配置文件中。

### 快速开始

1. **复制API keys模板文件**：
   ```bash
   cp api_keys.yml.template api_keys.yml
   ```

2. **编辑api_keys.yml文件**，填入您的实际API keys：
   ```yaml
   # 必需的API Keys
   MODELSCOPE_API_KEY: "your-actual-modelscope-api-key"
   TAVILY_API_KEY: "your-actual-tavily-api-key"
   
   # 可选的API Keys（根据需要配置）
   OPENAI_API_KEY: "your-openai-api-key"
   NVIDIA_API_KEY: "your-nvidia-api-key"
   BAILIAN_API_KEY: "your-bailian-api-key"
   # ... 其他API keys
   ```

3. **启动项目**：
   ```bash
   # Linux/macOS
   ./start_with_auth.sh
   
   # Windows
   install.bat
   ```

### API Keys说明

| API Key | 用途 | 必需性 |
|---------|------|--------|
| MODELSCOPE_API_KEY | ModelScope LLM服务 | 必需 |
| TAVILY_API_KEY | Tavily搜索服务 | 必需 |
| OPENAI_API_KEY | OpenAI服务 | 可选 |
| NVIDIA_API_KEY | NVIDIA服务 | 可选 |
| BAILIAN_API_KEY | 阿里云百炼服务 | 可选 |

### 安全注意事项

⚠️ **重要提醒**：
- `api_keys.yml`文件已被添加到`.gitignore`中，**不会**被提交到版本控制系统
- 请妥善保管您的API keys，不要在公开场合分享
- 如需分享项目，请使用`api_keys.yml.template`模板文件
- 定期更换API keys以确保安全

### 故障排除

如果遇到API key相关问题：

1. **检查文件是否存在**：
   ```bash
   ls -la api_keys.yml
   ```

2. **验证文件格式**：
   ```bash
   python3 -c "import yaml; print(yaml.safe_load(open('api_keys.yml')))"
   ```

3. **检查环境变量**：
   ```bash
   echo $MODELSCOPE_API_KEY
   ```

### 开发者指南

如果您需要在代码中使用API keys：

```python
# 推荐方式：使用环境变量
import os
api_key = os.getenv('MODELSCOPE_API_KEY')

# 或者使用提供的工具函数
from load_api_keys import load_api_keys
keys = load_api_keys()
api_key = keys.get('MODELSCOPE_API_KEY')
```

## 项目启动

配置完API keys后，您可以启动项目：

```bash
# 启动带认证的服务
./start_with_auth.sh
```

访问 http://localhost:8080/dashboard.html 开始使用。

---

## 实施完成总结

✅ **已完成的API Keys统一管理方案**：

### 1. 配置文件系统
- ✅ 创建了`api_keys.yml`统一配置文件
- ✅ 提供了`api_keys.yml.template`安全模板
- ✅ 更新了`.gitignore`确保API keys不被提交

### 2. 自动化加载机制
- ✅ 创建了`load_api_keys.py`Python工具
- ✅ 修改了所有启动脚本以自动加载API keys
- ✅ 配置文件现在使用环境变量引用

### 3. 跨平台支持
- ✅ Linux/macOS: `start_with_auth.sh`
- ✅ Windows: `install.bat`
- ✅ Python: `load_api_keys.py`

### 4. 安全性提升
- ✅ API keys不再硬编码在配置文件中
- ✅ 统一管理，便于维护和更新
- ✅ 版本控制安全，实际keys不会被提交

### 5. 用户体验
- ✅ 简单的配置流程
- ✅ 详细的文档说明
- ✅ 错误提示和故障排除指南

现在您的项目已经具备了安全、统一的API keys管理系统！

