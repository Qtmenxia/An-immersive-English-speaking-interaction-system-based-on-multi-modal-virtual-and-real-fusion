import asyncio
import json
import time
import autogen
from autogen.io import IOWebsockets
from flask import Flask, jsonify
from flask_sock import Sock
from websockets.sync.client import connect as ws_connect
from autogen import AssistantAgent, GroupChat, GroupChatManager
import threading
from agents.group.RecorderAgent import RecorderAgent
from agents.group.UserConversationAgent import MyConversableAgent
from agents.group.EvaluationAgent import EvaluationAgent
from tools.ClientContext import ClientContext
from tools.utils import extract_agent_info, extract_user_name

app = Flask(__name__)
sock = Sock(app)

gpt_config = {
    "cache_seed": None,
    "config_list": [
        {"model": "doubao-lite-128k", "api_key": "sk-9MEPSX1IHIrlX7nP4b1b55849fE54535Af6e30Ae2dFdDe14",
         "base_url": "https://api.v3.cm/v1",
         }
    ],
    "timeout": 100,
    "stream": True
}

task_description = """Let the waiter and the customer complete the process of "see the menu-order-serve-pay".
If the customer pays, output "TERMINATE"."""

# 定义服务员和记录员 Agent
recorder = RecorderAgent(
    name="Recorder",
    llm_config=gpt_config,  # 使用传入的配置
    system_message=(
        "Track and report the state transitions for the waiter.Speak in a fixed format:\n"
        "first line: 'The waiter`s action is XX'\n"  # 加快传输，先只输出动作状态
    ),
    description="I am **ONLY** allowed to speak **immediately** after the waiter.",
    action_set=["need_pay", "deliver_food", "running", "sitting", "idle", "clapping", "walking"],
)

# 服务员 Agent
waiter = AssistantAgent(
    name="Waiter",
    llm_config=gpt_config,
    system_message="You are a fast-food restaurant server. Your role is to greet the customer, take their order, "
                   "offer suggestions, answer questions, confirm the order, and handle payment. After the customer "
                   "is done ordering, you should thank them and tell them their order number. "
                   "When the user finishes ordering, you should command them to pay immediately."
                   "You can ask the customer the food they want, or you can suggest some of the available food."
                   "Here's the menu you can offer: "
                   "Burger : Hamburger - $4, Double Hamburger - $5, Cheeseburger - $4.5  Double Cheeseburger - $6, "
                   "Sandwich : - Chicken Sandwich - $5,"
                   "Fries : Small French Fries - $4.5, Medium French Fries - $5.5, Large French Fries - $6.5, "
                   "Fries : Coke - $2,Lemonade - $3 ."
                   "You must always answered in the fixed format:"
                   "first line: 'Start'"
                   "second line: Real conversational content"
                   "last line: 'End'",
    description="I am **ONLY** allowed to speak **immediately** after the user.",
)

# Evaluation Agent
evaluation_agent = EvaluationAgent(
    name="Evaluator",
    llm_config=gpt_config,
    system_message="Evaluate the conversation between the waiter and the customer.",
    description="I evaluate the conversation for semantic similarity and readability.",
)

# 存储客户端上下文
client_contexts = {}


def handle_client(ws):
    """处理单个客户端的 WebSocket 连接"""
    client_id = id(ws)
    extra_input = ws.environ.get('QUERY_STRING', '')
    user_name = extract_user_name(extra_input)
    context = ClientContext(ws)
    client_contexts[client_id] = context
    context.clientName = user_name
    try:
        manage_client_chat(context)
    except Exception as e:
        print("error in manage_client_chat: " + str(e))
        ws.send(json.dumps({'error': str(e)}))
    finally:
        del client_contexts[client_id]


def manage_client_chat(context):
    """管理单个客户端的聊天流程"""
    ws = context.ws
    stream_tran = False
    sentence_buffer = ""
    # 添加对话历史记录
    conversation_history = {
        "waiter": [],
        "user": []
    }
    # 添加难度追踪
    current_difficulty = "normal"  # 可以是 "easy", "normal", "hard"

    while True:
        message = ws.receive()
        if not message:
            break

        data = json.loads(message)
        command = data.get("command")
        if command == "user_approach":
            context.chat_status = "ongoing"
            context.clear_queues()
            thread = threading.Thread(
                target=run_chat_ws,
                args=(ws, "user_name", context)
            )
            thread.start()
            while context.chat_status != "ended":
                if context.chat_status == "need_pay":
                    message = ws.receive()
                    data = json.loads(message)
                    command = data.get("command")
                    if command != " ":
                        ws.send(jsonify({'type': 'command', 'command': command}).data.decode('utf-8'))
                    if command == "user_paid":
                        context.chat_status = "deliver_food"
                        context.clear_queues()
                        ws.send(jsonify({'type': 'chat', 'text': "wait a second, I`ll deliver your food"}).data.decode(
                            'utf-8'))
                        ws.send(jsonify({'type': 'command', 'command': "deliver_food"}).data.decode('utf-8'))
                    else:
                        continue
                if context.chat_status == "deliver_food":
                    message = ws.receive()
                    data = json.loads(message)
                    command = data.get("command")
                    if command != " ":
                        ws.send(jsonify({'type': 'command', 'command': command}).data.decode('utf-8'))
                    if command == "deliver_food_end":
                        context.chat_status = "ongoing"
                        context.clear_queues()
                        ws.send(jsonify({'type': 'chat', 'text': "enjoy your food!"}).data.decode('utf-8'))
                    else:
                        continue
                if not context.chat_queue.empty():
                    msg = context.chat_queue.get()
                    # 判断是否处于流式传输状态
                    if stream_tran and msg != 'End':
                        # 拼接单词到缓冲区
                        sentence_buffer = sentence_buffer + msg + " "
                        # 检查是否构成一个句子
                        if msg.endswith(('.', '!', '?', ',')):
                            # 记录服务员的对话
                            if sentence_buffer.strip():
                                conversation_history["waiter"].append(sentence_buffer.strip())
                            ws.send(jsonify({'type': 'chat', 'text': sentence_buffer}).data.decode('utf-8'))
                            # 当对话累积到一定程度时进行评估
                            if len(conversation_history["waiter"]) > 0 and len(conversation_history["user"]) > 0:
                                last_waiter_msg = conversation_history["waiter"][-1]
                                last_user_msg = conversation_history["user"][-1]
                                
                                # 使用EvaluationAgent进行评估
                                evaluation_result = evaluation_agent.handle_conversation(
                                    last_waiter_msg,
                                    last_user_msg
                                )
                                
                                # 根据评估结果调整难度
                                if evaluation_result < 0.3:  # 用户理解困难
                                    current_difficulty = "easy"
                                elif evaluation_result > 0.7:  # 用户理解良好
                                    current_difficulty = "hard"
                                else:
                                    current_difficulty = "normal"
                                
                                # 发送评估结果到前端
                                ws.send(jsonify({
                                    'type': 'evaluation',
                                    'score': evaluation_result,
                                    'difficulty': current_difficulty
                                }).data.decode('utf-8'))
                            sentence_buffer = ""
                    if msg == 'Start':
                        stream_tran = True
                    if msg == 'End':
                        if sentence_buffer.strip():
                            ws.send(
                                jsonify({'type': 'chat', 'text': sentence_buffer}).data.decode('utf-8'))
                            sentence_buffer = ""
                        stream_tran = False
                if not context.response_queue.empty():
                    msg = context.response_queue.get()
                    str_data = json.dumps(msg)
                    action = extract_agent_info(str_data)
                    ws.send(jsonify({'type': 'command', 'command': action}).data.decode('utf-8'))
                    if action == 'need_pay':
                        ws.send(jsonify({'type': 'chat', 'text': "You can swipe your card on this terminal when "
                                                                 "you're ready to pay."}).data.decode('utf-8'))
                        context.chat_status = "need_pay"
                elif context.chat_status == "inputting" and context.user_queue.empty():
                    msg = ws.receive()
                    if msg:
                        data = json.loads(msg).get("text")
                        context.user_queue.put(data)
                        # 记录用户的对话
                        conversation_history["user"].append(data)
                        context.user_queue.put(data)
                        sentence_buffer = ""
                time.sleep(0.01)


def create_userproxy(context):
    # 客户（用户代理）Agent
    user_proxy = MyConversableAgent(
        name=context.clientName,
        context=context,
        system_message="Come into the restaurant and have a meal.",
        code_execution_config=False,
        is_termination_msg=lambda msg: "TERMINATE" in msg["content"],
        human_input_mode="ALWAYS",
    )

    def print_messages(recipient, messages, sender, config):
        content = messages[-1]['content']
        if all(key in messages[-1] for key in ['name']):
            context.response_queue.put({'user': messages[-1]['name'], 'message': content})
        elif messages[-1]['role'] == 'user':
            context.response_queue.put({'user': sender.name, 'message': content})
        else:
            context.response_queue.put({'user': recipient.name, 'message': content})

        return False, None

    user_proxy.register_reply(
        [autogen.Agent, None],
        reply_func=print_messages,
        config={"callback": None},
    )

    return user_proxy


portCounter = 8000


def run_chat_ws(ws, user_name, context):
    global portCounter

    def on_connect(iostream: IOWebsockets) -> None:
        userproxy = create_userproxy(context)
        manager, assistants = create_groupchat(userproxy)
        asyncio.run(initiate_chat(userproxy, manager, f"I`m coming"))

    try:
        with IOWebsockets.run_server_in_thread(on_connect=on_connect, port=portCounter) as uri:
            portCounter = portCounter + 1
            if portCounter > 10000:
                portCounter = 8000
            # 建立流式传输
            with ws_connect(uri) as websocket:
                while True:
                    message = websocket.recv()
                    message = message.decode("utf-8") if isinstance(message, bytes) else message
                    context.chat_queue.put(message)
                    print(message, end="", flush=True)
                    if "TERMINATE" in message:
                        break
    except Exception as e:
        context.chat_status = "error"
        context.response_queue.put({'user': "System", 'message': f"An error occurred: {str(e)}"})


async def initiate_chat(agent, recipient, message):
    result = await agent.a_initiate_chat(recipient, message=message, clear_history=False)
    return result


def create_groupchat(user_proxy):
    # 定义代理间的交互逻辑图
    graph_dict = {
        user_proxy: [waiter],
        waiter: [recorder],
        recorder: [evaluation_agent],
        evaluation_agent: [user_proxy],
    }
    group_chat = GroupChat(
        agents=[user_proxy, recorder, waiter, evaluation_agent],
        messages=[],
        max_round=25,
        allow_repeat_speaker=None,
        speaker_transitions_type="allowed",
        allowed_or_disallowed_speaker_transitions=graph_dict
    )
    # 创建 GroupChatManager
    manager = GroupChatManager(
        groupchat=group_chat,
        llm_config=gpt_config,
        is_termination_msg=lambda msg: msg.get("content", "").rstrip().endswith("TERMINATE"),
        code_execution_config=False,
    )

    return manager, [recorder, waiter, user_proxy]


@sock.route('/fast-food-restaurant/agent')
def agent_socket(ws):
    """WebSocket 路由入口"""
    handle_client(ws)


def main():
    app.run(host='0.0.0.0', port=5008, debug=True)


if __name__ == "__main__":
    main()

