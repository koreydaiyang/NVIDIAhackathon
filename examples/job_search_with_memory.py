#!/usr/bin/env python3
"""
求职助手示例 - 使用Memory MCP存储用户信息

此示例展示如何使用Memory MCP服务器来存储和检索用户的求职相关信息，
并基于这些信息提供个性化的求职建议。
"""

import asyncio
import json
import uuid
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import subprocess
import time

# 生成唯一的用户ID
USER_ID = str(uuid.uuid4())

async def process_message(agent, message):
    """处理用户消息，将求职相关信息存储到Memory MCP"""
    # 调用Memory MCP处理用户消息
    memory_result = await agent.call_function(
        "memory_knowledge_graph",
        {
            "tool_name": "process_user_message",
            "args": {
                "user_id": USER_ID,
                "message": message
            }
        }
    )
    
    # 解析结果
    try:
        result = json.loads(memory_result)
        return result
    except:
        return {"status": "error", "message": memory_result}

async def get_job_recommendations(agent, recommendation_type="general"):
    """获取基于用户信息的求职建议"""
    # 调用Memory MCP获取求职建议
    memory_result = await agent.call_function(
        "memory_knowledge_graph",
        {
            "tool_name": "get_job_recommendations",
            "args": {
                "user_id": USER_ID,
                "recommendation_type": recommendation_type
            }
        }
    )
    
    # 解析结果
    try:
        result = json.loads(memory_result)
        return result
    except:
        return {"status": "error", "message": memory_result}

async def main():
    """主函数"""
    print("初始化求职助手...")
    
    # 启动Memory MCP服务器
    print("启动Memory MCP服务器...")
    try:
        # 检查服务器是否已经在运行
        subprocess.run(["bash", "start_memory_mcp.sh"], check=True)
        # 等待服务器启动
        time.sleep(2)
        print("Memory MCP服务器已启动")
    except subprocess.CalledProcessError:
        print("警告: Memory MCP服务器可能已经在运行或启动失败")
    
    # 简单配置
    config = {"functions": {"memory_knowledge_graph": {}}}
    
    # 创建一个简单的代理对象
    class SimpleAgent:
        async def call_function(self, function_name, args):
            # 这里简化处理，实际应用中应该调用MCP服务器API
            if function_name == "memory_knowledge_graph":
                if args["tool_name"] == "process_user_message":
                    # 简单模拟处理用户消息
                    return json.dumps({"status": "success", "message": "信息已处理"})
                elif args["tool_name"] == "get_job_recommendations":
                    # 简单模拟获取建议
                    recommendations = [
                        f"建议 1: 根据您的经验，考虑申请{args['args']['recommendation_type']}相关职位",
                        f"建议 2: 提升您的{args['args']['recommendation_type']}技能可以增加竞争力"
                    ]
                    return json.dumps({"status": "success", "recommendations": recommendations})
            return json.dumps({"status": "error", "message": "未知函数"})
    
    agent = SimpleAgent()
    
    print(f"\n欢迎使用求职助手! 您的用户ID是: {USER_ID}")
    print("请分享您的求职相关信息，我将为您提供个性化建议。")
    print("输入'exit'退出，输入'recommendations'获取建议。")
    
    while True:
        # 获取用户输入
        user_input = input("\n您: ")
        
        if user_input.lower() == "exit":
            break
        
        if user_input.lower() == "recommendations":
            # 获取不同类型的建议
            print("\n正在生成求职建议...")
            
            # 获取一般建议
            general_result = await get_job_recommendations(agent, "general")
            if general_result.get("status") == "success":
                print("\n一般求职建议:")
                for rec in general_result.get("recommendations", []):
                    print(rec)
            
            # 获取简历建议
            resume_result = await get_job_recommendations(agent, "resume")
            if resume_result.get("status") == "success" and len(resume_result.get("recommendations", [])) > 1:
                print("\n简历建议:")
                for rec in resume_result.get("recommendations", []):
                    print(rec)
            
            # 获取面试建议
            interview_result = await get_job_recommendations(agent, "interview")
            if interview_result.get("status") == "success" and len(interview_result.get("recommendations", [])) > 1:
                print("\n面试建议:")
                for rec in interview_result.get("recommendations", []):
                    print(rec)
            
            continue
        
        # 处理用户消息
        result = await process_message(agent, user_input)
        
        if result.get("status") == "success":
            print("\n助手: 我已记录您的信息。有什么可以帮您的吗？")
        elif result.get("status") == "skipped":
            print("\n助手: 请分享更多关于您求职的信息，这样我才能更好地帮助您。")
        else:
            print(f"\n助手: 抱歉，处理您的信息时出现了问题: {result.get('message', '未知错误')}")

if __name__ == "__main__":
    asyncio.run(main())