from autogen import AssistantAgent
from tools.evaluation import (
    cal_readablility,
    cal_semantic_similarity,
    deepseek_chat,
    generate_prompt
)


class TeacherAgent(AssistantAgent):
    """英语教师代理，专门用于评估和提供语言学习反馈"""

    def __init__(self, name: str, llm_config: dict):
        system_message = (
            "You are an English teacher specializing in language learning feedback. "
            "Your job is to analyze the English usage of the user in the conversation, "
            "evaluate their vocabulary, grammar, fluency, and coherence, and provide constructive feedback.\n"
            "For each user response, you should:"
            "1. Calculate readability scores for both the agent's question and user's answer"
            "2. Calculate semantic similarity between expected answer and user's answer"
            "3. If semantic similarity is low (<0.5), suggest improvements using appropriate language level\n"
            "Format your response as follows:"
            "First line: 'Start'"
            "Second line: 'teacher'"
            "Third line: Analysis results in JSON format containing:"
            "- agent_readability: <score>"
            "- user_readability: <score>"
            "- semantic_similarity: <score>"
            "- feedback: <your feedback based on the scores>"
            "- suggestions: <specific improvement suggestions>"
            "Last line: 'End'"
        )

        super().__init__(
            name=name,
            system_message=system_message,
            llm_config=llm_config,
            description="I am **ONLY** allowed to speak **immediately** after the recorder."
        )

        # 注册评估工具
        self.tools = {
            "cal_readablility": cal_readablility,
            "cal_semantic_similarity": cal_semantic_similarity,
            "deepseek_chat": deepseek_chat,
            "generate_prompt": generate_prompt
        }

    @property
    def tools(self):
        return self._tools

    @tools.setter
    def tools(self, value):
        if isinstance(value, dict):
            self._tools = value
        else:
            raise ValueError("tools必须为字典类型")

    def analyze_language(self, agent_text: str, user_text: str) -> dict:
        """分析用户语言使用情况"""
        agent_readability = self.tools["cal_readablility"](agent_text)
        user_readability = self.tools["cal_readablility"](user_text)
        semantic_similarity = self.tools["cal_semantic_similarity"](agent_text, user_text)

        return {
            "agent_readability": agent_readability,
            "user_readability": user_readability,
            "semantic_similarity": semantic_similarity
        }

    def generate_improvement_suggestions(self, text: str, current_lexile: float, target_lexile: float) -> str:
        """生成改进建议"""
        if current_lexile < target_lexile:
            prompt = self.tools["generate_prompt"](text, current_lexile, target_lexile)
            return self.tools["deepseek_chat"](prompt)        
        return text