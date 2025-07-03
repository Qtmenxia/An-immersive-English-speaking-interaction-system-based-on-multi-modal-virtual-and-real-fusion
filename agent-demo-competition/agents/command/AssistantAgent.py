# 初始化 英语学习助教 Agent
import os, openai
from agents.Model.blue_adapter import BlueChatCompletion
openai.ChatCompletion = BlueChatCompletion
openai.api_key = os.getenv("DUMMY_KEY","sk-dummy")
openai.api_base = os.getenv("DUMMY_BASE","https:/dummy.local")
openai.api_type = "open_ai"
openai.api_version = ""
from autogen import ConversableAgent, config_list_from_json
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
# 定义英语学习助教的动作状态
class AssistantAgent(ConversableAgent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.state = "idle"  # 初始状态为空闲

    def set_state(self, new_state):
        self.state = new_state

    def receive_user_input(self, user_input):
        # 判断用户输入以切换动作状态
        if "explain" in user_input.lower():
            self.set_state("explaining")
        elif "practice" in user_input.lower():
            self.set_state("practicing")
        elif "correct" in user_input.lower():
            self.set_state("correcting")
        elif "vocabulary" in user_input.lower():
            self.set_state("vocabulary-building")

        # 模拟与用户的对话反馈，确保 user_response 为字符串
        user_response = self.generate_reply(
            messages=[{"content": user_input, "role": "user"}]
        )
        if user_response is None:
            user_response = "I'm here to help, but I couldn't generate a response. Please try again with a different input."

        return self.state,user_response


# 实例化
english_learning_agent = AssistantAgent(
    "english_learning_agent",
    system_message="You are an English learning assistant. Your role is to help the user improve their English by "
                   "explaining vocabulary,"
                   "practicing conversations, correcting grammar, and suggesting new words to learn.",
    llm_config=blue_config_transformed1,
    is_termination_msg=lambda msg: "thank you" in msg["content"].lower() or "goodbye" in msg["content"].lower(),
    human_input_mode="NEVER",
)
# print(english_learning_agent.receive_user_input("Can you correct my sentence: I does to school yesterday?"))