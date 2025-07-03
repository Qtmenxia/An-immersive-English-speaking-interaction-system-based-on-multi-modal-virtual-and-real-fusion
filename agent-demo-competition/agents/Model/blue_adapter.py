# blue_adapter.py
# -*- coding: utf-8 -*-
"""
Bridge between OpenAI-style ChatCompletion and vivo BlueLM (vivogpt/completions).
Author: <you>
Date  : 2025-04-25
"""

import base64
import hashlib
import hmac
import time
import uuid
import json
import random
import string
import urllib.parse as urlparse
from typing import List, Dict, Any, Optional

import requests   # pip install requests

# ---------------------------------------------------------------------------
# 🔑 1. 你的 BlueLM 凭据（可放到环境变量或配置文件里）
# ---------------------------------------------------------------------------
BLUE_APP_ID   = "2025761464"
BLUE_APP_KEY  = "uTfCZSgrEjvqauix"
BLUE_API_MODEL = "vivo-BlueLM-TB-Pro"          # 你在平台上开通的模型 ID
BLUE_API_URL   = "https://api-ai.vivo.com.cn/vivogpt/completions"

# ---------------------------------------------------------------------------
# 2. BlueLM 网关签名工具
#    生成 X-AI-GATEWAY-* 头部（参考官方鉴权规范）
# ---------------------------------------------------------------------------
def _gen_nonce(length: int = 12) -> str:
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=length))

def _canonical_query(params: Dict[str, str]) -> str:
    """将 query dict 编码并按 key 排序后拼接（RFC3986）。"""
    if not params:
        return ""
    esc = urlparse.quote
    return "&".join(f"{esc(k)}={esc(str(v))}" for k, v in sorted(params.items()))

def _gen_signature(app_key: str, signing: str) -> str:
    digest = hmac.new(app_key.encode(), signing.encode(), hashlib.sha256).digest()
    return base64.b64encode(digest).decode()

def _sign_headers(
    app_id: str,
    app_key: str,
    method: str,
    uri: str,
    query: Dict[str, str]
) -> Dict[str, str]:
    """
    返回 vivo 网关所需的 5 个签名头：
      X-AI-GATEWAY-APP-ID / -TIMESTAMP / -NONCE / -SIGNED-HEADERS / -SIGNATURE
    """
    timestamp = str(int(time.time()))
    nonce     = _gen_nonce()
    canonical_qs = _canonical_query(query)
    signed_headers_string = (
        f"x-ai-gateway-app-id:{app_id}\n"
        f"x-ai-gateway-timestamp:{timestamp}\n"
        f"x-ai-gateway-nonce:{nonce}"
    )

    signing_string = (
        f"{method.upper()}\n"           # ① HTTP Method
        f"{uri}\n"                      # ② HTTP URI
        f"{canonical_qs}\n"             # ③ canonical_query_string
        f"{app_id}\n"                   # ④ app_id
        f"{timestamp}\n"                # ⑤ timestamp
        f"{signed_headers_string}"      # ⑥ signed_headers_string
    )

    sig = _gen_signature(app_key, signing_string)
    return {
        "X-AI-GATEWAY-APP-ID": app_id,
        "X-AI-GATEWAY-TIMESTAMP": timestamp,
        "X-AI-GATEWAY-NONCE": nonce,
        "X-AI-GATEWAY-SIGNED-HEADERS":
            "x-ai-gateway-app-id;x-ai-gateway-timestamp;x-ai-gateway-nonce",
        "X-AI-GATEWAY-SIGNATURE": sig,
    }

# ---------------------------------------------------------------------------
# 3. 消息转换：OpenAI messages  →  BlueLM prompt
#    这里给出一种通用拼接方式，你可按业务自定义。
# ---------------------------------------------------------------------------
def _messages_to_prompt(messages: List[Dict[str, str]]) -> str:
    """把 OpenAI messages 列表拼成单回合 prompt（示例模板）。"""
    parts = []
    for m in messages:
        role = m["role"]
        if role == "system":
            parts.append(f"[SYSTEM] {m['content']}")
        elif role == "user":
            parts.append(f"[USER] {m['content']}")
        elif role == "assistant":
            parts.append(f"[ASSISTANT] {m['content']}")
        else:                       # tool / function / ...
            parts.append(f"[{role.upper()}] {m['content']}")
    # Blue 接口只收单字符串 prompt，所以用换行分隔
    return "\n".join(parts) + "\n[ASSISTANT] "

# ---------------------------------------------------------------------------
# 4. 主适配类：模仿 openai.ChatCompletion
# ---------------------------------------------------------------------------
class BlueChatCompletion:
    """
    用法：
        from blue_adapter import BlueChatCompletion as ChatCompletion

        resp = ChatCompletion.create(
            model="gpt-3.5-turbo",           # 任意占位符，内部会被替换
            messages=[{"role":"user","content":"今天天气？"}],
            temperature=0.7,
        )
        print(resp["choices"][0]["message"]["content"])
    """

    @staticmethod
    def create(
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.9,
        top_p: float = 1.0,
        stream: bool = False,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        接口完全兼容 openai.ChatCompletion.create 的常用参数。
        只实现最常用字段，更多字段请按需映射到 Blue `extra`。
        """
        # ---------- a) 组装 Blue 请求 ----------
        request_id = str(uuid.uuid4())
        query_params = {"requestId": request_id}

        body = {
            "prompt": _messages_to_prompt(messages),
            "model": BLUE_API_MODEL,
            "sessionId": kwargs.get("session_id", str(uuid.uuid4())),
            "extra": {
                "temperature": temperature,
                "top_p": top_p,
                # 你可以在这里增加 Blue 支持的更多采样 / 截止参数
            },
        }

        headers = {
            "Content-Type": "application/json",
            **_sign_headers(
                BLUE_APP_ID,
                BLUE_APP_KEY,
                "POST",
                "/vivogpt/completions",
                query_params,
            ),
        }

        # ---------- b) 发送 ----------
        resp = requests.post(
            BLUE_API_URL,
            params=query_params,
            json=body,
            headers=headers,
            stream=stream,
            timeout=kwargs.get("timeout", 100),
        )
        resp.raise_for_status()
        payload = resp.json()

        if payload.get("code") != 0:
            raise RuntimeError(f"BlueLM error: {payload}")

        data = payload["data"]
        content = data.get("content", "")

        # ---------- c) 转回 OpenAI ChatCompletion 结构 ----------
        created = int(time.time())
        choice = {
            "index": 0,
            "finish_reason": (data.get("finishReason") or "STOP").lower(),
            "message": {
                "role": "assistant",
                "content": content,
            },
        }

        usage_raw = data.get("usage") or {}
        usage = {
            "prompt_tokens": usage_raw.get("promptTokens"),
            "completion_tokens": usage_raw.get("completionTokens"),
            "total_tokens": usage_raw.get("totalTokens"),
            # Blue 目前还提供 duration，可按需添加
        }

        return {
            "id": data.get("requestId", request_id),
            "object": "chat.completion",
            "created": created,
            "model": model,
            "choices": [choice],
            "usage": usage,
        }


# ---------------------------------------------------------------------------
# 5. 给旧项目做“零改动”替换的两种思路
# ---------------------------------------------------------------------------
#
# ① 直接 import 重命名
# --------------------------------------------------
#   from blue_adapter import BlueChatCompletion as ChatCompletion
#
#   ChatCompletion.create( ... )  # 语义与 openai.ChatCompletion.create 相同
#
# ② monkey-patch openai
# --------------------------------------------------
#   import openai
#   from blue_adapter import BlueChatCompletion
#   openai.ChatCompletion = BlueChatCompletion
#
#   # 之后整站任意旧代码的 `openai.ChatCompletion.create(...)`
#   # 都会经由 BlueChatCompletion 路由到 vivo BlueLM。
#
# 注意：如需流式(stream=True)返回，可在 create() 里 yield 字符串行，
#       再按 OpenAI SSE 协议拼接；Blue 接口默认提供 chunk-ed JSON，
#       具体实现可参考官方示例或自行扩展。
