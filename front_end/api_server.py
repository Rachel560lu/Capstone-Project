from fastapi import FastAPI, File, UploadFile, HTTPException, Form, Body, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import uuid
import io
import json
from PIL import Image
import uvicorn
from pathlib import Path
import redis
from typing import Optional
from datetime import datetime
from pydantic import BaseModel
import shutil
import asyncio
from starlette.responses import FileResponse as StarletteFileResponse

app = FastAPI(title="房产视觉增强系统 API", version="2.0.0")

# 配置 CORS - 允许所有来源（开发环境）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源
    allow_credentials=False,  # 当使用 "*" 时，credentials 必须为 False
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# 目录配置
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'output'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# 注意：不再使用 app.mount()，而是使用显式的路由处理器（见下面的 /uploads/{filename} 和 /output/{filename}）
# 这样可以确保 CORS 头正确应用

# Redis 配置
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))
REDIS_QUEUE_PREFIX = "task_queue:"
TASK_STORAGE_PREFIX = "task_storage:"

# 用于存储任务信息的字典（如果 Redis 不可用，使用内存存储）
task_storage = {}

# 初始化 Redis 连接
try:
    redis_client = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=REDIS_DB,
        decode_responses=True,
        socket_connect_timeout=5
    )
    # 测试连接
    redis_client.ping()
    print(f"✓ Redis 连接成功: {REDIS_HOST}:{REDIS_PORT}")
except Exception as e:
    print(f"⚠ Redis 连接失败: {e}")
    print("⚠ 将使用模拟模式（不发送到队列）")
    redis_client = None


@app.get("/")
async def root():
    return {
        "message": "房产视觉增强系统 API",
        "version": "2.0.0",
        "status": "running",
        "redis_connected": redis_client is not None
    }


@app.get("/health")
async def health_check():
    redis_status = False
    if redis_client:
        try:
            redis_client.ping()
            redis_status = True
        except:
            pass
    
    return {
        "status": "healthy",
        "redis_connected": redis_status,
        "redis_host": REDIS_HOST,
        "redis_port": REDIS_PORT
    }


def store_task_info(task_id: str, task_data: dict) -> bool:
    """
    存储任务信息到 Redis 或内存
    
    Args:
        task_id: 任务ID
        task_data: 任务数据字典
    
    Returns:
        bool: 是否成功存储
    """
    if redis_client:
        try:
            key = f"{TASK_STORAGE_PREFIX}{task_id}"
            task_json = json.dumps(task_data, ensure_ascii=False)
            redis_client.setex(key, 3600, task_json)  # 存储1小时
            return True
        except Exception as e:
            print(f"✗ 存储任务信息到 Redis 失败: {e}")
            # 降级到内存存储
            task_storage[task_id] = task_data
            return True
    else:
        # 使用内存存储
        task_storage[task_id] = task_data
        return True


def get_task_info(task_id: str) -> Optional[dict]:
    """
    从 Redis 或内存获取任务信息
    
    Args:
        task_id: 任务ID
    
    Returns:
        dict: 任务数据，如果不存在返回 None
    """
    if redis_client:
        try:
            key = f"{TASK_STORAGE_PREFIX}{task_id}"
            task_json = redis_client.get(key)
            if task_json:
                return json.loads(task_json)
        except Exception as e:
            print(f"✗ 从 Redis 获取任务信息失败: {e}")
    
    # 从内存获取
    return task_storage.get(task_id)


def send_task_to_redis(task_type: str, task_data: dict) -> bool:
    """
    将任务发送到 Redis 消息队列
    
    Args:
        task_type: 任务类型 ('denoise' 或 'virtual')
        task_data: 任务数据字典
    
    Returns:
        bool: 是否成功发送
    """
    if not redis_client:
        print(f"[模拟模式] 任务已创建: {task_type} - {task_data.get('task_id')}")
        return False
    
    try:
        queue_name = f"{REDIS_QUEUE_PREFIX}{task_type}"
        task_json = json.dumps(task_data, ensure_ascii=False)
        redis_client.lpush(queue_name, task_json)
        print(f"✓ 任务已发送到队列 {queue_name}: {task_data.get('task_id')}")
        return True
    except Exception as e:
        print(f"✗ 发送任务到 Redis 失败: {e}")
        return False


@app.post("/upload-image")
async def upload_image(
    image: UploadFile = File(...),
    task_type: str = Form(...)
):
    """
    上传图片（仅上传，不处理）
    
    支持的任务类型:
    - denoise: AI高清放大与去杂
    - virtual: 虚拟布置
    
    流程:
    1. 接收图片并保存
    2. 生成任务ID并存储任务信息
    3. 立即返回图片 URL 和任务ID供前端展示
    """
    try:
        # 验证任务类型
        if task_type not in ['denoise', 'virtual']:
            raise HTTPException(
                status_code=400,
                detail=f"无效的任务类型: {task_type}。支持的类型: denoise, virtual"
            )
        
        # 验证文件类型
        if not image.content_type or not image.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="请上传图片文件")
        
        # 生成唯一任务 ID
        task_id = str(uuid.uuid4())
        original_filename = f"{task_id}_original.png"
        original_path = os.path.join(UPLOAD_FOLDER, original_filename)
        
        # 保存原始图片
        image_data = await image.read()
        img = Image.open(io.BytesIO(image_data))
        if img.mode != 'RGB':
            img = img.convert('RGB')
        img.save(original_path, 'PNG')
        
        # 获取图片信息
        image_width, image_height = img.size
        
        # 构建任务数据（不发送到队列，只存储）
        task_data = {
            "task_id": task_id,
            "task_type": task_type,
            "original_filename": original_filename,
            "original_path": original_path,
            "original_url": f"/uploads/{original_filename}",
            "image_width": image_width,
            "image_height": image_height,
            "created_at": datetime.now().isoformat(),
            "status": "uploaded"  # 状态为已上传，未处理
        }
        
        # 根据任务类型添加特定参数
        if task_type == 'denoise':
            task_data["description"] = "AI高清放大与去杂处理"
        elif task_type == 'virtual':
            task_data["description"] = "虚拟布置处理"
        
        # 存储任务信息（不发送到队列）
        store_task_info(task_id, task_data)
        
        # 立即返回结果，让前端可以展示上传的图片
        return JSONResponse({
            "success": True,
            "task_id": task_id,
            "task_type": task_type,
            "original_url": f"/uploads/{original_filename}",
            "message": "图片上传成功",
            "status": "uploaded"
        })
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")


class ProcessTaskRequest(BaseModel):
    task_id: str
    task_type: str
    decoration_style: Optional[str] = None
    max_price: Optional[int] = None
    room_type: Optional[str] = None


@app.post("/process-task")
async def process_task(request: ProcessTaskRequest = Body(...)):
    """
    触发任务处理（将任务发送到 Redis 消息队列）
    
    请求体:
    - task_id: 任务ID（必需）
    - task_type: 任务类型 ('denoise' 或 'virtual')（必需）
    - decoration_style: 装修风格（仅virtual任务，可选）
    - max_price: 最高预算（仅virtual任务，可选）
    - room_type: 房间类型（仅virtual任务，可选）
    
    流程:
    1. 根据 task_id 获取任务信息
    2. 添加任务特定参数到任务数据
    3. 将任务发送到 Redis 消息队列
    4. 更新任务状态
    """
    try:
        task_id = request.task_id
        task_type = request.task_type
        
        # 验证任务类型
        if task_type not in ['denoise', 'virtual']:
            raise HTTPException(
                status_code=400,
                detail=f"无效的任务类型: {task_type}。支持的类型: denoise, virtual"
            )
        
        # 获取任务信息
        task_data = get_task_info(task_id)
        if not task_data:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        # 验证任务类型是否匹配
        if task_data.get('task_type') != task_type:
            raise HTTPException(status_code=400, detail="任务类型不匹配")
        
        # 更新任务状态
        task_data["status"] = "queued"
        task_data["queued_at"] = datetime.now().isoformat()
        
        # 根据任务类型添加特定参数
        if task_type == 'denoise':
            task_data["description"] = "AI高清放大与去杂处理"
        elif task_type == 'virtual':
            task_data["description"] = "虚拟布置处理"
            # 添加虚拟布置的特定参数（确保所有参数都被传递，即使为None）
            task_data["decoration_style"] = request.decoration_style
            task_data["max_price"] = request.max_price
            task_data["room_type"] = request.room_type
            
            # 打印参数信息用于调试
            print(f"虚拟布置任务参数: decoration_style={request.decoration_style}, "
                  f"max_price={request.max_price}, room_type={request.room_type}")
        
        # 打印完整的任务数据用于调试
        print(f"发送到Redis队列的任务数据: {json.dumps(task_data, ensure_ascii=False, indent=2)}")
        
        # 发送任务到 Redis 消息队列
        send_success = send_task_to_redis(task_type, task_data)
        
        # 更新存储的任务信息
        store_task_info(task_id, task_data)
        
        return JSONResponse({
            "success": True,
            "task_id": task_id,
            "task_type": task_type,
            "message": f"{task_data['description']}任务已加入队列",
            "status": "queued",
            "redis_sent": send_success,
            "task_params": task_data if task_type == 'virtual' else None  # 返回任务参数用于确认
        })
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")


@app.get("/task/{task_id}")
async def get_task_status(task_id: str):
    """
    查询任务状态（可选功能，用于后续轮询任务处理结果）
    """
    # 这里可以扩展实现任务状态查询
    # 例如从 Redis 或数据库中查询任务处理状态
    return {
        "task_id": task_id,
        "status": "pending",
        "message": "任务状态查询功能待实现"
    }


async def simulate_task_processing(task_id: str, task_type: str):
    """
    模拟任务处理（实际应该从Redis队列读取并处理）
    这里模拟处理过程，使用示例图片作为结果
    """
    await asyncio.sleep(3)  # 模拟处理时间
    
    # 获取任务信息
    task_data = get_task_info(task_id)
    if not task_data:
        return
    
    # 更新任务状态为处理中
    task_data["status"] = "processing"
    store_task_info(task_id, task_data)
    
    # 模拟处理：复制示例图片作为处理结果
    # 实际应该从Redis队列读取任务，进行AI处理，然后保存结果
    try:
        if task_type == 'denoise':
            # 使用示例图片作为处理结果
            example_image_path = os.path.join('example', 'empty_room.jpg')
            if os.path.exists(example_image_path):
                processed_filename = f"{task_id}_processed.jpg"
                processed_path = os.path.join(OUTPUT_FOLDER, processed_filename)
                
                # 复制示例图片到输出目录
                shutil.copy2(example_image_path, processed_path)
                
                # 更新任务数据
                task_data["status"] = "completed"
                task_data["processed_url"] = f"/output/{processed_filename}"
                task_data["completed_at"] = datetime.now().isoformat()
                store_task_info(task_id, task_data)
                
                print(f"✓ 任务 {task_id} 处理完成，结果图片: {processed_filename}")
        else:
            # 虚拟布置任务的处理逻辑
            # 使用示例图片作为处理结果
            example_room_path = os.path.join('example', 'decorate_room.png')
            if os.path.exists(example_room_path):
                processed_filename = f"{task_id}_staged.png"
                processed_path = os.path.join(OUTPUT_FOLDER, processed_filename)
                
                # 复制示例图片到输出目录
                shutil.copy2(example_room_path, processed_path)
                
                # 复制家具列表 JSON
                example_selection_path = os.path.join('example', 'selection.json')
                furniture_list = []
                furniture_images = []
                if os.path.exists(example_selection_path):
                    with open(example_selection_path, 'r', encoding='utf-8') as f:
                        furniture_list = json.load(f)
                    
                    # 复制家具图片
                    example_dir = 'example'
                    for furniture in furniture_list:
                        model_id = furniture.get('model_id')
                        if model_id:
                            furniture_image_path = os.path.join(example_dir, f"{model_id}.png")
                            if os.path.exists(furniture_image_path):
                                furniture_filename = f"{task_id}_{model_id}.png"
                                furniture_output_path = os.path.join(OUTPUT_FOLDER, furniture_filename)
                                shutil.copy2(furniture_image_path, furniture_output_path)
                                
                                furniture_images.append({
                                    "model_id": model_id,
                                    "image_url": f"/output/{furniture_filename}"
                                })
                
                # 更新任务数据
                task_data["status"] = "completed"
                task_data["processed_url"] = f"/output/{processed_filename}"
                task_data["furniture_list"] = furniture_list
                task_data["furniture_images"] = furniture_images
                task_data["completed_at"] = datetime.now().isoformat()
                store_task_info(task_id, task_data)
                
                print(f"✓ 任务 {task_id} 处理完成，结果图片: {processed_filename}")
            else:
                # 如果没有示例图片，则复制原图
                original_path = task_data.get("original_path")
                if original_path and os.path.exists(original_path):
                    img = Image.open(original_path)
                    processed_filename = f"{task_id}_staged.jpg"
                    processed_path = os.path.join(OUTPUT_FOLDER, processed_filename)
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    img.save(processed_path, 'JPEG', quality=95)
                    
                    task_data["status"] = "completed"
                    task_data["processed_url"] = f"/output/{processed_filename}"
                    task_data["completed_at"] = datetime.now().isoformat()
                    store_task_info(task_id, task_data)
                    
                    print(f"✓ 任务 {task_id} 处理完成，结果图片: {processed_filename}")
                else:
                    task_data["status"] = "failed"
                    task_data["error"] = "无法找到原始图片或示例图片"
                    store_task_info(task_id, task_data)
    except Exception as e:
        print(f"✗ 处理任务 {task_id} 失败: {e}")
        task_data["status"] = "failed"
        task_data["error"] = str(e)
        store_task_info(task_id, task_data)


@app.get("/task/{task_id}/result")
async def get_task_result(task_id: str, background_tasks: BackgroundTasks):
    """
    获取任务处理结果（轮询接口）
    
    流程:
    1. 从Redis或存储中获取任务信息
    2. 检查任务状态
    3. 如果任务已加入队列但未开始处理，启动后台处理任务
    4. 如果处理完成，返回处理后的图片URL
    5. 如果仍在处理中，返回处理中状态
    """
    try:
        # 获取任务信息
        task_data = get_task_info(task_id)
        if not task_data:
            return JSONResponse({
                "success": False,
                "status": "not_found",
                "error": "任务不存在"
            }, status_code=404)
        
        task_status = task_data.get("status", "unknown")
        task_type = task_data.get("task_type")
        
        # 如果任务已加入队列但未开始处理，启动后台处理任务
        if task_status == "queued":
            # 启动后台处理任务（模拟从Redis队列读取并处理）
            background_tasks.add_task(simulate_task_processing, task_id, task_type)
            # 更新状态为处理中
            task_data["status"] = "processing"
            store_task_info(task_id, task_data)
            return JSONResponse({
                "success": True,
                "status": "processing",
                "task_id": task_id,
                "message": "任务处理中，请稍候..."
            })
        
        # 如果任务已完成，返回处理后的图片URL
        if task_status == "completed":
            processed_url = task_data.get("processed_url")
            if processed_url:
                response_data = {
                    "success": True,
                    "status": "completed",
                    "task_id": task_id,
                    "processed_url": processed_url,
                    "original_url": task_data.get("original_url")
                }
                
                # 如果是虚拟布置任务，添加家具列表和图片信息
                if task_type == "virtual":
                    furniture_list = task_data.get("furniture_list", [])
                    furniture_images = task_data.get("furniture_images", [])
                    
                    if furniture_list:
                        response_data["furniture_list"] = furniture_list
                    if furniture_images:
                        response_data["furniture_images"] = furniture_images
                
                return JSONResponse(response_data)
            else:
                return JSONResponse({
                    "success": False,
                    "status": "completed_no_result",
                    "error": "处理完成但未找到结果图片"
                })
        
        # 如果任务失败
        elif task_status == "failed":
            return JSONResponse({
                "success": False,
                "status": "failed",
                "error": task_data.get("error", "处理失败")
            })
        
        # 如果任务仍在处理中
        elif task_status == "processing":
            return JSONResponse({
                "success": True,
                "status": "processing",
                "task_id": task_id,
                "message": "任务处理中，请稍候..."
            })
        
        # 其他状态
        else:
            return JSONResponse({
                "success": True,
                "status": task_status,
                "task_id": task_id,
                "message": "等待处理..."
            })
            
    except Exception as e:
        return JSONResponse({
            "success": False,
            "status": "error",
            "error": f"查询任务结果失败: {str(e)}"
        }, status_code=500)


@app.options("/uploads/{filename}")
async def options_upload(filename: str):
    """处理上传文件的 OPTIONS 预检请求"""
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Max-Age": "3600",
        }
    )


@app.get("/uploads/{filename}")
async def get_upload(filename: str):
    """获取上传的原始图片"""
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="文件不存在")
    
    # 读取文件内容
    with open(file_path, "rb") as f:
        file_content = f.read()
    
    # 确定媒体类型
    if filename.endswith('.jpg') or filename.endswith('.jpeg'):
        media_type = "image/jpeg"
    elif filename.endswith('.png'):
        media_type = "image/png"
    else:
        media_type = "application/octet-stream"
    
    # 返回响应，手动设置 CORS 头
    return Response(
        content=file_content,
        media_type=media_type,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "*",
            "Content-Disposition": f'inline; filename="{filename}"',
        }
    )


@app.options("/output/{filename}")
async def options_output(filename: str):
    """处理输出文件的 OPTIONS 预检请求"""
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Max-Age": "3600",
        }
    )


@app.get("/output/{filename}")
async def get_output(filename: str):
    """获取处理后的图片"""
    file_path = os.path.join(OUTPUT_FOLDER, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="文件不存在")
    
    # 读取文件内容
    with open(file_path, "rb") as f:
        file_content = f.read()
    
    # 确定媒体类型
    if filename.endswith('.jpg') or filename.endswith('.jpeg'):
        media_type = "image/jpeg"
    elif filename.endswith('.png'):
        media_type = "image/png"
    else:
        media_type = "application/octet-stream"
    
    # 返回响应，手动设置 CORS 头
    return Response(
        content=file_content,
        media_type=media_type,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "*",
            "Content-Disposition": f'inline; filename="{filename}"',
        }
    )


if __name__ == "__main__":
    # 默认端口，可通过环境变量覆盖
    PORT = int(os.getenv("PORT", 5001))
    
    print("=" * 60)
    print("启动房产视觉增强系统 FastAPI 后端服务 (Redis 队列版本)")
    print("=" * 60)
    print(f"访问 http://localhost:{PORT}/docs 查看 API 文档")
    print(f"访问 http://localhost:{PORT}/health 检查服务状态")
    print(f"Redis 配置: {REDIS_HOST}:{REDIS_PORT}")
    print("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="info")

