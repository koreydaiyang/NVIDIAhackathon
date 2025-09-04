#!/usr/bin/env python3
"""
Memory MCP服务器
按照NVIDIA官方MCP架构实现Memory知识图谱工具
支持用户对话时创建记忆，并且只保存与求职相关的信息
支持多用户存储
"""

import asyncio
import json
import logging
import sys
import subprocess
import re
import os
from typing import Any, Dict, List, Optional
from datetime import datetime

# 检查并安装必要的依赖
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import (
        CallToolRequest,
        CallToolResult,
        ListToolsRequest,
        ListToolsResult,
        Tool,
        TextContent,
    )
except ImportError:
    print("正在安装必要的依赖: mcp...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "mcp~=1.10"])
    
    # 重新导入
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import (
        CallToolRequest,
        CallToolResult,
        ListToolsRequest,
        ListToolsResult,
        Tool,
        TextContent,
    )

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MemoryMCPServer:
    """Memory MCP服务器类"""
    
    def __init__(self):
        self.server = Server("memory-knowledge-graph")
        self.user_knowledge_graphs = {}  # 存储每个用户的知识图谱
        self.current_user = None  # 当前用户
        self.setup_handlers()
        
        # 创建持久化存储目录
        self.storage_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "memory_storage")
        os.makedirs(self.storage_dir, exist_ok=True)
        
        # 为每个用户创建独立的存储目录
        self.users_dir = os.path.join(self.storage_dir, "users")
        os.makedirs(self.users_dir, exist_ok=True)
    
    def _load_user_knowledge_graph(self, username):
        """从文件加载指定用户的知识图谱"""
        try:
            user_dir = os.path.join(self.users_dir, username)
            os.makedirs(user_dir, exist_ok=True)
            
            storage_file = os.path.join(user_dir, "knowledge_graph.json")
            if os.path.exists(storage_file):
                with open(storage_file, "r", encoding="utf-8") as f:
                    self.user_knowledge_graphs[username] = json.load(f)
                logger.info(f"已加载用户 {username} 的知识图谱，包含 {len(self.user_knowledge_graphs[username])} 个实体")
            else:
                self.user_knowledge_graphs[username] = {}
                logger.info(f"为用户 {username} 创建新的知识图谱")
        except Exception as e:
            logger.error(f"加载用户 {username} 的知识图谱失败: {e}")
            self.user_knowledge_graphs[username] = {}
    
    def _save_user_knowledge_graph(self, username):
        """保存指定用户的知识图谱到文件"""
        try:
            if username not in self.user_knowledge_graphs:
                return
                
            user_dir = os.path.join(self.users_dir, username)
            os.makedirs(user_dir, exist_ok=True)
            
            storage_file = os.path.join(user_dir, "knowledge_graph.json")
            with open(storage_file, "w", encoding="utf-8") as f:
                json.dump(self.user_knowledge_graphs[username], f, ensure_ascii=False, indent=2)
            logger.info(f"已保存用户 {username} 的知识图谱，包含 {len(self.user_knowledge_graphs[username])} 个实体")
        except Exception as e:
            logger.error(f"保存用户 {username} 的知识图谱失败: {e}")
    
    def set_current_user(self, username):
        """设置当前用户"""
        self.current_user = username
        if username not in self.user_knowledge_graphs:
            self._load_user_knowledge_graph(username)
        logger.info(f"当前用户设置为: {username}")
    
    def get_current_knowledge_graph(self):
        """获取当前用户的知识图谱"""
        if not self.current_user:
            return {}
        return self.user_knowledge_graphs.get(self.current_user, {})
    
    def update_current_knowledge_graph(self, graph):
        """更新当前用户的知识图谱"""
        if self.current_user:
            self.user_knowledge_graphs[self.current_user] = graph
            self._save_user_knowledge_graph(self.current_user)
    
    def _is_job_related(self, text):
        """判断文本是否与求职相关"""
        job_keywords = [
            "工作", "职位", "求职", "面试", "简历", "技能", "经验", "公司", "薪资", "职业",
            "招聘", "应聘", "岗位", "职场", "工资", "待遇", "福利", "晋升", "发展", "培训",
            "job", "work", "career", "interview", "resume", "skill", "experience", "company",
            "salary", "position", "employment", "hiring", "application", "workplace"
        ]
        
        text_lower = text.lower()
        return any(keyword.lower() in text_lower for keyword in job_keywords)
    
    def setup_handlers(self):
        """设置MCP服务器的处理器"""
        
        @self.server.list_tools()
        async def list_tools() -> ListToolsResult:
            """列出所有可用的工具"""
            return ListToolsResult(
                tools=[
                    Tool(
                        name="create_entities",
                        description="Create multiple new entities in the knowledge graph",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "entities": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "name": {"type": "string", "description": "The name of the entity"},
                                            "entityType": {"type": "string", "description": "The type of the entity"},
                                            "observations": {
                                                "type": "array",
                                                "items": {"type": "string"},
                                                "description": "An array of observation contents associated with the entity"
                                            }
                                        },
                                        "required": ["name", "entityType", "observations"]
                                    }
                                }
                            },
                            "required": ["entities"]
                        }
                    ),
                    Tool(
                        name="create_relations",
                        description="Create multiple new relations between entities in the knowledge graph. Relations should be in active voice",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "relations": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "from": {"type": "string", "description": "The name of the entity where the relation starts"},
                                            "to": {"type": "string", "description": "The name of the entity where the relation ends"},
                                            "relationType": {"type": "string", "description": "The type of the relation"}
                                        },
                                        "required": ["from", "to", "relationType"]
                                    }
                                }
                            },
                            "required": ["relations"]
                        }
                    ),
                    Tool(
                        name="add_observations",
                        description="Add new observations to existing entities in the knowledge graph",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "observations": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "entityName": {"type": "string", "description": "The name of the entity to add the observations to"},
                                            "contents": {
                                                "type": "array",
                                                "items": {"type": "string"},
                                                "description": "An array of observation contents to add"
                                            }
                                        },
                                        "required": ["entityName", "contents"]
                                    }
                                }
                            },
                            "required": ["observations"]
                        }
                    ),
                    Tool(
                        name="delete_entities",
                        description="Delete multiple entities and their associated relations from the knowledge graph",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "entityNames": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "An array of entity names to delete"
                                }
                            },
                            "required": ["entityNames"]
                        }
                    ),
                    Tool(
                        name="delete_observations",
                        description="Delete specific observations from entities in the knowledge graph",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "deletions": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "entityName": {"type": "string", "description": "The name of the entity containing the observations"},
                                            "observations": {
                                                "type": "array",
                                                "items": {"type": "string"},
                                                "description": "An array of observations to delete"
                                            }
                                        },
                                        "required": ["entityName", "observations"]
                                    }
                                }
                            },
                            "required": ["deletions"]
                        }
                    ),
                    Tool(
                        name="delete_relations",
                        description="Delete multiple relations from the knowledge graph",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "relations": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "from": {"type": "string", "description": "The name of the entity where the relation starts"},
                                            "to": {"type": "string", "description": "The name of the entity where the relation ends"},
                                            "relationType": {"type": "string", "description": "The type of the relation"}
                                        },
                                        "required": ["from", "to", "relationType"]
                                    },
                                    "description": "An array of relations to delete"
                                }
                            },
                            "required": ["relations"]
                        }
                    ),
                    Tool(
                        name="read_graph",
                        description="Read the entire knowledge graph",
                        inputSchema={
                            "type": "object",
                            "properties": {}
                        }
                    ),
                    Tool(
                        name="search_nodes",
                        description="Search for nodes in the knowledge graph based on a query",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "query": {"type": "string", "description": "The search query to match against entity names, types, and observation content"}
                            },
                            "required": ["query"]
                        }
                    ),
                    Tool(
                        name="open_nodes",
                        description="Open specific nodes in the knowledge graph by their names",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "names": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "An array of entity names to retrieve"
                                }
                            },
                            "required": ["names"]
                        }
                    )
                ]
            )
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
            """处理工具调用"""
            try:
                if name == "create_entities":
                    result = await self._create_entities(arguments)
                elif name == "create_relations":
                    result = await self._create_relations(arguments)
                elif name == "add_observations":
                    result = await self._add_observations(arguments)
                elif name == "delete_entities":
                    result = await self._delete_entities(arguments)
                elif name == "delete_observations":
                    result = await self._delete_observations(arguments)
                elif name == "delete_relations":
                    result = await self._delete_relations(arguments)
                elif name == "read_graph":
                    result = await self._read_graph(arguments)
                elif name == "search_nodes":
                    result = await self._search_nodes(arguments)
                elif name == "open_nodes":
                    result = await self._open_nodes(arguments)
                else:
                    result = [TextContent(type="text", text=f"未知工具: {name}")]
                
                return CallToolResult(content=result)
            except Exception as e:
                logger.error(f"工具调用失败 {name}: {e}")
                return CallToolResult(
                    content=[TextContent(type="text", text=f"工具调用失败: {str(e)}")],
                    isError=True
                )
    
    async def _create_entities(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """创建实体"""
        entities = arguments.get("entities", [])
        
        if not entities:
            return [TextContent(type="text", text="错误: 未提供实体")]
        
        try:
            # 获取当前用户的知识图谱
            knowledge_graph = self.get_current_knowledge_graph()
            
            created = []
            for entity in entities:
                name = entity.get("name")
                entity_type = entity.get("entityType")
                observations = entity.get("observations", [])
                
                # 过滤求职相关的观察
                job_related_observations = [obs for obs in observations if self._is_job_related(obs)]
                
                if not name or not entity_type:
                    continue
                
                # 创建或更新实体
                if name not in knowledge_graph:
                    knowledge_graph[name] = {
                        "type": entity_type,
                        "observations": job_related_observations,
                        "relations": []
                    }
                else:
                    # 更新现有实体
                    knowledge_graph[name]["type"] = entity_type
                    knowledge_graph[name]["observations"].extend(job_related_observations)
                
                created.append(name)
            
            # 更新知识图谱
            self.update_current_knowledge_graph(knowledge_graph)
            
            result = {
                "created": created,
                "count": len(created)
            }
            
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]
            
        except Exception as e:
            logger.error(f"创建实体失败: {e}")
            return [TextContent(type="text", text=f"创建实体失败: {str(e)}")]

    async def _create_relations(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """创建关系"""
        relations = arguments.get("relations", [])
        
        if not relations:
            return [TextContent(type="text", text="错误: 未提供关系")]
        
        try:
            # 获取当前用户的知识图谱
            knowledge_graph = self.get_current_knowledge_graph()
            
            created = []
            skipped = []
            
            for relation in relations:
                from_entity = relation.get("from")
                to_entity = relation.get("to")
                relation_type = relation.get("relationType")
                
                if not from_entity or not to_entity or not relation_type:
                    continue
                
                # 检查实体是否存在
                if from_entity not in knowledge_graph or to_entity not in knowledge_graph:
                    skipped.append({
                        "from": from_entity,
                        "to": to_entity,
                        "type": relation_type,
                        "reason": "实体不存在"
                    })
                    continue
                
                # 检查关系是否已存在
                relation_exists = False
                for existing_rel in knowledge_graph[from_entity]["relations"]:
                    if (existing_rel["type"] == relation_type and 
                        existing_rel["to"] == to_entity):
                        relation_exists = True
                        break
                
                if relation_exists:
                    skipped.append({
                        "from": from_entity,
                        "to": to_entity,
                        "type": relation_type,
                        "reason": "关系已存在"
                    })
                    continue
                
                # 创建关系对象
                relation_obj = {
                    "type": relation_type,
                    "to": to_entity,
                    "created_at": datetime.now().isoformat()
                }
                
                # 添加关系
                knowledge_graph[from_entity]["relations"].append(relation_obj)
                created.append({
                    "from": from_entity,
                    "to": to_entity,
                    "type": relation_type
                })
            
            # 更新知识图谱
            self.update_current_knowledge_graph(knowledge_graph)
            
            result = {
                "created": created,
                "skipped": skipped,
                "count": len(created)
            }
            
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]
            
        except Exception as e:
            logger.error(f"创建关系失败: {e}")
            return [TextContent(type="text", text=f"创建关系失败: {str(e)}")]

    async def _add_observations(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """添加观察"""
        observations_list = arguments.get("observations", [])
        
        if not observations_list:
            return [TextContent(type="text", text="错误: 未提供观察")]
        
        try:
            # 获取当前用户的知识图谱
            knowledge_graph = self.get_current_knowledge_graph()
            
            added = []
            skipped = []
            
            for obs_item in observations_list:
                entity_name = obs_item.get("entityName")
                contents = obs_item.get("contents", [])
                
                if not entity_name or not contents:
                    continue
                
                # 检查实体是否存在
                if entity_name not in knowledge_graph:
                    skipped.append({
                        "entity": entity_name,
                        "reason": "实体不存在"
                    })
                    continue
                
                # 添加观察
                for content in contents:
                    if content not in knowledge_graph[entity_name]["observations"]:
                        knowledge_graph[entity_name]["observations"].append(content)
                        added.append({
                            "entity": entity_name,
                            "content": content
                        })
                    else:
                        skipped.append({
                            "entity": entity_name,
                            "content": content,
                            "reason": "观察已存在"
                        })
            
            # 更新知识图谱
            self.update_current_knowledge_graph(knowledge_graph)
            
            result = {
                "added": added,
                "skipped": skipped,
                "added_count": len(added),
                "skipped_count": len(skipped)
            }
            
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]
            
        except Exception as e:
            logger.error(f"添加观察失败: {e}")
            return [TextContent(type="text", text=f"添加观察失败: {str(e)}")]
    
    async def _delete_entities(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """删除实体"""
        entity_names = arguments.get("entityNames", [])
        
        if not entity_names:
            return [TextContent(type="text", text="错误: 未提供实体名称")]
        
        try:
            # 获取当前用户的知识图谱
            knowledge_graph = self.get_current_knowledge_graph()
            
            deleted = []
            not_found = []
            
            for name in entity_names:
                if name in knowledge_graph:
                    del knowledge_graph[name]
                    deleted.append(name)
                    
                    # 删除指向该实体的关系
                    for entity_name, entity_data in knowledge_graph.items():
                        entity_data["relations"] = [
                            rel for rel in entity_data["relations"] 
                            if rel["to"] != name
                        ]
                else:
                    not_found.append(name)
            
            # 更新知识图谱
            self.update_current_knowledge_graph(knowledge_graph)
            
            result = {
                "deleted": deleted,
                "not_found": not_found,
                "count": len(deleted)
            }
            
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]
            
        except Exception as e:
            logger.error(f"删除实体失败: {e}")
            return [TextContent(type="text", text=f"删除实体失败: {str(e)}")]
    
    async def _delete_observations(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """删除观察"""
        deletions = arguments.get("deletions", [])
        
        if not deletions:
            return [TextContent(type="text", text="错误: 未提供删除信息")]
        
        try:
            # 获取当前用户的知识图谱
            knowledge_graph = self.get_current_knowledge_graph()
            
            deleted = []
            not_found = []
            
            for deletion in deletions:
                entity_name = deletion.get("entityName")
                observations = deletion.get("observations", [])
                
                if not entity_name or not observations:
                    continue
                
                if entity_name not in knowledge_graph:
                    not_found.append({
                        "entity": entity_name,
                        "reason": "实体不存在"
                    })
                    continue
                
                for obs in observations:
                    if obs in knowledge_graph[entity_name]["observations"]:
                        knowledge_graph[entity_name]["observations"].remove(obs)
                        deleted.append({
                            "entity": entity_name,
                            "observation": obs
                        })
                    else:
                        not_found.append({
                            "entity": entity_name,
                            "observation": obs,
                            "reason": "观察不存在"
                        })
            
            # 更新知识图谱
            self.update_current_knowledge_graph(knowledge_graph)
            
            result = {
                "deleted": deleted,
                "not_found": not_found,
                "count": len(deleted)
            }
            
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]
            
        except Exception as e:
            logger.error(f"删除观察失败: {e}")
            return [TextContent(type="text", text=f"删除观察失败: {str(e)}")]
    
    async def _delete_relations(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """删除关系"""
        relations = arguments.get("relations", [])
        
        if not relations:
            return [TextContent(type="text", text="错误: 未提供关系")]
        
        try:
            # 获取当前用户的知识图谱
            knowledge_graph = self.get_current_knowledge_graph()
            
            deleted = []
            not_found = []
            
            for relation in relations:
                from_entity = relation.get("from")
                to_entity = relation.get("to")
                relation_type = relation.get("relationType")
                
                if not from_entity or not to_entity or not relation_type:
                    continue
                
                if from_entity not in knowledge_graph:
                    not_found.append({
                        "from": from_entity,
                        "to": to_entity,
                        "type": relation_type,
                        "reason": "源实体不存在"
                    })
                    continue
                
                # 查找并删除关系
                relations_list = knowledge_graph[from_entity]["relations"]
                for i, rel in enumerate(relations_list):
                    if rel["type"] == relation_type and rel["to"] == to_entity:
                        del knowledge_graph[from_entity]["relations"][i]
                        deleted.append({
                            "from": from_entity,
                            "to": to_entity,
                            "type": relation_type
                        })
                        break
                else:
                    not_found.append({
                        "from": from_entity,
                        "to": to_entity,
                        "type": relation_type,
                        "reason": "关系不存在"
                    })
            
            # 更新知识图谱
            self.update_current_knowledge_graph(knowledge_graph)
            
            result = {
                "deleted": deleted,
                "not_found": not_found,
                "count": len(deleted)
            }
            
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]
            
        except Exception as e:
            logger.error(f"删除关系失败: {e}")
            return [TextContent(type="text", text=f"删除关系失败: {str(e)}")]
    
    async def _read_graph(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """读取整个知识图谱"""
        try:
            # 获取当前用户的知识图谱
            knowledge_graph = self.get_current_knowledge_graph()
            
            result = {
                "entities": len(knowledge_graph),
                "graph": knowledge_graph
            }
            
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]
            
        except Exception as e:
            logger.error(f"读取知识图谱失败: {e}")
            return [TextContent(type="text", text=f"读取知识图谱失败: {str(e)}")]
    
    async def _search_nodes(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """搜索节点"""
        query = arguments.get("query", "")
        
        if not query:
            return [TextContent(type="text", text="错误: 未提供搜索查询")]
        
        try:
            # 获取当前用户的知识图谱
            knowledge_graph = self.get_current_knowledge_graph()
            
            results = {}
            query_lower = query.lower()
            
            for name, data in knowledge_graph.items():
                # 搜索实体名称、类型和观察内容
                if (query_lower in name.lower() or 
                    query_lower in data.get("type", "").lower() or
                    any(query_lower in obs.lower() for obs in data.get("observations", []))):
                    results[name] = data
            
            result = {
                "query": query,
                "matches": len(results),
                "results": results
            }
            
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]
            
        except Exception as e:
            logger.error(f"搜索节点失败: {e}")
            return [TextContent(type="text", text=f"搜索节点失败: {str(e)}")]
    
    async def _open_nodes(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """打开指定节点"""
        names = arguments.get("names", [])
        
        if not names:
            return [TextContent(type="text", text="错误: 未提供节点名称")]
        
        try:
            # 获取当前用户的知识图谱
            knowledge_graph = self.get_current_knowledge_graph()
            
            results = {}
            not_found = []
            
            for name in names:
                if name in knowledge_graph:
                    results[name] = knowledge_graph[name]
                else:
                    not_found.append(name)
            
            result = {
                "requested": names,
                "found": len(results),
                "not_found": not_found,
                "results": results
            }
            
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]
            
        except Exception as e:
            logger.error(f"打开节点失败: {e}")
            return [TextContent(type="text", text=f"打开节点失败: {str(e)}")]
    
    async def run(self):
        """运行MCP服务器"""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )

async def main():
    """主函数"""
    server = MemoryMCPServer()
    await server.run()

if __name__ == "__main__":
    asyncio.run(main())