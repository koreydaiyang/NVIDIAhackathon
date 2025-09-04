// 登录页面JavaScript逻辑

class LoginManager {
    constructor() {
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadStoredUsers();
    }

    bindEvents() {
        // 表单切换
        document.getElementById('registerLink').addEventListener('click', (e) => {
            e.preventDefault();
            this.showRegisterForm();
        });

        document.getElementById('loginLink').addEventListener('click', (e) => {
            e.preventDefault();
            this.showLoginForm();
        });

        // 表单提交
        document.getElementById('loginForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleLogin();
        });

        document.getElementById('registerForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleRegister();
        });
    }

    showRegisterForm() {
        document.getElementById('loginForm').classList.add('hidden');
        document.getElementById('registerForm').classList.remove('hidden');
        document.querySelector('.login-header h1').textContent = '注册账户';
        document.querySelector('.login-header p').textContent = '创建您的个人求职助手账户';
    }

    showLoginForm() {
        document.getElementById('registerForm').classList.add('hidden');
        document.getElementById('loginForm').classList.remove('hidden');
        document.querySelector('.login-header h1').textContent = '求职助手';
        document.querySelector('.login-header p').textContent = '您的个人化AI求职顾问';
    }

    loadStoredUsers() {
        // 从localStorage加载用户数据
        const users = localStorage.getItem('jobAssistantUsers');
        if (!users) {
            localStorage.setItem('jobAssistantUsers', JSON.stringify({}));
        }
    }

    getStoredUsers() {
        return JSON.parse(localStorage.getItem('jobAssistantUsers') || '{}');
    }

    saveUser(username, password) {
        const users = this.getStoredUsers();
        users[username] = {
            password: this.hashPassword(password),
            createdAt: new Date().toISOString(),
            lastLogin: null,
            memoryData: {}
        };
        localStorage.setItem('jobAssistantUsers', JSON.stringify(users));
    }

    // API基础URL
    getApiBase() {
        return 'http://localhost:8001/api';
    }

    // 发送API请求的辅助函数
    async apiRequest(endpoint, method = 'GET', data = null) {
        const options = {
            method,
            headers: {
                'Content-Type': 'application/json',
            },
        };
        
        // 添加认证头
        const token = localStorage.getItem('sessionToken');
        if (token) {
            options.headers['Authorization'] = `Bearer ${token}`;
        }
        
        if (data) {
            options.body = JSON.stringify(data);
        }
        
        try {
            const response = await fetch(`${this.getApiBase()}${endpoint}`, options);
            const result = await response.json();
            
            if (!response.ok) {
                throw new Error(result.error || '请求失败');
            }
            
            return result;
        } catch (error) {
            console.error('API请求错误:', error);
            throw error;
        }
    }

    validateUser(username, password) {
        const users = this.getStoredUsers();
        const user = users[username];
        if (!user) return false;
        return user.password === this.hashPassword(password);
    }

    updateLastLogin(username) {
        const users = this.getStoredUsers();
        if (users[username]) {
            users[username].lastLogin = new Date().toISOString();
            localStorage.setItem('jobAssistantUsers', JSON.stringify(users));
        }
    }

    async handleLogin() {
        const username = document.getElementById('username').value.trim();
        const password = document.getElementById('password').value;

        if (!username || !password) {
            this.showNotification('请填写完整的登录信息', 'error');
            return;
        }

        try {
            const result = await this.apiRequest('/login', 'POST', {
                username,
                password
            });
            
            // 保存会话令牌和用户信息
            localStorage.setItem('sessionToken', result.session_token);
            localStorage.setItem('currentUser', JSON.stringify({
                username: result.username,
                loginTime: new Date().toISOString()
            }));
            
            this.showNotification('登录成功！正在跳转...', 'success');
            
            // 延迟跳转到主页面
            setTimeout(() => {
                window.location.href = 'dashboard.html';
            }, 1500);
        } catch (error) {
            this.showNotification(error.message, 'error');
        }
    }

    async handleRegister() {
        const username = document.getElementById('regUsername').value.trim();
        const password = document.getElementById('regPassword').value;
        const confirmPassword = document.getElementById('confirmPassword').value;

        if (!username || !password || !confirmPassword) {
            this.showNotification('请填写完整的注册信息', 'error');
            return;
        }

        if (username.length < 3) {
            this.showNotification('用户名至少需要3个字符', 'error');
            return;
        }

        if (password.length < 6) {
            this.showNotification('密码至少需要6个字符', 'error');
            return;
        }

        if (password !== confirmPassword) {
            this.showNotification('两次输入的密码不一致', 'error');
            return;
        }

        try {
            const result = await this.apiRequest('/register', 'POST', {
                username,
                password
            });
            
            this.showNotification('注册成功！请登录', 'success');
            
            // 清空表单并切换到登录
            document.getElementById('registerForm').reset();
            setTimeout(() => {
                this.showLoginForm();
            }, 1500);
        } catch (error) {
            this.showNotification(error.message, 'error');
        }
    }

    setCurrentUser(username) {
        sessionStorage.setItem('currentUser', username);
    }

    getCurrentUser() {
        return sessionStorage.getItem('currentUser');
    }

    showNotification(message, type) {
        const notification = document.getElementById('notification');
        notification.textContent = message;
        notification.className = `notification ${type} show`;
        
        setTimeout(() => {
            notification.classList.remove('show');
        }, 3000);
    }

    // 验证会话
    async validateSession() {
        try {
            const result = await this.apiRequest('/validate');
            return result.username;
        } catch (error) {
            // 会话无效，清除本地存储
            localStorage.removeItem('sessionToken');
            localStorage.removeItem('currentUser');
            return null;
        }
    }

    // 登出
    async logout() {
        try {
            await this.apiRequest('/logout', 'POST');
        } catch (error) {
            console.error('登出错误:', error);
        } finally {
            // 清除本地存储
            localStorage.removeItem('sessionToken');
            localStorage.removeItem('currentUser');
            window.location.href = 'login.html';
        }
    }

    // 导出用户数据
    async exportUserData() {
        try {
            const result = await this.apiRequest('/export');
            
            // 创建下载链接
            const blob = new Blob([JSON.stringify(result, null, 2)], {
                type: 'application/json'
            });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `user_data_${new Date().toISOString().split('T')[0]}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            
            this.showNotification('数据导出成功！', 'success');
        } catch (error) {
            this.showNotification('导出失败: ' + error.message, 'error');
        }
    }
}

// 初始化登录管理器
const loginManager = new LoginManager();

// 全局函数，供其他页面使用
window.LoginManager = LoginManager;
window.loginManager = loginManager;