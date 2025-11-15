# Redis 安装与启动指南

## 检查 Redis 是否已安装

### macOS / Linux
```bash
redis-cli --version
# 或
which redis-server
```

### Windows
```cmd
redis-cli --version
```

## 安装 Redis

### macOS (使用 Homebrew)
```bash
# 安装 Redis
brew install redis

# 启动 Redis 服务（前台运行）
redis-server

# 或作为后台服务启动（开机自启）
brew services start redis
```

### Linux (Ubuntu/Debian)
```bash
# 更新包列表
sudo apt update

# 安装 Redis
sudo apt install redis-server

# 启动 Redis 服务
sudo systemctl start redis-server

# 设置开机自启
sudo systemctl enable redis-server

# 检查状态
sudo systemctl status redis-server
```

### Linux (CentOS/RHEL)
```bash
# 安装 EPEL 仓库（如果还没有）
sudo yum install epel-release

# 安装 Redis
sudo yum install redis

# 启动 Redis 服务
sudo systemctl start redis

# 设置开机自启
sudo systemctl enable redis
```

### Windows

#### 方法 1: 使用 WSL (推荐)
```bash
# 在 WSL (Ubuntu) 中安装
sudo apt update
sudo apt install redis-server
sudo service redis-server start
```

#### 方法 2: 使用 Memurai (Redis for Windows)
1. 下载 Memurai: https://www.memurai.com/
2. 安装并启动服务

#### 方法 3: 使用 Docker
```bash
docker run -d -p 6379:6379 --name redis redis:latest
```

## 启动 Redis 服务

### 方法 1: 前台运行（开发测试）
```bash
redis-server
```

### 方法 2: 后台运行（生产环境）

#### macOS
```bash
# 使用 Homebrew 服务管理
brew services start redis

# 或手动后台运行
redis-server --daemonize yes
```

#### Linux
```bash
# 使用 systemd
sudo systemctl start redis-server

# 或手动后台运行
redis-server --daemonize yes
```

#### Windows (WSL)
```bash
sudo service redis-server start
```

## 验证 Redis 是否运行

### 测试连接
```bash
redis-cli ping
# 应该返回: PONG
```

### 查看 Redis 信息
```bash
redis-cli info
```

### 查看 Redis 状态（Linux）
```bash
sudo systemctl status redis-server
```

## 停止 Redis 服务

### macOS
```bash
# 如果使用 Homebrew 服务
brew services stop redis

# 或使用 redis-cli
redis-cli shutdown
```

### Linux
```bash
# 使用 systemd
sudo systemctl stop redis-server

# 或使用 redis-cli
redis-cli shutdown
```

### Windows (WSL)
```bash
sudo service redis-server stop
```

## 配置 Redis（可选）

### 查看配置文件位置
```bash
redis-cli CONFIG GET dir
```

### 编辑配置文件

#### macOS / Linux
```bash
# 通常位置: /usr/local/etc/redis.conf 或 /etc/redis/redis.conf
sudo nano /usr/local/etc/redis.conf
```

#### 常用配置项
```conf
# 绑定地址（默认只允许本地连接）
bind 127.0.0.1

# 端口（默认 6379）
port 6379

# 密码（可选，生产环境建议设置）
# requirepass your_password

# 持久化
save 900 1
save 300 10
save 60 10000
```

### 使用自定义配置文件启动
```bash
redis-server /path/to/redis.conf
```

## 常用 Redis 命令

```bash
# 连接到 Redis
redis-cli

# 查看所有键
KEYS *

# 查看队列长度
LLEN task_queue:denoise
LLEN task_queue:virtual

# 查看队列内容（不移除）
LRANGE task_queue:denoise 0 -1

# 清空所有数据（谨慎使用！）
FLUSHALL

# 退出
exit
```

## 故障排查

### 问题 1: 端口被占用
```bash
# 查看端口占用
lsof -i :6379  # macOS / Linux
netstat -ano | findstr :6379  # Windows

# 修改 Redis 端口
redis-server --port 6380
```

### 问题 2: 连接被拒绝
- 检查 Redis 是否正在运行: `redis-cli ping`
- 检查防火墙设置
- 检查 Redis 配置文件中的 `bind` 设置

### 问题 3: 权限问题
```bash
# Linux 可能需要 sudo
sudo redis-server

# 或修改 Redis 数据目录权限
sudo chown -R redis:redis /var/lib/redis
```

## 快速启动脚本

### macOS / Linux
创建 `start_redis.sh`:
```bash
#!/bin/bash
if ! redis-cli ping &> /dev/null; then
    echo "启动 Redis 服务..."
    redis-server --daemonize yes
    sleep 1
    if redis-cli ping &> /dev/null; then
        echo "✓ Redis 启动成功"
    else
        echo "✗ Redis 启动失败"
    fi
else
    echo "✓ Redis 已在运行"
fi
```

### Windows
创建 `start_redis.bat`:
```batch
@echo off
redis-cli ping >nul 2>&1
if errorlevel 1 (
    echo 启动 Redis 服务...
    redis-server --daemonize yes
    timeout /t 1 >nul
    redis-cli ping >nul 2>&1
    if errorlevel 1 (
        echo Redis 启动失败
    ) else (
        echo Redis 启动成功
    )
) else (
    echo Redis 已在运行
)
pause
```

## 项目中的 Redis 配置

本项目使用以下默认配置：
- **Host**: localhost
- **Port**: 6379
- **DB**: 0

可以通过环境变量修改：
```bash
export REDIS_HOST=localhost
export REDIS_PORT=6379
export REDIS_DB=0
```

## 下一步

1. ✅ 确保 Redis 服务已启动
2. ✅ 启动 API Server: `python api_server.py`
3. ✅ 启动 Worker Server: `python worker_server.py`
4. ✅ 启动前端: `npm run dev`

现在你的系统已经可以完整运行了！

