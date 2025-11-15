"""
Worker Server - 从 Redis 队列读取任务，处理后写回 Redis
模拟 AI 处理服务器，完成完整的任务处理闭环
"""

import os
import json
import time
import redis
import shutil
from PIL import Image
from datetime import datetime
from pathlib import Path
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Worker Server - Task Processor", version="1.0.0")

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 目录配置
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'output'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Redis 配置（与 api_server.py 保持一致）
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))
REDIS_QUEUE_PREFIX = "task_queue:"
TASK_STORAGE_PREFIX = "task_storage:"

# 初始化 Redis 连接
redis_client = None
try:
    redis_client = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=REDIS_DB,
        decode_responses=True,
        socket_connect_timeout=5
    )
    redis_client.ping()
    print(f"✓ Worker Server: Redis 连接成功 {REDIS_HOST}:{REDIS_PORT}")
except Exception as e:
    print(f"✗ Worker Server: Redis 连接失败: {e}")
    print("✗ Worker Server 需要 Redis 才能运行，请先启动 Redis 服务")
    exit(1)


def get_task_info(task_id: str) -> dict:
    """
    从 Redis 获取任务信息
    
    Args:
        task_id: 任务ID
    
    Returns:
        dict: 任务数据，如果不存在返回 None
    """
    try:
        key = f"{TASK_STORAGE_PREFIX}{task_id}"
        task_json = redis_client.get(key)
        if task_json:
            return json.loads(task_json)
    except Exception as e:
        print(f"✗ 从 Redis 获取任务信息失败: {e}")
    return None


def update_task_info(task_id: str, task_data: dict) -> bool:
    """
    更新任务信息到 Redis
    
    Args:
        task_id: 任务ID
        task_data: 任务数据字典
    
    Returns:
        bool: 是否成功更新
    """
    try:
        key = f"{TASK_STORAGE_PREFIX}{task_id}"
        task_json = json.dumps(task_data, ensure_ascii=False)
        redis_client.setex(key, 3600, task_json)  # 存储1小时
        return True
    except Exception as e:
        print(f"✗ 更新任务信息到 Redis 失败: {e}")
        return False


def process_denoise_task(task_data: dict) -> dict:
    """
    处理 AI 高清放大与去杂任务
    
    Args:
        task_data: 任务数据字典
    
    Returns:
        dict: 更新后的任务数据
    """
    task_id = task_data.get("task_id")
    original_path = task_data.get("original_path")
    
    print(f"[处理中] 任务 {task_id}: AI高清放大与去杂处理")
    
    # 更新任务状态为处理中
    task_data["status"] = "processing"
    task_data["processing_started_at"] = datetime.now().isoformat()
    update_task_info(task_id, task_data)
    
    try:
        # 模拟处理时间（实际应该是 AI 模型处理）
        time.sleep(2)  # 模拟处理耗时
        
        # 检查原始图片是否存在
        if not os.path.exists(original_path):
            raise FileNotFoundError(f"原始图片不存在: {original_path}")
        
        # 读取原始图片
        img = Image.open(original_path)
        
        # 模拟 AI 处理：这里使用示例图片作为处理结果
        # 实际应该调用 AI 模型进行去杂处理
        example_image_path = os.path.join('example', 'empty_room.jpg')
        
        if os.path.exists(example_image_path):
            # 使用示例图片作为处理结果
            processed_filename = f"{task_id}_processed.jpg"
            processed_path = os.path.join(OUTPUT_FOLDER, processed_filename)
            shutil.copy2(example_image_path, processed_path)
        else:
            # 如果没有示例图片，则简单复制原图（实际应该进行 AI 处理）
            processed_filename = f"{task_id}_processed.png"
            processed_path = os.path.join(OUTPUT_FOLDER, processed_filename)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            img.save(processed_path, 'PNG')
        
        # 更新任务数据
        task_data["status"] = "completed"
        task_data["processed_url"] = f"/output/{processed_filename}"
        task_data["processed_path"] = processed_path
        task_data["completed_at"] = datetime.now().isoformat()
        
        print(f"✓ 任务 {task_id} 处理完成: {processed_filename}")
        return task_data
        
    except Exception as e:
        print(f"✗ 处理任务 {task_id} 失败: {e}")
        task_data["status"] = "failed"
        task_data["error"] = str(e)
        task_data["failed_at"] = datetime.now().isoformat()
        return task_data


def process_virtual_staging_task(task_data: dict) -> dict:
    """
    处理虚拟布置任务
    
    Args:
        task_data: 任务数据字典
    
    Returns:
        dict: 更新后的任务数据
    """
    task_id = task_data.get("task_id")
    original_path = task_data.get("original_path")
    decoration_style = task_data.get("decoration_style", "modern")
    max_price = task_data.get("max_price", 50000)
    room_type = task_data.get("room_type", "living room")
    
    print(f"[处理中] 任务 {task_id}: 虚拟布置处理")
    print(f"  参数: 风格={decoration_style}, 预算={max_price}, 房间类型={room_type}")
    
    # 更新任务状态为处理中
    task_data["status"] = "processing"
    task_data["processing_started_at"] = datetime.now().isoformat()
    update_task_info(task_id, task_data)
    
    try:
        # 模拟处理时间（实际应该是 AI 虚拟布置模型处理）
        time.sleep(3)  # 虚拟布置可能需要更长时间
        
        # 检查原始图片是否存在
        if not os.path.exists(original_path):
            raise FileNotFoundError(f"原始图片不存在: {original_path}")
        
        # 模拟 AI 虚拟布置处理
        # 实际应该调用 AI 模型根据 decoration_style, max_price, room_type 进行虚拟布置
        # 这里使用示例文件作为处理结果
        
        # 1. 复制效果图
        example_room_path = os.path.join('example', 'decorate_room.png')
        if os.path.exists(example_room_path):
            processed_filename = f"{task_id}_staged.png"
            processed_path = os.path.join(OUTPUT_FOLDER, processed_filename)
            shutil.copy2(example_room_path, processed_path)
        else:
            # 如果没有示例图片，则复制原图
            img = Image.open(original_path)
            processed_filename = f"{task_id}_staged.jpg"
            processed_path = os.path.join(OUTPUT_FOLDER, processed_filename)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            img.save(processed_path, 'JPEG', quality=95)
        
        # 2. 复制家具列表 JSON
        example_selection_path = os.path.join('example', 'selection.json')
        furniture_list = []
        if os.path.exists(example_selection_path):
            with open(example_selection_path, 'r', encoding='utf-8') as f:
                furniture_list = json.load(f)
            
            # 复制 JSON 文件到输出目录
            selection_filename = f"{task_id}_selection.json"
            selection_path = os.path.join(OUTPUT_FOLDER, selection_filename)
            shutil.copy2(example_selection_path, selection_path)
        
        # 3. 复制家具图片
        furniture_images = []
        example_dir = 'example'
        if furniture_list:
            for furniture in furniture_list:
                model_id = furniture.get('model_id')
                if model_id:
                    furniture_image_path = os.path.join(example_dir, f"{model_id}.png")
                    if os.path.exists(furniture_image_path):
                        # 复制家具图片到输出目录
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
        task_data["processed_path"] = processed_path
        task_data["furniture_list"] = furniture_list
        task_data["furniture_images"] = furniture_images
        task_data["selection_url"] = f"/output/{selection_filename}" if furniture_list else None
        task_data["completed_at"] = datetime.now().isoformat()
        task_data["processing_params"] = {
            "decoration_style": decoration_style,
            "max_price": max_price,
            "room_type": room_type
        }
        
        print(f"✓ 任务 {task_id} 处理完成: {processed_filename}")
        print(f"  家具数量: {len(furniture_list)}, 家具图片: {len(furniture_images)}")
        return task_data
        
    except Exception as e:
        print(f"✗ 处理任务 {task_id} 失败: {e}")
        import traceback
        traceback.print_exc()
        task_data["status"] = "failed"
        task_data["error"] = str(e)
        task_data["failed_at"] = datetime.now().isoformat()
        return task_data


def process_task_from_queue(queue_name: str, timeout: int = 5):
    """
    从 Redis 队列中读取并处理任务
    
    Args:
        queue_name: 队列名称（如 "task_queue:denoise"）
        timeout: 阻塞超时时间（秒）
    """
    try:
        # 使用 BRPOP 阻塞式读取队列（从右侧弹出，即先进先出）
        result = redis_client.brpop(queue_name, timeout=timeout)
        
        if result:
            queue, task_json = result
            task_data = json.loads(task_json)
            task_id = task_data.get("task_id")
            task_type = task_data.get("task_type")
            
            print(f"\n{'='*60}")
            print(f"收到新任务: {task_id} (类型: {task_type})")
            print(f"{'='*60}")
            
            # 根据任务类型处理
            if task_type == "denoise":
                updated_task_data = process_denoise_task(task_data)
            elif task_type == "virtual":
                updated_task_data = process_virtual_staging_task(task_data)
            else:
                print(f"✗ 未知的任务类型: {task_type}")
                task_data["status"] = "failed"
                task_data["error"] = f"未知的任务类型: {task_type}"
                updated_task_data = task_data
            
            # 更新任务信息到 Redis（供 api_server 查询）
            update_task_info(task_id, updated_task_data)
            
            print(f"✓ 任务 {task_id} 处理完成，结果已更新到 Redis")
            print(f"{'='*60}\n")
            
            return True
        else:
            # 超时，没有任务
            return False
            
    except redis.exceptions.ConnectionError:
        print("✗ Redis 连接断开，尝试重连...")
        return False
    except Exception as e:
        print(f"✗ 处理队列任务失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def worker_loop():
    """
    Worker 主循环：持续从队列中读取任务并处理
    """
    print("\n" + "="*60)
    print("Worker Server 启动 - 开始监听 Redis 队列")
    print("="*60)
    print(f"监听队列:")
    print(f"  - {REDIS_QUEUE_PREFIX}denoise (AI高清放大与去杂)")
    print(f"  - {REDIS_QUEUE_PREFIX}virtual (虚拟布置)")
    print("="*60 + "\n")
    
    queue_names = [
        f"{REDIS_QUEUE_PREFIX}denoise",
        f"{REDIS_QUEUE_PREFIX}virtual"
    ]
    
    while True:
        try:
            # 检查 Redis 连接
            redis_client.ping()
            
            # 轮询所有队列
            task_processed = False
            for queue_name in queue_names:
                if process_task_from_queue(queue_name, timeout=1):
                    task_processed = True
                    break  # 处理完一个任务后，重新开始轮询
            
            # 如果没有任务，短暂休眠避免 CPU 占用过高
            if not task_processed:
                time.sleep(0.5)
                
        except redis.exceptions.ConnectionError:
            print("✗ Redis 连接断开，5秒后重试...")
            time.sleep(5)
            # 尝试重连
            try:
                redis_client.ping()
                print("✓ Redis 重连成功")
            except:
                pass
        except KeyboardInterrupt:
            print("\n\n收到中断信号，Worker Server 正在关闭...")
            break
        except Exception as e:
            print(f"✗ Worker 循环错误: {e}")
            import traceback
            traceback.print_exc()
            time.sleep(1)


@app.get("/")
async def root():
    """Worker Server 状态"""
    try:
        redis_status = redis_client.ping()
    except:
        redis_status = False
    
    return {
        "service": "Worker Server - Task Processor",
        "version": "1.0.0",
        "status": "running",
        "redis_connected": redis_status,
        "redis_host": REDIS_HOST,
        "redis_port": REDIS_PORT,
        "queues": [
            f"{REDIS_QUEUE_PREFIX}denoise",
            f"{REDIS_QUEUE_PREFIX}virtual"
        ]
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    try:
        redis_status = redis_client.ping()
    except:
        redis_status = False
    
    return {
        "status": "healthy" if redis_status else "unhealthy",
        "redis_connected": redis_status,
        "redis_host": REDIS_HOST,
        "redis_port": REDIS_PORT
    }


if __name__ == "__main__":
    import threading
    
    # 默认端口，可通过环境变量覆盖
    PORT = int(os.getenv("WORKER_PORT", 5002))
    
    print("=" * 60)
    print("启动 Worker Server - 任务处理服务")
    print("=" * 60)
    print(f"Worker API: http://localhost:{PORT}/")
    print(f"健康检查: http://localhost:{PORT}/health")
    print(f"Redis 配置: {REDIS_HOST}:{REDIS_PORT}")
    print("=" * 60)
    
    # 在后台线程中启动 Worker 循环
    worker_thread = threading.Thread(target=worker_loop, daemon=True)
    worker_thread.start()
    
    # 启动 FastAPI 服务器（用于健康检查和状态查询）
    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="info")

