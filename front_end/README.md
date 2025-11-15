# 房产视觉增强系统 - React版本

这是一个基于 React 的房产视觉增强系统前端应用。

## 项目结构

```
front_end/
├── src/
│   ├── components/          # React 组件
│   │   ├── MandalaBackground.jsx
│   │   ├── RoleSelection.jsx
│   │   ├── UploadSection.jsx
│   │   ├── ComparisonViewer.jsx
│   │   ├── FeaturesSection.jsx
│   │   ├── TutorialSection.jsx
│   │   ├── LoadingOverlay.jsx
│   │   └── ErrorMessage.jsx
│   ├── styles/              # 样式文件
│   │   └── App.css
│   ├── App.jsx              # 主应用组件
│   └── main.jsx             # 入口文件
├── index.html               # HTML 模板
├── package.json             # 项目配置
├── vite.config.js           # Vite 配置
└── README.md                # 说明文档
```

## 安装依赖

```bash
npm install
```

## 运行开发服务器

```bash
npm run dev
```

应用将在 `http://localhost:3000` 启动。

## 构建生产版本

```bash
npm run build
```

## 预览生产构建

```bash
npm run preview
```

## 后端服务

### API Server (主后端服务)

FastAPI 后端服务，处理前端请求和任务队列管理（默认端口 5001）：

```bash
python api_server.py
```

或使用启动脚本：
- Linux/Mac: `./start_backend.sh`
- Windows: `start_backend.bat`

### Worker Server (任务处理服务)

Worker 服务器，从 Redis 队列读取任务并处理（默认端口 5002）：

```bash
python worker_server.py
```

或使用启动脚本：
- Linux/Mac: `./start_worker.sh`
- Windows: `start_worker.bat`

**重要提示：**
1. 确保 Redis 服务已启动（默认端口 6379）
2. 先启动 API Server，再启动 Worker Server
3. Worker Server 会持续监听 Redis 队列，处理任务并更新结果

### 系统架构

```
前端 (React) 
    ↓
API Server (FastAPI) 
    ↓
Redis 消息队列
    ↓
Worker Server (任务处理)
    ↓
Redis (更新任务结果)
    ↓
API Server (返回结果给前端)
```

## 功能特性

- ✅ 角色选择（卖房者/买房者）
- ✅ 图片上传（支持拖放）
- ✅ 图片处理与对比查看
- ✅ 响应式设计
- ✅ 加载状态提示
- ✅ 错误处理

## 技术栈

- React 18
- Vite
- CSS3 (动画、渐变、响应式)



