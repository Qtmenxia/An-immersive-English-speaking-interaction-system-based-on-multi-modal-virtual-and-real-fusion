import os, openai
from agents.Model.blue_adapter import BlueChatCompletion
openai.ChatCompletion = BlueChatCompletion
openai.api_key = os.getenv("DUMMY_KEY","sk-dummy")
openai.api_base = os.getenv("DUMMY_BASE","https:/dummy.local")
openai.api_type = "open_ai"
openai.api_version = ""
from openai import OpenAI
import tools.LEXILE as LEXILE
from bleurt import score
from tools.evaluation import cal_readablility, cal_semantic_similarity, deepseek_chat, generate_prompt
from autogen import ConversableAgent
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
class ScoreAgent(ConversableAgent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.checkpoint = "tools/bleurt/bleurt/test_checkpoint"
        self.scorer = score.BleurtScorer(self.checkpoint)

    def handle_conversation(self, phrase_agent_ask: str, phrase_user_answer: str):
        self_answer_prompt = f"Answer the following question with the form of text only: {phrase_agent_ask}"
        phrase_agent_self_answer = self.deepseek_chat(self_answer_prompt)

        similarity_score = self.cal_semantic_similarity(phrase_agent_self_answer, phrase_user_answer)
        print(f"Semantic similarity score: {similarity_score}")

        if similarity_score < 0.5:
            source_text = phrase_agent_ask
            source_readability = self.cal_readability(phrase_agent_ask)
            target_readability = self.cal_readability(phrase_user_answer)

            prompt = self.generate_prompt(source_text, source_readability, target_readability)
            
            adjusted_text = self.deepseek_chat(prompt)   
      
            
        else:
            adjusted_text = phrase_agent_ask
    
        return adjusted_text
    
    # 给VR的接口：返回的分数
    def VR_score_and_similarity(self, phrase_agent_ask: str, phrase_user_answer: str):

        agent_ask_score = self.cal_readability(phrase_agent_ask)
        user_answer_score = self.cal_readability(phrase_user_answer)
        similarity_score = self.cal_semantic_similarity(phrase_agent_ask, phrase_user_answer)
        return agent_ask_score, user_answer_score, similarity_score

# 实例化
eval_agent = ScoreAgent(
    "eval_agent",
    system_message="You are an evaluation assistant. Your role is to evaluate the conversation between the agent and the user.",
    llm_config=blue_config_transformed1,
    is_termination_msg=lambda msg: "thank you" in msg["content"].lower() or "goodbye" in msg["content"].lower(),
    human_input_mode="NEVER",
)

# 模拟对话场景
phrase_agent_ask = "What is the capital of France?"
print(f"Agent asks: {phrase_agent_ask}")

# 使用 deepseek_chat 生成代理的自我回答
self_answer_prompt = f"Answer the following question with the form of text only: {phrase_agent_ask}"
phrase_agent_self_answer = deepseek_chat(self_answer_prompt)
print(f"Agent self-answer: {phrase_agent_self_answer}")

# 假设用户提供的答案
phrase_user_answer = "The capital of France is Paris."
print(f"User answer: {phrase_user_answer}")

# 计算语义相似度
similarity_score = cal_semantic_similarity(phrase_agent_self_answer, phrase_user_answer)
print(f"Semantic similarity score: {similarity_score}")

print(f"The whole round: {phrase_user_answer}")
