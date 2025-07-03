import os, openai
from agents.Model.blue_adapter import BlueChatCompletion
openai.ChatCompletion = BlueChatCompletion
openai.api_key = os.getenv("DUMMY_KEY","sk-dummy")
openai.api_base = os.getenv("DUMMY_BASE","https:/dummy.local")
openai.api_type = "open_ai"
openai.api_version = ""
from autogen.agentchat import GroupChat, AssistantAgent, UserProxyAgent, GroupChatManager
from flask import Flask
from flask_sock import Sock
import json
from agents.group.RecorderAgent import RecorderAgent
# 不要改以上部分的顺序
blue_config_transformed1 = {
    "cache_seed": None,
    "config_list": [
        {"model": "gpt-3.5-turbo",
         "api_key": "sk-jbmMVXAxqeYyblhwC3Ec16F06e824fAaB3EaB2Cb0a847013",
         "base_url": "https://api.v3.cm/v1",
         }
    ],
    "timeout": 100,
    # "stream": True
}
app = Flask(__name__)
sock = Sock(app)
# gpt_config = {
#     "cache_seed": None,
#     "temperature": 0,
#     "config_list": [
#         {"model": "gpt-4-1106-preview", "api_key": "sk-9MEPSX1IHIrlX7nP4b1b55849fE54535Af6e30Ae2dFdDe14",
#          "base_url": "https://api.v3.cm/v1"}],
#     "timeout": 100,
# }
# 维护连接的客户端列表
client_list = []


# 定义任务
task = """Let the waiter and the customer complete the process of "see the menu-order-serve-pay".If the customer pay, 
output "TERMINATE"""

# 服务员动作集
waiter_actions = {
    "showing_menu": "Presenting the menu to the customer.",
    "taking_order": "Taking the customer's order.",
    "serving_food": "Serving the food to the customer.",
    "processing_payment": "Processing the customer's payment.",
    "waiting": "Miscellaneous",
}

# 动作状态记录Agent
recorder = RecorderAgent(
    name="Recorder",
    llm_config=blue_config_transformed1,
    system_message="Track and report the state transitions for the waiter.and speak in a fixed format:"
                   "first line:“The waiter`s state is XX”"
                   "second line:”The waiter `s action is XX”"
                   "third line:”The waiter `s next possible state is XX""",

    description="""I am **ONLY** allowed to speak **immediately** after waiter. """,
    action_set=["show_menu", "take_order", "others"]
)

# 服务员Agent
waiter = AssistantAgent(
    name="Waiter",
    llm_config=blue_config_transformed1,
    system_message="a human restaurant server. Help the customer with the restaurant service process.",
    description="Responsible for guiding the customer through the restaurant process, "
                "including showing menu, taking orders, "
                "serving food, and processing payment."
)

user_proxy = UserProxyAgent(
    name="User",
    system_message="Come into the restaurant and have a meal.",
    code_execution_config=False,
    human_input_mode="ALWAYS",
    llm_config=False,
)

graph_dict = {}
graph_dict[user_proxy] = [waiter]
graph_dict[waiter] = [recorder]
graph_dict[recorder] = [user_proxy]

agents = [user_proxy, recorder, waiter]

# 创建groupchat
group_chat = GroupChat(agents=agents, messages=[], max_round=25, allow_repeat_speaker=None,
                       speaker_transitions_type="allowed", allowed_or_disallowed_speaker_transitions=graph_dict)

# 创建groupManager
manager = GroupChatManager(
    groupchat=group_chat,
    llm_config=blue_config_transformed1,
    is_termination_msg=lambda x: x.get("content", "") and x.get("content", "").rstrip().endswith("TERMINATE"),
    code_execution_config=False,
)

# # 初始化对话
# user_proxy.initiate_chat(
#     manager,
#     message="Come into the restaurant",
#     clear_history=True
# )