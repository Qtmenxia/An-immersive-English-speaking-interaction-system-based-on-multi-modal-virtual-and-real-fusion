import requests
import json
import time
import hashlib
import hmac
import uuid
from typing import Dict, Any
from autogen import LLMConfig
from autogen.oai.client import ModelClient
from agents.Model.blue_adapter import BlueChatCompletion as ChatCompletion

# 蓝心大模型配置参数（用户提供）
APP_ID = "2025761464"
APP_KEY = "uTfCZSgrEjvqauix"
API_URL = "https://api-ai.vivo.com.cn/vivogpt/completions"
URI = '/vivogpt/completions'
DOMAIN = 'api-ai.vivo.com.cn'
MODEL_NAME = 'vivo-BlueLM-TB-Pro'  # 或对应新模型标识符
METHOD = 'POST'

blue_config_transformed1 = ChatCompletion.create(
            model="gpt-3.5-turbo",           # 任意占位符，内部会被替换
            messages=[{"role":"user","content":"今天天气？"}],
            temperature=0.7,
        )

def generate_signature(app_id, app_key):
    """生成API签名（基于vivo文档的签名逻辑）"""
    timestamp = str(int(time.time() * 1000))  # 精确到毫秒[7](@ref)
    nonce = hashlib.md5(str(time.time()).encode()).hexdigest()[:8]  # 生成8位随机数
    message = f"{app_id}{timestamp}{nonce}"
    
    # HMAC-SHA256签名[6,7](@ref)
    signature = hmac.new(
        app_key.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return timestamp, nonce, signature

# 修改后的蓝心大模型配置字典
# 分步定义配置字典
blue_config = {
    "cache_seed": None,
    "config_list": [
        {
            "model": "vivo-BlueLM-TB-Pro",
            "api_key": "uTfCZSgrEjvqauix",
            "base_url": "https://api-ai.vivo.com.cn/vivogpt/completions",
            "app_id": "2025761464"
        }
    ],
    "timeout": 100
}

# 追加动态生成的头部（延迟求值）
blue_config["extra_headers"] = {
    "Content-Type": "application/json",
    "X-AI-GATEWAY-APP-ID": blue_config["config_list"][0]["app_id"],  # ✅此时字典已完整定义
    "X-AI-GATEWAY-TIMESTAMP	": lambda: generate_signature(
                app_id="2025761464",
                app_key="uTfCZSgrEjvqauix")[0],
    "X-AI-GATEWAY-NONCE": lambda: generate_signature(
                app_id="2025761464",
                app_key="uTfCZSgrEjvqauix")[1],
    "X-AI-GATEWAY-SIGNATURE": lambda: generate_signature(
                app_id="2025761464",
                app_key="uTfCZSgrEjvqauix")[2],
    "X-AI-GATEWAY-SIGNED-HEADERS": "x-ai-gateway-app-id;x-ai-gateway-timestamp;x-ai-gateway-nonce"
}

class BlueLMAdapter:
    def __init__(self, config: Dict):
        self.base_url = config["config_list"][0]["base_url"]  # ✅ 从顶层获取
        self.app_id = config["config_list"][0]["app_id"]
        self.api_key = config["config_list"][0]["api_key"]
        self.timeout = config.get("timeout", 100)  # 可选默认值
        
    def _generate_headers(self) -> Dict:
        """动态生成签名请求头"""
        headers = {
            "Content-Type": "application/json",
            "X-AI-GATEWAY-APP-ID": self.config["app_id"]
        }
        # 动态计算签名三要素（示例实现）
        timestamp, nonce, signature = generate_signature(
            app_id=self.config["app_id"],
            app_key=self.config["api_key"]
        )
        headers.update({
            "X-AI-GATEWAY-TIMESTAMP": timestamp,
            "X-AI-GATEWAY-NONCE": nonce,
            "X-AI-GATEWAY-SIGNATURE": signature,
            "X-AI-GATEWAY-SIGNED-HEADERS": "x-ai-gateway-app-id;x-ai-gateway-timestamp;x-ai-gateway-nonce"
        })
        return headers

    def gpt_to_blue_format(self, gpt_params: Dict) -> Dict:
        """GPT参数格式转换"""
        return {
            "prompt": "\n".join([msg["content"] for msg in gpt_params.get("messages", [])]),
            "sessionId": str(uuid.uuid4()),
            "extra": {
                "temperature": gpt_params.get("temperature", 0.7),
                "max_tokens": gpt_params.get("max_tokens", 1024)
            }
        }

    def blue_to_gpt_format(self, blue_response: Dict) -> Dict:
        """蓝心响应格式转换"""
        if blue_response.get("code") == 0:
            return {
                "choices": [{
                    "message": {
                        "content": blue_response["data"]["content"],
                        "role": "assistant"
                    }
                }]
            }
        raise Exception(f"API Error: {blue_response.get('message')}")

    def execute(self, gpt_params: Dict) -> Dict:
        """完整执行流程"""
        # 参数转换
        blue_data = self.gpt_to_blue_format(gpt_params)
        # 构建请求
        response = requests.post(
            self.config["base_url"],
            json=blue_data,
            headers=self._generate_headers(),
            params={"requestId": self.base_params["requestId"]},
            timeout=self.config["timeout"]
        )
        # 响应处理
        return self.blue_to_gpt_format(response.json())
    

blue_adapter = BlueLMAdapter(blue_config)
blue_config_transformed = {
    "config_list": [{
            "model": "vivo-BlueLM-TB-Pro",
            "api_type": "openai",
            "requestor": blue_adapter.execute  # 注入适配器
        }]
}

def call_vivo_llm(prompt):
    """调用蓝心大模型接口"""
    # 生成签名参数
    timestamp, nonce, signature = generate_signature(APP_ID, APP_KEY)
    
    # 构造请求头[1,7](@ref)
    headers = {
        "Content-Type": "application/json",
        "X-AI-GATEWAY-APP-ID": APP_ID,
        "X-AI-GATEWAY-TIMESTAMP	": timestamp,
        "X-AI-GATEWAY-NONCE": nonce,
        "X-AI-GATEWAY-SIGNED-HEADERS": "X-AI-GATEWAY-APP-ID,X-AI-GATEWAY-TIMESTAMP,X-AI-GATEWAY-NONCE",
        "X-AI-GATEWAY-SIGNATURE": signature
    }

    # 构造请求体（根据实际API文档调整）
    payload = {
        "model": "蓝心大模型-70B",  # 或具体模型标识符
        "prompt": prompt,         # 根据接口文档选择prompt/messages参数
        "temperature": 0.8,
        "max_tokens": 1024,
        "top_p": 0.9,
        "stream": False
    }

    try:
        response = requests.post(
            API_URL,
            headers=headers,
            data=json.dumps(payload),
            timeout=30
        )
        response.raise_for_status()
        
        result = response.json()
        if 'data' in result and 'content' in result['data']:  # 根据实际响应结构调整
            return result['data']['content']
        else:
            return f"Error: {result.get('msg', 'Unknown error')}"
            
    except requests.exceptions.RequestException as e:
        return f"API请求失败: {str(e)}"
    except json.JSONDecodeError:
        return "响应解析失败"

# 使用示例
if __name__ == "__main__":
    while True:
        user_input = input("请输入问题（输入q退出）: ")
        if user_input.lower() == 'q':
            break
        response = call_vivo_llm(user_input)
        print("\n蓝心大模型响应：")
        print(response)
        print("\n" + "="*50 + "\n")