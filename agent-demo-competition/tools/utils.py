import json
import re


def extract_agent_info(json_str):
    # 解析JSON字符串
    data = json.loads(json_str)
    # print(f"extract_agent_info: {data}")

    # 提取message字段
    message = data.get("message", "")
    # print(f"extract_agent_info message: {message}")

    # 使用正则表达式提取action和text
    action_match = re.search(r"The waiter`s action is (\S+)", message)
    text_match = re.search(r"The waiter's text is (.+)", message)
    # print(f"extract_agent_info action_match: {action_match}")

    # 返回提取的action和text，如果未找到则返回None
    action = action_match.group(1) if action_match else None
    text = text_match.group(1) if text_match else None
    if action:
        return action
    elif text:
        return text

def extract_data(json_str):
    # 解析JSON字符串
    data = json.loads(json_str)

    # 获取data的值
    return data.get("data")

def extract_user_name(input_string):
    # 检查字符串是否包含"userName="
    if "userName=" in input_string:
        # 从"userName="之后开始提取，直到字符串末尾
        user_name = input_string.split("userName=", 1)[1]
        return user_name
    else:
        return "userName not found"
