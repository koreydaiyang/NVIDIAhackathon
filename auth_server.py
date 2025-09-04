#!/usr/bin/env python3
"""
用户认证和会话管理服务器

提供用户注册、登录、会话管理和数据存储功能
"""

import json
import os
import hashlib
import secrets
import time
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from typing import Optional
import threading
import uuid

class UserManager:
    def __init__(self, data_dir="user_data"):
        self.data_dir = data_dir
        self.users_file = os.path.join(data_dir, "users.json")
        self.sessions_file = os.path.join(data_dir, "sessions.json")
        self.memory_dir = os.path.join(data_dir, "memory")
        
        # 确保目录存在
        os.makedirs(data_dir, exist_ok=True)
        os.makedirs(self.memory_dir, exist_ok=True)
        
        # 加载数据
        self.users = self.load_users()
        self.sessions = self.load_sessions()
        
        # 清理过期会话
        self.cleanup_expired_sessions()
    
    def load_users(self):
        """加载用户数据"""
        if os.path.exists(self.users_file):
            try:
                with open(self.users_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def save_users(self):
        """保存用户数据"""
        with open(self.users_file, 'w', encoding='utf-8') as f:
            json.dump(self.users, f, ensure_ascii=False, indent=2)
    
    def load_sessions(self):
        """加载会话数据"""
        if os.path.exists(self.sessions_file):
            try:
                with open(self.sessions_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def save_sessions(self):
        """保存会话数据"""
        with open(self.sessions_file, 'w', encoding='utf-8') as f:
            json.dump(self.sessions, f, ensure_ascii=False, indent=2)
    
    def hash_password(self, password):
        """密码哈希"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def generate_session_token(self):
        """生成会话令牌"""
        return secrets.token_urlsafe(32)
    
    def register_user(self, username, password):
        """注册用户"""
        if username in self.users:
            return {"success": False, "message": "用户名已存在"}
        
        if len(username) < 3:
            return {"success": False, "message": "用户名至少需要3个字符"}
        
        if len(password) < 6:
            return {"success": False, "message": "密码至少需要6个字符"}
        
        user_id = str(uuid.uuid4())
        self.users[username] = {
            "user_id": user_id,
            "password_hash": self.hash_password(password),
            "created_at": datetime.now().isoformat(),
            "last_login": None
        }
        
        # 创建用户专属的memory目录
        user_memory_dir = os.path.join(self.memory_dir, user_id)
        os.makedirs(user_memory_dir, exist_ok=True)
        
        self.save_users()
        return {"success": True, "message": "注册成功"}
    
    def login_user(self, username, password):
        """用户登录"""
        if username not in self.users:
            return {"success": False, "message": "用户名或密码错误"}
        
        user = self.users[username]
        if user["password_hash"] != self.hash_password(password):
            return {"success": False, "message": "用户名或密码错误"}
        
        # 创建会话
        session_token = self.generate_session_token()
        from datetime import timedelta
        expires_at = (datetime.now() + timedelta(days=7)).isoformat()
        
        self.sessions[session_token] = {
            "username": username,
            "user_id": user["user_id"],
            "created_at": datetime.now().isoformat(),
            "expires_at": expires_at
        }
        
        # 更新最后登录时间
        self.users[username]["last_login"] = datetime.now().isoformat()
        
        self.save_users()
        self.save_sessions()
        
        return {
            "success": True, 
            "message": "登录成功",
            "session_token": session_token,
            "user_id": user["user_id"],
            "expires_at": expires_at
        }
    
    def validate_session(self, session_token):
        """验证会话"""
        if session_token not in self.sessions:
            return None
        
        session = self.sessions[session_token]
        expires_at = datetime.fromisoformat(session["expires_at"])
        
        if datetime.now() > expires_at:
            # 会话已过期
            del self.sessions[session_token]
            self.save_sessions()
            return None
        
        return session
    
    def logout_user(self, session_token):
        """用户登出"""
        if session_token in self.sessions:
            del self.sessions[session_token]
            self.save_sessions()
            return {"success": True, "message": "登出成功"}
        return {"success": False, "message": "无效的会话"}
    
    def cleanup_expired_sessions(self):
        """清理过期会话"""
        now = datetime.now()
        expired_tokens = []
        
        for token, session in self.sessions.items():
            expires_at = datetime.fromisoformat(session["expires_at"])
            if now > expires_at:
                expired_tokens.append(token)
        
        for token in expired_tokens:
            del self.sessions[token]
        
        if expired_tokens:
            self.save_sessions()
    
    def get_user_memory_path(self, user_id):
        """获取用户memory存储路径"""
        return os.path.join(self.memory_dir, user_id)
    
    def export_user_data(self, username):
        """导出用户数据"""
        if username not in self.users:
            return None
        
        user = self.users[username]
        user_id = user["user_id"]
        memory_path = self.get_user_memory_path(user_id)
        
        # 收集memory数据
        memory_data = {}
        if os.path.exists(memory_path):
            for filename in os.listdir(memory_path):
                if filename.endswith('.json'):
                    file_path = os.path.join(memory_path, filename)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            memory_data[filename] = json.load(f)
                    except:
                        continue
        
        export_data = {
            "username": username,
            "user_id": user_id,
            "created_at": user["created_at"],
            "last_login": user["last_login"],
            "memory_data": memory_data,
            "exported_at": datetime.now().isoformat()
        }
        
        return export_data

class AuthHandler(BaseHTTPRequestHandler):
    user_manager: Optional['UserManager'] = None
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def _send_error(self, status_code, message):
        """发送错误响应"""
        self.send_json_response({"error": message}, status_code)
    
    def do_OPTIONS(self):
        """处理CORS预检请求"""
        self.send_response(200)
        self.send_cors_headers()
        self.end_headers()
    
    def send_cors_headers(self):
        """发送CORS头"""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
    
    def send_json_response(self, data, status_code=200):
        """发送JSON响应"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
    
    def do_POST(self):
        """处理POST请求"""
        try:
            if not self.user_manager:
                self._send_error(500, "Server not properly initialized")
                return
                
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            path = urlparse(self.path).path
            
            if path == '/api/register':
                result = self.user_manager.register_user(
                    data.get('username', ''),
                    data.get('password', '')
                )
                self.send_json_response(result)
            
            elif path == '/api/login':
                result = self.user_manager.login_user(
                    data.get('username', ''),
                    data.get('password', '')
                )
                self.send_json_response(result)
            
            elif path == '/api/logout':
                session_token = data.get('session_token', '')
                result = self.user_manager.logout_user(session_token)
                self.send_json_response(result)
            
            elif path == '/api/set_user':
                self._handle_set_user()
            
            else:
                self.send_json_response({"error": "未找到接口"}, 404)
        
        except Exception as e:
            self.send_json_response({"error": str(e)}, 500)
    
    def _handle_set_user(self):
        """处理设置当前用户请求"""
        try:
            if not self.__class__.user_manager:
                self.send_json_response({"error": "用户管理器未初始化"}, 500)
                return
                
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            # 从Authorization头或POST数据获取session_token
            auth_header = self.headers.get('Authorization', '')
            if auth_header.startswith('Bearer '):
                session_token = auth_header[7:]  # 移除'Bearer '前缀
            else:
                session_token = data.get('session_token')
                
            if not session_token:
                self.send_json_response({"error": "缺少会话令牌"}, 400)
                return
            
            session = self.__class__.user_manager.validate_session(session_token)
            if not session:
                self.send_json_response({"error": "无效的会话"}, 401)
                return
            
            # 简化版本：直接返回用户信息，不与Memory MCP服务器通信
            # 在实际部署时，可以添加与Memory服务器的通信逻辑
            self.send_json_response({
                "success": True,
                "user_id": session["user_id"],
                "username": session["username"],
                "message": "用户设置成功"
            })
                
        except Exception as e:
            print(f"设置用户时出错: {e}")
            self.send_json_response({"error": "设置用户失败"}, 500)
    
    def do_GET(self):
        """处理GET请求"""
        try:
            if not self.user_manager:
                self._send_error(500, "Server not properly initialized")
                return
                
            parsed_url = urlparse(self.path)
            path = parsed_url.path
            query_params = parse_qs(parsed_url.query)
            
            if path == '/api/validate':
                # 从Authorization头或查询参数获取session_token
                auth_header = self.headers.get('Authorization', '')
                if auth_header.startswith('Bearer '):
                    session_token = auth_header[7:]  # 移除'Bearer '前缀
                else:
                    session_token = query_params.get('session_token', [''])[0]
                session = self.user_manager.validate_session(session_token)
                
                if session:
                    self.send_json_response({
                        "valid": True,
                        "username": session["username"],
                        "user_id": session["user_id"]
                    })
                else:
                    self.send_json_response({"valid": False}, 401)
            
            elif path == '/api/export':
                # 从Authorization头或查询参数获取session_token
                auth_header = self.headers.get('Authorization', '')
                if auth_header.startswith('Bearer '):
                    session_token = auth_header[7:]  # 移除'Bearer '前缀
                else:
                    session_token = query_params.get('session_token', [''])[0]
                session = self.user_manager.validate_session(session_token)
                
                if not session:
                    self.send_json_response({"error": "无效的会话"}, 401)
                    return
                
                export_data = self.user_manager.export_user_data(session["username"])
                if export_data:
                    self.send_json_response(export_data)
                else:
                    self.send_json_response({"error": "导出失败"}, 500)
            
            elif path == '/api/set_user':
                self._handle_set_user()
            
            else:
                self.send_json_response({"error": "未找到接口"}, 404)
        
        except Exception as e:
            self.send_json_response({"error": str(e)}, 500)

def create_auth_server(port=8001):
    """创建认证服务器"""
    user_manager = UserManager()
    
    # 设置类变量
    AuthHandler.user_manager = user_manager
    
    server = HTTPServer(('localhost', port), AuthHandler)
    return server, user_manager

def main():
    """主函数"""
    port = 8001
    server, user_manager = create_auth_server(port)
    
    print(f"认证服务器启动在 http://localhost:{port}")
    print("可用的API接口:")
    print("  POST /api/register - 用户注册")
    print("  POST /api/login - 用户登录")
    print("  POST /api/logout - 用户登出")
    print("  GET /api/validate - 验证会话")
    print("  GET /api/export - 导出用户数据")
    print("\n按 Ctrl+C 停止服务器")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n正在关闭服务器...")
        server.shutdown()
        server.server_close()

if __name__ == "__main__":
    main()