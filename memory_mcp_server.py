#!/usr/bin/env python3
"""
Memory MCP服务器
按照NVIDIA官方MCP架构实现Memory知识图谱工具
支持用户对话时创建记忆，并且只保存与求职相关的信息
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
        self.knowledge_graph = {}
        self.setup_handlers()
        
        # 创建持久化存储目录
        self.storage_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "memory_storage")
        os.makedirs(self.storage_dir, exist_ok=True)
        
        # 加载现有知识图谱（如果存在）
        self._load_knowledge_graph()
    
    def _load_knowledge_graph(self):
        """从文件加载知识图谱"""
        try:
            storage_file = os.path.join(self.storage_dir, "knowledge_graph.json")
            if os.path.exists(storage_file):
                with open(storage_file, "r", encoding="utf-8") as f:
                    self.knowledge_graph = json.load(f)
                logger.info(f"已加载知识图谱，包含 {len(self.knowledge_graph)} 个实体")
        except Exception as e:
            logger.error(f"加载知识图谱失败: {e}")
            self.knowledge_graph = {}
    
    def _save_knowledge_graph(self):
        """保存知识图谱到文件"""
        try:
            storage_file = os.path.join(self.storage_dir, "knowledge_graph.json")
            with open(storage_file, "w", encoding="utf-8") as f:
                json.dump(self.knowledge_graph, f, ensure_ascii=False, indent=2)
            logger.info(f"已保存知识图谱，包含 {len(self.knowledge_graph)} 个实体")
        except Exception as e:
            logger.error(f"保存知识图谱失败: {e}")
    
    def _is_job_related(self, text):
        """判断文本是否与求职相关"""
        job_keywords = [
            "求职", "简历", "面试", "招聘", "职位", "工作", "就业", "职业", "薪资", "薪水", 
            "技能", "能力", "经验", "学历", "背景", "专业", "行业", "公司", "岗位", "职责",
            "job", "resume", "interview", "recruitment", "position", "work", "employment", 
            "career", "salary", "skill", "experience", "education", "background", 
            "profession", "industry", "company", "role", "responsibility"
        ]
        
        text_lower = text.lower()
        for keyword in job_keywords:
            if keyword.lower() in text_lower:
                return True
        return False
    
    def setup_handlers(self):
        """设置MCP处理器"""
        
        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """列出可用的工具"""
            return [
                Tool(
                    name="create_entities",
                    description="在知识图谱中创建多个新实体",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "entities": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "name": {
                                            "type": "string",
                                            "description": "实体名称"
                                        },
                                        "entityType": {
                                            "type": "string",
                                            "description": "实体类型"
                                        },
                                        "observations": {
                                            "type": "array",
                                            "items": {"type": "string"},
                                            "description": "与实体关联的观察内容数组"
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
                    description="在知识图谱中的实体之间创建多个新关系。关系应使用主动语态",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "relations": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "from": {
                                            "type": "string",
                                            "description": "关系起始实体的名称"
                                        },
                                        "to": {
                                            "type": "string",
                                            "description": "关系终止实体的名称"
                                        },
                                        "relationType": {
                                            "type": "string",
                                            "description": "关系类型"
                                        }
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
                    description="向知识图谱中的现有实体添加新观察",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "observations": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "entityName": {
                                            "type": "string",
                                            "description": "要添加观察的实体名称"
                                        },
                                        "contents": {
                                            "type": "array",
                                            "items": {"type": "string"},
                                            "description": "要添加的观察内容数组"
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
                    description="从知识图谱中删除多个实体及其关联关系",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "entityNames": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "要删除的实体名称数组"
                            }
                        },
                        "required": ["entityNames"]
                    }
                ),
                Tool(
                    name="delete_observations",
                    description="从知识图谱中的实体删除特定观察",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "deletions": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "entityName": {
                                            "type": "string",
                                            "description": "包含观察的实体名称"
                                        },
                                        "observations": {
                                            "type": "array",
                                            "items": {"type": "string"},
                                            "description": "要删除的观察数组"
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
                    description="从知识图谱中删除多个关系",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "relations": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "from": {
                                            "type": "string",
                                            "description": "关系起始实体的名称"
                                        },
                                        "to": {
                                            "type": "string",
                                            "description": "关系终止实体的名称"
                                        },
                                        "relationType": {
                                            "type": "string",
                                            "description": "关系类型"
                                        }
                                    },
                                    "required": ["from", "to", "relationType"]
                                },
                                "description": "要删除的关系数组"
                            }
                        },
                        "required": ["relations"]
                    }
                ),
                Tool(
                    name="read_graph",
                    description="读取整个知识图谱",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                ),
                Tool(
                    name="search_nodes",
                    description="基于查询在知识图谱中搜索节点",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "与实体名称、类型和观察内容匹配的搜索查询"
                            }
                        },
                        "required": ["query"]
                    }
                ),
                Tool(
                    name="open_nodes",
                    description="通过名称打开知识图谱中的特定节点",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "names": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "要检索的实体名称数组"
                            }
                        },
                        "required": ["names"]
                    }
                ),
                Tool(
                    name="process_user_message",
                    description="处理用户消息，提取求职相关信息并存储到知识图谱",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "user_id": {
                                "type": "string",
                                "description": "用户ID"
                            },
                            "message": {
                                "type": "string",
                                "description": "用户消息内容"
                            }
                        },
                        "required": ["user_id", "message"]
                    }
                ),
                Tool(
                    name="get_job_recommendations",
                    description="基于用户的知识图谱信息提供求职建议",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "user_id": {
                                "type": "string",
                                "description": "用户ID"
                            },
                            "recommendation_type": {
                                "type": "string",
                                "description": "建议类型，如'resume'（简历）, 'interview'（面试）, 'skills'（技能）, 'general'（一般建议）"
                            }
                        },
                        "required": ["user_id"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """调用工具"""
            try:
                if name == "create_entities":
                    return await self._create_entities(arguments)
                elif name == "create_relations":
                    return await self._create_relations(arguments)
                elif name == "add_observations":
                    return await self._add_observations(arguments)
                elif name == "delete_entities":
                    return await self._delete_entities(arguments)
                elif name == "delete_observations":
                    return await self._delete_observations(arguments)
                elif name == "delete_relations":
                    return await self._delete_relations(arguments)
                elif name == "read_graph":
                    return await self._read_graph(arguments)
                elif name == "search_nodes":
                    return await self._search_nodes(arguments)
                elif name == "open_nodes":
                    return await self._open_nodes(arguments)
                elif name == "process_user_message":
                    return await self._process_user_message(arguments)
                elif name == "get_job_recommendations":
                    return await self._get_job_recommendations(arguments)
                else:
                    raise ValueError(f"未知工具: {name}")
            except Exception as e:
                logger.error(f"工具调用失败: {e}")
                return [TextContent(type="text", text=f"错误: {str(e)}")]
    
    async def _create_entities(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """创建实体"""
        entities = arguments.get("entities", [])
        
        if not entities:
            return [TextContent(type="text", text="错误: 未提供实体")]
        
        try:
            created = []
            for entity in entities:
                name = entity.get("name")
                entity_type = entity.get("entityType")
                observations = entity.get("observations", [])
                
                if not name or not entity_type:
                    continue
                
                # 创建或更新实体
                if name not in self.knowledge_graph:
                    self.knowledge_graph[name] = {
                        "type": entity_type,
                        "observations": observations,
                        "relations": []
                    }
                else:
                    # 更新现有实体
                    self.knowledge_graph[name]["type"] = entity_type
                    self.knowledge_graph[name]["observations"].extend(observations)
                
                created.append(name)
            
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
            created = []
            skipped = []
            
            for relation in relations:
                from_entity = relation.get("from")
                to_entity = relation.get("to")
                relation_type = relation.get("relationType")
                
                if not from_entity or not to_entity or not relation_type:
                    continue
                
                # 检查实体是否存在
                if from_entity not in self.knowledge_graph or to_entity not in self.knowledge_graph:
                    skipped.append({
                        "from": from_entity,
                        "to": to_entity,
                        "type": relation_type,
                        "reason": "一个或多个实体不存在"
                    })
                    continue
                
                # 添加关系
                relation_obj = {
                    "to": to_entity,
                    "type": relation_type
                }
                
                # 检查关系是否已存在
                exists = False
                for existing_rel in self.knowledge_graph[from_entity]["relations"]:
                    if existing_rel["to"] == to_entity and existing_rel["type"] == relation_type:
                        exists = True
                        break
                
                if not exists:
                    self.knowledge_graph[from_entity]["relations"].append(relation_obj)
                    created.append({
                        "from": from_entity,
                        "to": to_entity,
                        "type": relation_type
                    })
                else:
                    skipped.append({
                        "from": from_entity,
                        "to": to_entity,
                        "type": relation_type,
                        "reason": "关系已存在"
                    })
            
            result = {
                "created": created,
                "skipped": skipped,
                "created_count": len(created),
                "skipped_count": len(skipped)
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
            added = []
            skipped = []
            
            for obs_item in observations_list:
                entity_name = obs_item.get("entityName")
                contents = obs_item.get("contents", [])
                
                if not entity_name or not contents:
                    continue
                
                # 检查实体是否存在
                if entity_name not in self.knowledge_graph:
                    skipped.append({
                        "entity": entity_name,
                        "reason": "实体不存在"
                    })
                    continue
                
                # 添加观察
                for content in contents:
                    if content not in self.knowledge_graph[entity_name]["observations"]:
                        self.knowledge_graph[entity_name]["observations"].append(content)
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
            deleted = []
            not_found = []
            
            for name in entity_names:
                if name in self.knowledge_graph:
                    del self.knowledge_graph[name]
                    deleted.append(name)
                    
                    # 删除指向该实体的关系
                    for entity_name, entity_data in self.knowledge_graph.items():
                        entity_data["relations"] = [
                            rel for rel in entity_data["relations"] if rel["to"] != name
                        ]
                else:
                    not_found.append(name)
            
            result = {
                "deleted": deleted,
                "not_found": not_found,
                "deleted_count": len(deleted),
                "not_found_count": len(not_found)
            }
            
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]
            
        except Exception as e:
            logger.error(f"删除实体失败: {e}")
            return [TextContent(type="text", text=f"删除实体失败: {str(e)}")]
    
    async def _delete_observations(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """删除观察"""
        deletions = arguments.get("deletions", [])
        
        if not deletions:
            return [TextContent(type="text", text="错误: 未提供删除项")]
        
        try:
            deleted = []
            not_found = []
            
            for deletion in deletions:
                entity_name = deletion.get("entityName")
                observations = deletion.get("observations", [])
                
                if not entity_name or not observations:
                    continue
                
                # 检查实体是否存在
                if entity_name not in self.knowledge_graph:
                    not_found.append({
                        "entity": entity_name,
                        "reason": "实体不存在"
                    })
                    continue
                
                # 删除观察
                for obs in observations:
                    if obs in self.knowledge_graph[entity_name]["observations"]:
                        self.knowledge_graph[entity_name]["observations"].remove(obs)
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
            
            result = {
                "deleted": deleted,
                "not_found": not_found,
                "deleted_count": len(deleted),
                "not_found_count": len(not_found)
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
            deleted = []
            not_found = []
            
            for relation in relations:
                from_entity = relation.get("from")
                to_entity = relation.get("to")
                relation_type = relation.get("relationType")
                
                if not from_entity or not to_entity or not relation_type:
                    continue
                
                # 检查实体是否存在
                if from_entity not in self.knowledge_graph:
                    not_found.append({
                        "from": from_entity,
                        "to": to_entity,
                        "type": relation_type,
                        "reason": "起始实体不存在"
                    })
                    continue
                
                # 查找并删除关系
                found = False
                for i, rel in enumerate(self.knowledge_graph[from_entity]["relations"]):
                    if rel["to"] == to_entity and rel["type"] == relation_type:
                        del self.knowledge_graph[from_entity]["relations"][i]
                        deleted.append({
                            "from": from_entity,
                            "to": to_entity,
                            "type": relation_type
                        })
                        found = True
                        break
                
                if not found:
                    not_found.append({
                        "from": from_entity,
                        "to": to_entity,
                        "type": relation_type,
                        "reason": "关系不存在"
                    })
            
            result = {
                "deleted": deleted,
                "not_found": not_found,
                "deleted_count": len(deleted),
                "not_found_count": len(not_found)
            }
            
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]
            
        except Exception as e:
            logger.error(f"删除关系失败: {e}")
            return [TextContent(type="text", text=f"删除关系失败: {str(e)}")]
    
    async def _read_graph(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """读取整个知识图谱"""
        try:
            result = {
                "entities": len(self.knowledge_graph),
                "graph": self.knowledge_graph
            }
            
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]
            
        except Exception as e:
            logger.error(f"读取知识图谱失败: {e}")
            return [TextContent(type="text", text=f"读取知识图谱失败: {str(e)}")]
    
    async def _search_nodes(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """搜索节点"""
        query = arguments.get("query", "")
        
        if not query:
            return [TextContent(type="text", text="错误: 未提供查询")]
        
        try:
            results = []
            
            # 简单的字符串匹配搜索
            query = query.lower()
            for name, data in self.knowledge_graph.items():
                matched = False
                
                # 检查名称
                if query in name.lower():
                    matched = True
                
                # 检查类型
                if query in data["type"].lower():
                    matched = True
                
                # 检查观察
                for obs in data["observations"]:
                    if query in obs.lower():
                        matched = True
                        break
                
                if matched:
                    results.append({
                        "name": name,
                        "type": data["type"],
                        "observations_count": len(data["observations"]),
                        "relations_count": len(data["relations"])
                    })
            
            result = {
                "query": query,
                "results": results,
                "count": len(results)
            }
            
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]
            
        except Exception as e:
            logger.error(f"搜索节点失败: {e}")
            return [TextContent(type="text", text=f"搜索节点失败: {str(e)}")]
    
    async def _open_nodes(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """打开节点"""
        names = arguments.get("names", [])
        
        if not names:
            return [TextContent(type="text", text="错误: 未提供实体名称")]
        
        try:
            results = {}
            not_found = []
            
            for name in names:
                if name in self.knowledge_graph:
                    results[name] = self.knowledge_graph[name]
                else:
                    not_found.append(name)
            
            result = {
                "entities": results,
                "not_found": not_found,
                "found_count": len(results),
                "not_found_count": len(not_found)
            }
            
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]
            
        except Exception as e:
            logger.error(f"打开节点失败: {e}")
            return [TextContent(type="text", text=f"打开节点失败: {str(e)}")]
    
    async def _process_user_message(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """处理用户消息，提取求职相关信息并存储到知识图谱"""
        user_id = arguments.get("user_id")
        message = arguments.get("message")
        
        if not user_id or not message:
            return [TextContent(type="text", text="错误: 未提供用户ID或消息内容")]
        
        try:
            # 检查消息是否与求职相关
            if not self._is_job_related(message):
                return [TextContent(type="text", text=json.dumps({
                    "status": "skipped",
                    "reason": "消息内容与求职无关"
                }, ensure_ascii=False, indent=2))]
            
            # 确保用户实体存在
            user_entity_name = f"user:{user_id}"
            if user_entity_name not in self.knowledge_graph:
                # 创建用户实体
                self.knowledge_graph[user_entity_name] = {
                    "type": "user",
                    "observations": [],
                    "relations": []
                }
            
            # 创建消息实体
            timestamp = datetime.now().isoformat()
            message_entity_name = f"message:{user_id}:{timestamp}"
            
            self.knowledge_graph[message_entity_name] = {
                "type": "message",
                "observations": [message],
                "relations": []
            }
            
            # 创建用户与消息之间的关系
            self.knowledge_graph[user_entity_name]["relations"].append({
                "to": message_entity_name,
                "type": "sent"
            })
            
            # 提取关键信息并添加到用户实体的观察中
            # 这里可以使用更复杂的NLP技术来提取关键信息，这里简化处理
            key_info = message
            if key_info not in self.knowledge_graph[user_entity_name]["observations"]:
                self.knowledge_graph[user_entity_name]["observations"].append(key_info)
            
            # 保存知识图谱
            self._save_knowledge_graph()
            
            result = {
                "status": "success",
                "user_entity": user_entity_name,
                "message_entity": message_entity_name,
                "timestamp": timestamp
            }
            
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]
            
        except Exception as e:
            logger.error(f"处理用户消息失败: {e}")
            return [TextContent(type="text", text=f"处理用户消息失败: {str(e)}")]
    
    async def _get_job_recommendations(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """基于用户的知识图谱信息提供求职建议"""
        user_id = arguments.get("user_id")
        recommendation_type = arguments.get("recommendation_type", "general")
        
        if not user_id:
            return [TextContent(type="text", text="错误: 未提供用户ID")]
        
        try:
            user_entity_name = f"user:{user_id}"
            
            # 检查用户是否存在
            if user_entity_name not in self.knowledge_graph:
                return [TextContent(type="text", text=json.dumps({
                    "status": "error",
                    "reason": "用户不存在"
                }, ensure_ascii=False, indent=2))]
            
            # 获取用户的所有观察
            user_observations = self.knowledge_graph[user_entity_name]["observations"]
            
            # 获取用户的所有消息
            user_messages = []
            for relation in self.knowledge_graph[user_entity_name]["relations"]:
                if relation["type"] == "sent" and relation["to"] in self.knowledge_graph:
                    message_entity = self.knowledge_graph[relation["to"]]
                    if message_entity["observations"]:
                        user_messages.extend(message_entity["observations"])
            
            # 根据推荐类型生成建议
            recommendations = []
            
            if recommendation_type == "resume":
                recommendations.append("基于您的背景，建议在简历中突出以下几点：")
                # 这里可以添加更复杂的逻辑来生成具体的简历建议
                for obs in user_observations:
                    if any(kw in obs.lower() for kw in ["经验", "技能", "项目", "学历"]):
                        recommendations.append(f"- {obs}")
            
            elif recommendation_type == "interview":
                recommendations.append("针对面试，您可以准备以下几个方面：")
                # 这里可以添加更复杂的逻辑来生成具体的面试建议
                for obs in user_observations:
                    if any(kw in obs.lower() for kw in ["面试", "问题", "回答", "技能"]):
                        recommendations.append(f"- {obs}")
            
            elif recommendation_type == "skills":
                recommendations.append("根据您的情况，建议提升以下技能：")
                # 这里可以添加更复杂的逻辑来生成具体的技能建议
                for obs in user_observations:
                    if any(kw in obs.lower() for kw in ["技能", "能力", "学习", "提升"]):
                        recommendations.append(f"- {obs}")
            
            else:  # general
                recommendations.append("基于您的信息，以下是一些求职建议：")
                # 这里可以添加更复杂的逻辑来生成一般建议
                for obs in user_observations:
                    recommendations.append(f"- {obs}")
            
            # 如果没有足够的信息生成建议
            if len(recommendations) <= 1:
                recommendations = ["目前没有足够的信息来提供具体建议，请分享更多关于您求职需求的信息。"]
            
            result = {
                "status": "success",
                "user_id": user_id,
                "recommendation_type": recommendation_type,
                "recommendations": recommendations
            }
            
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]
            
        except Exception as e:
            logger.error(f"获取求职建议失败: {e}")
            return [TextContent(type="text", text=f"获取求职建议失败: {str(e)}")]
    
    async def run(self):
        """运行MCP服务器"""
        logger.info("启动Memory MCP服务器...")
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