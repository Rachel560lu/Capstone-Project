# FastAPI 后端使用说明

## 项目结构

```
front_end/
├── backend.py              # FastAPI 主应用
├── image_processor.py      # 图像处理模块（封装 rcsd.py 逻辑）
├── rcsd.py                 # 原始图像处理脚本
├── requirements.txt        # Python 依赖
├── start_backend.sh        # Linux/Mac 启动脚本
└── start_backend.bat       # Windows 启动脚本
```

## 安装依赖

```bash
pip install -r requirements.txt
```

## 启动后端服务

### Linux/Mac:
```bash
./start_backend.sh
# 或
python backend.py
```

### Windows:
```cmd
start_backend.bat
# 或
python backend.py
```

服务将在 `http://localhost:5000` 启动。

## API 接口

### 1. 健康检查
```
GET /health
```

返回服务状态和 GPU 可用性。

### 2. 处理图片
```
POST /process-image
Content-Type: multipart/form-data

参数:
- image: 图片文件（支持拖放或选择）
```

返回:
```json
{
  "success": true,
  "original_url": "/uploads/{filename}",
  "processed_url": "/output/{filename}",
  "message": "图片处理完成"
}
```

### 3. 获取原始图片
```
GET /uploads/{filename}
```

### 4. 获取处理后的图片
```
GET /output/{filename}
```

## API 文档

启动服务后，访问以下地址查看自动生成的 API 文档：

- Swagger UI: http://localhost:5000/docs
- ReDoc: http://localhost:5000/redoc

## 图像处理流程

1. **接收上传的图片** - 保存到 `uploads/` 目录
2. **语义分割** - 使用 SegFormer 模型识别房间结构
3. **生成 Mask** - 识别非结构元素（家具等）
4. **图像修复** - 使用 Stable Diffusion Inpainting 移除家具
5. **迭代优化** - 最多迭代 10 次，直到没有非结构元素
6. **返回结果** - 保存到 `output/` 目录并返回 URL

## 配置参数

在 `image_processor.py` 中可以调整以下参数：

- `MAX_ITER`: 最大迭代次数（默认 10）
- `STRUCTURE_CLASSES`: 保留的结构类（墙、地板、天花板等）
- `OTHER_EXPAND`: Mask 扩展像素数

## 注意事项

1. **GPU 要求**: 推荐使用 NVIDIA GPU 加速，CPU 模式会非常慢
2. **内存要求**: 至少需要 8GB 显存（GPU）或 16GB 内存（CPU）
3. **首次运行**: 首次运行会下载模型文件，需要较长时间
4. **处理时间**: 每张图片处理时间约 1-5 分钟（取决于 GPU 性能）

## 故障排除

### 模型加载失败
- 检查网络连接（需要下载模型）
- 确保有足够的磁盘空间（模型文件约 10GB+）

### GPU 不可用
- 检查 CUDA 是否正确安装
- 检查 PyTorch 是否支持 CUDA
- 系统会自动降级到 CPU 模式（较慢）

### 内存不足
- 减少 `MAX_ITER` 参数
- 使用较小的图片尺寸
- 关闭其他占用显存的程序




