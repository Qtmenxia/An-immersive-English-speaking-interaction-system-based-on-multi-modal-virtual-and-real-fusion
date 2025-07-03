import os, openai
from agents.Model.blue_adapter import BlueChatCompletion
openai.ChatCompletion = BlueChatCompletion
openai.api_key = os.getenv("DUMMY_KEY","sk-dummy")
openai.api_base = os.getenv("DUMMY_BASE","https:/dummy.local")
openai.api_type = "open_ai"
openai.api_version = ""
from autogen.agentchat import AssistantAgent
from typing import Callable, Dict, Literal, Optional, Union, List
from agents.command.ScoreAgent import ScoreAgent
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

class EvaluationAgent(AssistantAgent):
    def __init__(self,
                 name: str,
                 llm_config: Optional[Union[Dict, Literal[False]]] = None,
                 system_message: Optional[str] = "DEFAULT_SYSTEM_MESSAGE", # 存疑，感觉和ScoreAgent的system_message冲突了
                 is_termination_msg: Optional[Callable[[Dict], bool]] = None,
                 max_consecutive_auto_reply: Optional[int] = None,
                 human_input_mode: Literal["ALWAYS", "NEVER", "TERMINATE"] = "NEVER",
                 description: Optional[str] = None, *args, **kwargs):
        super().__init__(name=name,
                         system_message=system_message,
                         llm_config=llm_config,
                         is_termination_msg=is_termination_msg,
                         max_consecutive_auto_reply=max_consecutive_auto_reply,
                         human_input_mode=human_input_mode,
                         description=description,
                         **kwargs)
        self.score_agent = ScoreAgent(
            name="eval_agent",
            system_message="You are an evaluation assistant. Your role is to evaluate the conversation between the agent and the user.",
            llm_config=blue_config_transformed1,
            is_termination_msg=lambda msg: "thank you" in msg["content"].lower() or "goodbye" in msg["content"].lower(),
            human_input_mode="NEVER",
        )

    def handle_conversation(self, phrase_agent_ask: str, phrase_user_answer: str):
        return self.score_agent.handle_conversation(phrase_agent_ask, phrase_user_answer)

    def data_back(self, phrase_agent_ask: str, phrase_user_answer: str):
        return self.score_agent.VR_score_and_similarity(phrase_agent_ask)
