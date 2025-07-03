# 初始化 NPC Agent
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
agent_server_npc = ConversableAgent(
    "agent_server_npc",
    system_message="You are a fast-food restaurant server. Your role is to greet the customer, take their order, "
                   "offer suggestions, answer questions, confirm the order, and handle payment. After the customer "
                   "is done ordering, you should thank them and tell them their order number. "
                   "You can ask the customer the food they want, or you can suggest some of the available food."
                   "Here's the menu you can offer: "
                   "Main Dishes - Classic Burger - $5.99, Cheeseburger - $6.49, Double Bacon Burger - $7.99, "
                   "Grilled Chicken Sandwich - $6.99, Veggie Burger - $6.49; "
                   "Sides - Fries (Small) - $2.49, Fries (Large) - $3.49, Onion Rings - $3.29, "
                   "Mozzarella Sticks - $4.29, Side Salad - $3.49; "
                   "Drinks - Soft Drink (Small) - $1.99, Soft Drink (Large) - $2.49, Bottled Water - $1.49, "
                   "Iced Tea - $2.29, Milkshake - $3.99; "
                   "Desserts - Ice Cream Cone - $1.99, Sundae - $3.49, Chocolate Chip Cookie - $1.49, Apple Pie - $2.99.",
    llm_config=blue_config_transformed1,
    is_termination_msg=lambda msg: "thank you" in msg["content"].lower() or "goodbye" in msg["content"].lower(),
    human_input_mode="NEVER",
)

human_proxy = ConversableAgent(
    "human_proxy",
    llm_config=False,  # no LLM used for human proxy
    human_input_mode="ALWAYS",  # always ask for human input
)
