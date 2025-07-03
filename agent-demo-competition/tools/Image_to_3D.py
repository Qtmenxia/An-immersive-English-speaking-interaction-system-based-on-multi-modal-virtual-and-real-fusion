import asyncio
import websockets
import json
import base64
import time
from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.hunyuan.v20230901 import hunyuan_client, models
import logging
from PIL import Image
from io import BytesIO

# 配置区域
SECRET_ID = ""  # 替换为腾讯云API密钥
SECRET_KEY = "" # 替换为腾讯云API密钥
IMAGE_PATH = ""  # 本地图片路径

# WebSocket 服务器配置
WS_HOST = "0.0.0.0"  
WS_PORT = 8081       

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Hunyuan3D")

def image_to_base64(image_path):
    """将图片转为Base64并验证"""
    with open(image_path, "rb") as f:
        img_data = f.read()
        img = Image.open(BytesIO(img_data))
        
        # 验证分辨率
        if min(img.size) < 50 or max(img.size) > 5000:
            raise ValueError("图片分辨率需在50-5000像素之间")
        
        # 验证大小
        if len(img_data) > 6 * 1024 * 1024:
            raise ValueError("图片大小超过6MB限制")
        
        return base64.b64encode(img_data).decode('utf-8')

def submit_3d_job(image_base64):
    """提交3D生成任务"""
    cred = credential.Credential(SECRET_ID, SECRET_KEY)
    http_profile = HttpProfile(endpoint="hunyuan.tencentcloudapi.com")
    client_profile = ClientProfile(httpProfile=http_profile)
    
    client = hunyuan_client.HunyuanClient(cred, "ap-guangzhou", client_profile)
    req = models.SubmitHunyuanTo3DJobRequest()
    req.ImageBase64 = image_base64
    
    try:
        resp = client.SubmitHunyuanTo3DJob(req)
        return resp.JobId
    except Exception as e:
        raise RuntimeError(f"任务提交失败: {str(e)}")

def get_model_url(job_id):
    """获取生成的OBJ模型URL"""
    cred = credential.Credential(SECRET_ID, SECRET_KEY)
    client = hunyuan_client.HunyuanClient(cred, "ap-guangzhou")
    
    while True:
        req = models.QueryHunyuanTo3DJobRequest()
        req.JobId = job_id
        resp = client.QueryHunyuanTo3DJob(req)
        
        if resp.Status == "DONE":
            for file_group in resp.ResultFile3Ds:
                for file_info in file_group.File3D:
                    if file_info.Type == "OBJ":
                        return file_info.Url
            raise ValueError("未找到OBJ模型文件")
        elif resp.Status == "FAIL":
            raise RuntimeError(f"任务失败: {resp.ErrorMessage}")
        
        logger.info(f"⏳ 任务处理中... 当前状态: {resp.Status}")
        time.sleep(10)

async def handle_client(websocket):
    """处理客户端连接"""
    client_ip = websocket.remote_address[0]
    logger.info(f"客户端已连接: {client_ip}")
    
    try:
        # 1. 准备图片
        logger.info("🖼 正在处理图片...")
        img_base64 = image_to_base64(IMAGE_PATH)
        
        # 2. 提交3D任务
        logger.info("🚀 提交3D生成任务到腾讯云...")
        job_id = submit_3d_job(img_base64)
        logger.info(f"📌 任务ID: {job_id}")
        
        # 3. 获取模型URL
        logger.info("⏳ 等待3D模型生成...")
        obj_url = get_model_url(job_id)
        # logger.info(f"🎉 OBJ模型已生成: {obj_url}")
        
        # 4. 发送模型URL到Unity客户端
        payload = {
            "type": "model_url",
            "url": "",
            "timestamp": int(time.time())
        }
        await websocket.send(json.dumps(payload))
        logger.info(f"✅ OBJ模型URL已发送至Unity客户端")
        
        # 5. 等待Unity确认
        response = await websocket.recv()
        logger.info(f"🔄 Unity客户端响应: {response}")
        
    except asyncio.TimeoutError:
        logger.error("⚠️ 处理超时")
        await websocket.close(code=1011, reason="处理超时")
    except Exception as e:
        logger.error(f"❌ 处理错误: {str(e)}")
        await websocket.close(code=1011, reason=str(e))
    finally:
        logger.info(f"客户端断开连接: {client_ip}")

async def start_server():
    """启动WebSocket服务器"""
    logger.info(f"启动WebSocket服务器: {WS_HOST}:{WS_PORT}")
    async with websockets.serve(
        handle_client, 
        WS_HOST, 
        WS_PORT,
        ping_interval=30,   # 每30秒发送ping
        ping_timeout=60,    # 客户端60秒无响应断开
        max_size=10 * 1024 * 1024  # 最大消息10MB
    ):
        logger.info("服务器已启动，等待客户端连接...")
        await asyncio.Future()  # 永久运行

if __name__ == "__main__":
    asyncio.run(start_server())