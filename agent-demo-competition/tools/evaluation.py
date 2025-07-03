from openai import OpenAI
import time
import tools.LEXILE as LEXILE
from bleurt import score

# 计算可读性
def cal_readablility(phrase):
    read_score = LEXILE.LEXIE(phrase)
    return read_score

# 计算语义相似度
def cal_semantic_similarity(phrase1, phrase2):
    checkpoint = "C:\\Users\\15211\\Desktop\\wuweidihuangwan\\agent-demo-competition\\tools\\bleurt\\bleurt\\test_checkpoint"
    scorer = score.BleurtScorer(checkpoint)
    scores = scorer.score(references=[phrase1], candidates=[phrase2])
    assert isinstance(scores, list) and len(scores) == 1
    return scores[0]

# Deepseek api调用
def deepseek_chat(message):
    client = OpenAI(api_key="sk-3f99a17dd45f492bafa03a26276f25a0", base_url="https://api.deepseek.com")
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": message},
        ],
        stream=False,
        temperature= 1.3
    )
    return response.choices[0].message.content

# 生成零样本 prompt
def generate_prompt(source_text, source_lexile, target_lexile):
    """
    生成零样本prompt，包含动态设置的Lexile level和TEXT。

    :param source_text: 原始文本
    :param source_lexile: 原始文本的Lexile级别
    :param target_lexile: 目标Lexile级别
    :return: 生成的零样本prompt字符串
    """
    message = f"""
A Lexile measure is defined as "the numeric representation of an individual’s reading ability or a text’s readability (or difficulty)," where lower scores reflect easier readability and higher scores indicate harder readability.

In this task, we are trying to rewrite a given text into the target Lexile level and keep the original meaning and information. Given the original draft (Lexile = {source_lexile}):

[TEXT START]
{source_text}
[TEXT END]

Rewrite the above text to the difficulty level of Lexile = {target_lexile}.
"""
    return message

# 给VR的接口：返回的分数
def VR_score_and_similarity(self, phrase_agent_ask: str, phrase_user_answer: str):
    agent_ask_score = self.cal_readability(phrase_agent_ask)
    user_answer_score = self.cal_readability(phrase_user_answer)
    similarity_score = self.cal_semantic_similarity(phrase_agent_ask, phrase_user_answer)
    return agent_ask_score, user_answer_score, similarity_score

# 主程序
if __name__ == "__main__":
    api_key = "sk-3f99a17dd45f492bafa03a26276f25a0"  

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

    # 根据语义相似度决定是否调整文本
    if similarity_score < 0.5:
        source_text = phrase_agent_ask
        source_readability = cal_readablility(phrase_agent_ask)
        target_readability = cal_readablility(phrase_user_answer)

        prompt = generate_prompt(source_text, source_readability, target_readability)
        print(f"Generated prompt: {prompt}")

        # 调用 deepseek_chat 生成调整后的文本
        strat = time.time()
        adjusted_text = deepseek_chat(prompt)
        end = time.time()

        print(f"Adjusted text: {adjusted_text}")
        print(f"deepseek_chat 此次调用花费时间为：{(end - strat):.4f}秒")

    else:
        # 继续进行该水平的对话
        print("Semantic similarity is high. Continue with the current conversation.")
        