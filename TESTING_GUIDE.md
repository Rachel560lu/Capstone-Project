# 测试指南 (Testing Guide)

本指南说明如何测试项目的各个阶段。

## 📋 前置要求

### 1. Python 环境
```bash
# 创建虚拟环境（推荐）
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# 或 .venv\Scripts\activate  # Windows
```

### 2. GPU 要求
- **推荐**: NVIDIA GPU with CUDA（用于 Stage 1 和 Stage 3）
- **可选**: CPU 模式（速度较慢）

---

## 🧪 Stage 1: 家具移除 (Clutter Removal)

### 安装依赖
```bash
# Stage 1 需要以下包（需要手动安装或从其他 requirements.txt 安装）
pip install torch torchvision diffusers transformers accelerate pillow opencv-python numpy
```

### 运行测试
```bash
cd "stage1_clutter removal"

# 1. 准备输入图片
# 将你的房间图片放在 input/room.jpeg

# 2. 运行脚本
python rcsd.py
```

**输入**: `input/room.jpeg`  
**输出**: `output/` 目录中的修复后图片

**注意**: 需要 GPU (CUDA) 支持，否则会很慢。

---

## 🪑 Stage 2: 家具选择和布局规划

### 安装依赖
```bash
cd "stage2_furniture selection"
pip install -r requirements.txt
```

### 运行测试
```bash
# 方法 1: 使用 run.py（推荐）
python run.py

# 方法 2: 使用 Jupyter Notebook
cd furniture_select
jupyter notebook stage.ipynb
```

### 配置参数（在 run.py 中修改）
```python
room_image = "inputs/empty_room.jpg"  # 空房间图片
budget_cny = 6000.0                   # 预算（人民币）
style = "modern"                       # 风格：modern, classic, etc.
room_type = "living room"             # 房间类型
room_size_m = (6.0, 5)                # 房间尺寸（米）
```

**输入**: 
- `inputs/empty_room.jpg` - 空房间图片
- `inputs/furniture.json` - 家具配置（可选）

**输出**: 
- `furniture_place/composed_room.jpg` - 布局后的房间草图
- `furniture_select/selection.json` - 选择的家具列表

---

## 🎨 Stage 3: 房间渲染 (Room Rendering)

### 安装依赖
```bash
cd "stage3_room rendering"

# Stage 3 需要的依赖
pip install torch torchvision diffusers transformers accelerate pillow opencv-python numpy
```

### 运行测试
```bash
python furnishing.py
```

**输入**:
- `Sample Data/empty_room.png` - 空房间图片（由 Stage 1 生成）
- `Sample Data/crude_image.png` - 带家具的草图（由 Stage 2 生成）

**输出**:
- `furnished_room.png` - 渲染后的房间
- `edge_map.png` - 边缘检测图

**注意**: 
1. 需要 GPU (CUDA) 支持
2. 代码中第 146-159 行有未完成的代码（`img2img_pipe` 未定义），可以注释掉或修复

### 修复 Stage 3 代码问题
`furnishing.py` 第 146-159 行有未定义的变量，可以：
1. **注释掉**（推荐用于快速测试）：
```python
# 注释掉第 143-159 行
```

2. **或者修复**（需要添加 img2img pipeline）

---

## 🌐 Front End: Web 界面

### 安装依赖

#### 前端 (React)
```bash
cd front_end
npm install
```

#### 后端 (Python)
```bash
cd front_end
pip install -r requirements.txt
```

### 运行测试

#### 1. 启动 Redis（必需）
```bash
# macOS (使用 Homebrew)
brew install redis
brew services start redis

# 或直接运行
redis-server

# Linux
sudo systemctl start redis
# 或
redis-server

# Windows
# 下载 Redis for Windows 并启动服务
```

#### 2. 启动后端 API 服务器
```bash
cd front_end
python api_server.py
```
服务器将在 `http://localhost:5001` 启动

#### 3. 启动 Worker 服务器（处理任务）
```bash
cd front_end
# 在另一个终端窗口
python worker_server.py
```

#### 4. 启动前端开发服务器
```bash
cd front_end
npm run dev
```
前端将在 `http://localhost:3000` 启动（或 Vite 显示的端口）

### 访问应用
打开浏览器访问: `http://localhost:3000`

---

## 🚀 完整流程测试

### 端到端测试流程

1. **Stage 1**: 移除家具
   ```bash
   cd "stage1_clutter removal"
   # 准备 input/room.jpeg
   python rcsd.py
   # 得到空房间图片
   ```

2. **Stage 2**: 选择和布局家具
   ```bash
   cd "stage2_furniture selection"
   # 将 Stage 1 的输出复制到 inputs/empty_room.jpg
   python run.py
   # 得到 composed_room.jpg
   ```

3. **Stage 3**: 渲染最终效果
   ```bash
   cd "stage3_room rendering"
   # 将 Stage 1 输出复制到 Sample Data/empty_room.png
   # 将 Stage 2 输出复制到 Sample Data/crude_image.png
   python furnishing.py
   # 得到 furnished_room.png
   ```

4. **Front End**: 使用 Web 界面
   - 启动所有服务（Redis, API Server, Worker, Frontend）
   - 在浏览器中上传图片并处理

---

## ⚠️ 常见问题

### 1. CUDA 错误
如果遇到 CUDA 相关错误：
```python
# 在代码中修改设备
pipe.to("cpu")  # 使用 CPU（会很慢）
# 或
pipe.to("cuda")  # 使用 GPU（需要 NVIDIA GPU）
```

### 2. 内存不足
- 减小图片尺寸
- 使用 CPU 模式（很慢）
- 减少 batch size

### 3. Redis 连接错误
确保 Redis 服务正在运行：
```bash
redis-cli ping
# 应该返回 PONG
```

### 4. 依赖冲突
建议为每个阶段使用独立的虚拟环境。

---

## 📝 快速测试命令总结

```bash
# 1. 环境准备
python -m venv .venv
source .venv/bin/activate

# 2. Stage 2 测试（最简单，不需要 GPU）
cd "stage2_furniture selection"
pip install -r requirements.txt
python run.py

# 3. Stage 3 测试（需要 GPU）
cd "stage3_room rendering"
pip install torch torchvision diffusers transformers accelerate pillow opencv-python numpy
python furnishing.py

# 4. Front End 测试
cd front_end
npm install
pip install -r requirements.txt
# 启动 Redis, API Server, Worker, Frontend
```

---

## 🔧 调试提示

1. **检查 GPU 是否可用**:
```python
import torch
print(torch.cuda.is_available())
```

2. **查看模型下载位置**:
```python
from transformers import file_utils
print(file_utils.default_cache_path)
```

3. **测试单个组件**:
- 先测试 Stage 2（最简单）
- 再测试 Stage 3（需要 GPU）
- 最后测试完整流程

---

祝测试顺利！🎉

