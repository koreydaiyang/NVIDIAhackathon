# Memory MCP 求职助手集成指南

本文档介绍如何使用Memory MCP服务器来增强求职助手功能，实现用户对话记忆和个性化求职建议。

## 功能概述

- **用户记忆存储**：自动识别并存储用户对话中的求职相关信息
- **知识图谱构建**：将用户信息构建为知识图谱，包含实体和关系
- **个性化求职建议**：基于用户的历史信息提供针对性的求职建议
- **多类型建议**：支持简历、面试、技能提升等多种类型的建议

## 系统架构

系统由以下组件组成：

1. **Memory MCP服务器**：提供知识图谱存储和检索功能
2. **主应用程序**：使用NeMo Agent Toolkit处理用户请求
3. **配置文件**：定义Memory MCP服务和主应用程序的集成方式

## 启动指南

### 1. 启动Memory MCP服务器

```bash
# 确保脚本有执行权限
chmod +x start_memory_mcp.sh

# 启动Memory MCP服务器
./start_memory_mcp.sh
```

### 2. 启动主应用程序

在另一个终端窗口中：

```bash
# 启动主应用程序
python -m aiq.cli.run --config configs/hackathon_config.yml
```

## 使用示例

### 示例脚本

我们提供了一个示例脚本 `examples/job_search_with_memory.py`，展示如何使用Memory MCP进行求职对话：

```bash
python examples/job_search_with_memory.py
```

### 代码示例

以下是如何在代码中使用Memory MCP的示例：

```python
# 处理用户消息并存储到Memory MCP
async def process_message(agent, user_id, message):
    return await agent.call_function(
        "memory_knowledge_graph",
        {
            "tool_name": "process_user_message",
            "args": {
                "user_id": user_id,
                "message": message
            }
        }
    )

# 获取求职建议
async def get_recommendations(agent, user_id, recommendation_type="general"):
    return await agent.call_function(
        "memory_knowledge_graph",
        {
            "tool_name": "get_job_recommendations",
            "args": {
                "user_id": user_id,
                "recommendation_type": recommendation_type
            }
        }
    )
```

## 可用工具

Memory MCP提供以下工具：

1. **process_user_message**：处理用户消息，提取求职相关信息
   - 参数：`user_id`（用户ID）, `message`（消息内容）

2. **get_job_recommendations**：获取求职建议
   - 参数：`user_id`（用户ID）, `recommendation_type`（建议类型，可选值：general, resume, interview, skills）

3. **create_entities**：创建知识图谱实体

4. **create_relations**：创建实体间关系

5. **add_observations**：添加实体观察

6. **read_graph**：读取整个知识图谱

7. **search_nodes**：搜索知识图谱节点

8. **open_nodes**：打开特定节点

## 数据持久化

用户的知识图谱数据会自动保存在 `memory_storage/knowledge_graph.json` 文件中，确保在应用程序重启后数据不会丢失。

## 自定义与扩展

您可以通过以下方式扩展系统功能：

1. 修改 `_is_job_related` 方法中的关键词列表，以更精确地识别求职相关信息
2. 在 `_process_user_message` 方法中添加更复杂的NLP处理逻辑
3. 在 `_get_job_recommendations` 方法中增强建议生成逻辑
4. 添加新的工具以支持更多功能