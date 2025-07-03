# -*- coding: utf8 -*-
import asyncio
import websockets
import json
import time
from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.hunyuan.v20230901 import hunyuan_client, models

# ==== 配置区域 ====
PROMPT = "一只可爱的兔子"
PORT = 8080
# ==================

def submit_3d_job(prompt):
    """提交混元生3D任务（文生3D）"""
    try:
        cred = credential.Credential("", "")
        httpProfile = HttpProfile()
        httpProfile.endpoint = "hunyuan.tencentcloudapi.com"
        clientProfile = ClientProfile()
        clientProfile.httpProfile = httpProfile

        client = hunyuan_client.HunyuanClient(cred, "ap-guangzhou", clientProfile)
        
        req = models.SubmitHunyuanTo3DJobRequest()
        req.Prompt = prompt
        req.Num = 1
        
        resp = client.SubmitHunyuanTo3DJob(req)
        print(f"任务提交成功! JobID: {resp.JobId}")
        return resp.JobId

    except TencentCloudSDKException as err:
        print(f"API调用失败: {err}")
        return None

def query_3d_job(job_id):
    """查询混元生3D任务状态"""
    try:
        cred = credential.Credential("", "")
        httpProfile = HttpProfile()
        httpProfile.endpoint = "hunyuan.tencentcloudapi.com"
        clientProfile = ClientProfile()
        clientProfile.httpProfile = httpProfile

        client = hunyuan_client.HunyuanClient(cred, "ap-guangzhou", clientProfile)
        
        req = models.QueryHunyuanTo3DJobRequest()
        req.JobId = job_id
        
        while True:
            resp = client.QueryHunyuanTo3DJob(req)
            status = resp.Status
            
            if status == "DONE":
                print("\n任务完成! 生成结果:")
                for file in resp.ResultFile3Ds[0].File3D:
                    print(f"文件类型: {file.Type}, 下载URL: {file.Url}")
                    if file.Type == "OBJ":
                        return file.Url
                
            elif status == "FAIL":
                print(f"\n任务失败! 错误码: {resp.ErrorCode}, 错误信息: {resp.ErrorMessage}")
                return None
            else:
                print(f"任务状态: {status}, 等待10秒后重试...", end='\r')
                time.sleep(10)
                
    except TencentCloudSDKException as err:
        print(f"查询任务失败: {err}")
        return None

async def send_obj_to_unity(websocket):
    """WebSocket 事件回调：Unity 连接后发送 OBJ URL"""
    print("Unity 客户端已连接，准备发送3D模型URL...")

    # 步骤1：提交生成任务
    job_id = submit_3d_job(PROMPT)
    if not job_id:
        await websocket.send(json.dumps({"type": "error", "message": "提交任务失败"}))
        return

    # 步骤2：查询结果
    obj_url = query_3d_job(job_id)
    if not obj_url:
        await websocket.send(json.dumps({"type": "error", "message": "任务查询失败"}))
        return

    # 步骤3：构建JSON并发送
    message = {
        "type": "3d_model",
        "url":  "",
        "timestamp": int(time.time())
    }
    await websocket.send(json.dumps(message))
    print("已发送 OBJ URL 给 Unity 客户端")

async def main():
    print(f"启动 WebSocket 服务器，等待 Unity 客户端连接（端口 {PORT}）...")
    async with websockets.serve(send_obj_to_unity, "localhost", PORT):
        await asyncio.Future()  # 永远运行，不退出

if __name__ == "__main__":
    asyncio.run(main())

