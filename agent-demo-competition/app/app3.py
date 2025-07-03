import asyncio
import json
import time
from flask import Flask, jsonify
from flask_sock import Sock
from websockets.sync.client import connect as ws_connect
import threading
from agents.group.RecorderAgent import RecorderAgent
from agents.group.UserConversationAgent import MyConversableAgent
from tools.ClientContext import ClientContext
from tools.utils import extract_agent_info, extract_user_name
from websockets import connect as async_connect
from tools.evaluation import (
    cal_readablility,
    cal_semantic_similarity,
    deepseek_chat,
    generate_prompt
)
from tools.text2img import text_to_img
from agents.group.TeacherAgent import TeacherAgent
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import tensorflow_probability as tfp
tfd = tfp.distributions
import nltk
nltk.data.path.append(r'C:\Users\32928\AppData\Roaming\nltk_data')
# from agents.Model.blue_adapter import BlueChatCompletion as ChatCompletion
import os, openai
from agents.Model.blue_adapter import BlueChatCompletion
openai.ChatCompletion = BlueChatCompletion
openai.api_key = os.getenv("DUMMY_KEY","sk-dummy")
openai.api_base = os.getenv("DUMMY_BASE","https:/dummy.local")
openai.api_type = "open_ai"
openai.api_version = ""
import autogen
from autogen.io import IOWebsockets
from autogen import AssistantAgent, GroupChat, GroupChatManager
# 不要改以上部分的顺序
app = Flask(__name__)
sock = Sock(app)

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

task_description = """Let the waiter and the customer complete the process of "see the menu-order-serve-pay".
If the customer pays, output "TERMINATE"."""

# 定义服务员和记录员 Agent
recorder = RecorderAgent(
    name="Recorder",
    llm_config=blue_config_transformed1,  # 使用传入的配置
    system_message=(
        "Track and report the state transitions for the waiter."
        "When user need to pay,you should say 'need_pay'."
        "When user ask to pay ,you should say 'need_pay'."
        "When waiter ask user to pay,you should say 'need_pay'."
        "Speak in a fixed format:\n"
        "first line: 'The waiter`s action is XX'\n"  # 加快传输，先只输出动作状态
    ),
    description="I am **ONLY** allowed to speak **immediately** after the waiter.",
    action_set=["need_pay", "sitting", "idle", "clapping", "walking"],
)

teacher = TeacherAgent(
    name="teacher",
    llm_config=blue_config_transformed1
)

father = AssistantAgent(
    name="father",
    llm_config=blue_config_transformed1,
    system_message="You are a father dining with your daughter in a fast-food restaurant. "
                   "You are responsible for helping your daughter order food, making small talk, "
                   "and ensuring she eats well. You should ask about the menu if needed and confirm "
                   "your order with the waiter before paying. "
                   "You like talking with order people who have a lunch in the restaurant and have a conversion actively"
                   "You are caring, patient, and sometimes make jokes to keep the conversation light."
                   "You must always answer in the fixed format:"
                   "First line: 'Start'"
                   "Second line: 'father'"
                   "Third line: Real conversational content"
                   "Last line: 'End'",
    description="A caring and humorous father dining with his daughter.",
)

daughter = AssistantAgent(
    name="daughter",
    llm_config=blue_config_transformed1,
    system_message="You are a young girl dining with your father in a fast-food restaurant. "
                   "You love burgers and fries, but you might ask your father for recommendations. "
                   "Sometimes, you get excited about your favorite food, or you might be indecisive. "
                   "You can also ask questions about the menu and express your emotions naturally."
                   "You must always answer in the fixed format:"
                   "First line: 'Start'"
                   "Second line: 'daughter'"
                   "Third line: Real conversational content"
                   "Last line: 'End'",
    description="A cheerful and curious daughter enjoying a meal with her father.",
)

# 服务员 Agent
waiter = AssistantAgent(
    name="waiter",
    llm_config=blue_config_transformed1,
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
                   "Second line:'waiter'"
                   "Third line: Real conversational content"                  
                   "last line: 'End'",
    description="I am **ONLY** allowed to speak **immediately** after the teacher.",
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

class StoppableChatThread(threading.Thread):
    def __init__(self, ws, user_name, context):
        super().__init__()
        self.ws = ws
        self.user_name = user_name
        self.context = context
        self._stop_event = threading.Event()  # 用于控制线程退出的标志位

    def stop(self):
        self._stop_event.set()  # 设置标志位，通知线程退出

    def run(self):
        run_chat_ws(self.ws, self.user_name, self.context, self._stop_event)


def manage_client_chat(context):
    """管理单个客户端的聊天流程"""
    ws = context.ws
    stream_tran = False
    sentence_buffer = ""
    agent = ""
    flag=0#跳过teacher第一轮回答
    while True:
        message = ws.receive()#chat和command两类消息
        if not message:
            break

        data = json.loads(message)
        command = data.get("command")
        if command == "user_approach": #对waitor
            context.chat_status = "ongoing"
            context.clear_queues()
            thread = StoppableChatThread(ws, "user_name", context) #线程内部会调用run_chat_ws函数，包括groupchat
            thread.start()
            while context.chat_status != "ended":
                if context.chat_status == "need_pay":
                    message = ws.receive()
                    data = json.loads(message)
                    command = data.get("command")
                    # if command != " ":
                    #     ws.send(jsonify({'agent':'waiter','type': 'command', 'command': command}).data.decode('utf-8'))
                    if command == "user_paid":
                        context.chat_status = "deliver_food"
                        context.clear_queues()
                        ws.send(jsonify({'agent':'waiter','type': 'chat', 'text': "wait a second, I`ll deliver your food"}).data.decode(
                            'utf-8'))
                        ws.send(jsonify({'agent':'waiter','type': 'command', 'command': "deliver_food"}).data.decode('utf-8'))
                    else:
                        continue
                if context.chat_status == "deliver_food":
                    message = ws.receive()
                    data = json.loads(message)
                    command = data.get("command")
                    # if command != " ":
                    #     ws.send(jsonify({'agent':'waiter','type': 'command', 'command': command}).data.decode('utf-8'))
                    if command == "deliver_food_end":
                        context.clear_queues()
                        ws.send(jsonify({'agent':'waiter','type': 'chat', 'text': "enjoy your food!"}).data.decode('utf-8'))
                        context.chat_status = "ended"
                        thread.stop()
                        thread.join()
                        flag=0
                    else:
                        continue
                if not context.chat_queue.empty():
                    msg = context.chat_queue.get()
                    # 判断是否处于流式传输状态
                    if isinstance(msg, bytes):
                        msg = msg.decode('utf-8')
                    if stream_tran and msg != 'End':
                        # 拼接单词到缓冲区
                        sentence_buffer = sentence_buffer + msg + " "
                        # 对于 teacher 的反馈信息特殊处理
                        if agent == 'teacher' and '{' in msg: #groupchat当前发言的agent
                            # 收集完整的 JSON 字符串
                            json_buffer = msg #流式传输，积攒到完整的json字符串
                            while not json_buffer.endswith('}'):
                                if not context.chat_queue.empty():
                                    next_msg = context.chat_queue.get()
                                    if next_msg != 'End':
                                        json_buffer += next_msg

                            try:
                                feedback_data = json.loads(json_buffer)
                                # 提取 teacher 的回复内容到 teacher_text 变量中
                                teacher_text = feedback_data.get('feedback')
                                print("Teacher replied:", teacher_text)  # 打印 teacher_text 以便调试
                                img_url = text_to_img(teacher_text)  # 调用 text2img 得到图片url

                                ws.send(jsonify({
                                    'type': 'feedback',
                                    'data': {
                                        'agent_readability': feedback_data.get('agent_readability'),
                                        'user_readability': feedback_data.get('user_readability'),
                                        'semantic_similarity': feedback_data.get('semantic_similarity'),
                                        'feedback': teacher_text,
                                        'img_url': img_url
                                    },
                                    'agent': 'teacher'
                                }).data.decode('utf-8'))
                            except json.JSONDecodeError:
                                print("Error parsing teacher feedback JSON")
                        else:
                            if msg.endswith(('.', '!', '?', ',')):
                                ws.send(jsonify({'agent': agent, 'type': 'chat', 'text': sentence_buffer}).data.decode(
                                    'utf-8'))
                                sentence_buffer = ""
                    if msg == 'Start': 
                        stream_tran = True
                        context.chat_queue.get()
                        msg = context.chat_queue.get()
                        while not msg.endswith('\n'):
                            msg = msg + context.chat_queue.get()
                        agent = msg.strip() #反馈信息给大模型
                    if msg == 'End':
                        if sentence_buffer.strip():
                            ws.send(
                                jsonify({'agent':agent.lower(),'type': 'chat', 'text': sentence_buffer}).data.decode('utf-8'))
                            sentence_buffer = ""
                        stream_tran = False
                        agent = ''
                        flag=1
                if not context.response_queue.empty():
                    msg = context.response_queue.get()
                    str_data = json.dumps(msg)
                    action = extract_agent_info(str_data)
                    ws.send(jsonify({'agent':'waiter','type': 'command', 'command': action}).data.decode('utf-8'))
                    if action == 'need_pay':
                        ws.send(jsonify({'agent':'waiter','type': 'chat', 'text': "You can swipe your card on this terminal when "
                                                                 "you're ready to pay."}).data.decode('utf-8'))
                        context.chat_status = "need_pay"
                elif context.chat_status == "inputting" and context.user_queue.empty(): #等待用户说话
                    msg = ws.receive()
                    if msg:
                        data = json.loads(msg).get("text")
                        context.user_queue.put(data)
                        sentence_buffer = ""
                time.sleep(0.01)
        if command == "user_come": #对父女
            if flag==0:
                ws.send(jsonify({'agent': 'daughter', 'type': 'chat', 'text': "Hey,your food looks delicious."}).data.decode(
                    'utf-8'))
                flag=1
            context.chat_status = "ongoing"
            context.clear_queues()
            thread = threading.Thread(
                target=run_chat2_ws,
                args=(ws, "user_name", context)
            )
            thread.start()
            while context.chat_status != "ended":
                if not context.chat_queue.empty():
                    msg = context.chat_queue.get()
                    # 判断是否处于流式传输状态
                    if isinstance(msg, bytes):
                        msg = msg.decode('utf-8')
                    if stream_tran and msg != 'End':
                        # 拼接单词到缓冲区
                        sentence_buffer = sentence_buffer + msg + " "
                        # 对于 teacher 的反馈信息特殊处理
                        if agent == 'teacher' and '{' in msg:
                            # 收集完整的 JSON 字符串
                            json_buffer = msg
                            while not json_buffer.endswith('}'):
                                if not context.chat_queue.empty():
                                    next_msg = context.chat_queue.get()
                                    if next_msg != 'End':
                                        json_buffer += next_msg

                            try:
                                feedback_data = json.loads(json_buffer)
                                ws.send(jsonify({
                                    'type': 'feedback',
                                    'data': {
                                        'agent_readability': feedback_data.get('agent_readability'),
                                        'user_readability': feedback_data.get('user_readability'),
                                        'semantic_similarity': feedback_data.get('semantic_similarity'),
                                        'feedback': feedback_data.get('feedback') #把前端收到的信息发送回去
                                    },
                                    'agent': 'teacher'
                                }).data.decode('utf-8'))
                            except json.JSONDecodeError:
                                print("Error parsing teacher feedback JSON")
                        else:
                            if msg.endswith(('.', '!', '?', ',')):
                                ws.send(jsonify({'agent': agent, 'type': 'chat', 'text': sentence_buffer}).data.decode(
                                    'utf-8'))
                                sentence_buffer = ""
                    if msg == 'Start':
                        stream_tran = True
                        context.chat_queue.get()
                        msg = context.chat_queue.get()
                        while not msg.endswith('\n'):
                            msg = msg + context.chat_queue.get()
                        agent = msg.strip()
                    if msg == 'End':
                        if sentence_buffer.strip():
                            ws.send(
                                jsonify({'agent':agent.lower(),'type': 'chat', 'text': sentence_buffer}).data.decode('utf-8'))
                            sentence_buffer = ""
                        stream_tran = False
                        agent = ''
                elif context.chat_status == "inputting" and context.user_queue.empty():# inputting等待用户说话
                    msg = ws.receive()
                    if msg:
                        data = json.loads(msg).get("text")
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


async def run_chat_ws_async(ws, user_name, context, stop_event):
    global portCounter
    def on_connect(iostream: IOWebsockets) -> None:
        userproxy = create_userproxy(context)
        chatmanager, assistants = create_groupchat(userproxy)
        asyncio.run(initiate_chat(userproxy, chatmanager, f"I`m coming"))

    try:
        with IOWebsockets.run_server_in_thread(on_connect=on_connect, port=portCounter) as uri:
            portCounter += 1
            if portCounter > 10000:
                portCounter = 8000

            # 使用异步 websockets 连接
            async with async_connect(uri) as websocket:
                while not stop_event.is_set():  # 检查标志位
                    try:
                        # 使用 asyncio.wait_for 实现超时
                        message = await asyncio.wait_for(websocket.recv(), timeout=1)
                        message = message.decode("utf-8") if isinstance(message, bytes) else message
                        context.chat_queue.put(message)
                        print(message, end="", flush=True)
                        if "TERMINATE" in message:
                            break
                    except asyncio.TimeoutError:
                        # 超时后检查外部标志位
                        if stop_event.is_set():
                            print("Thread stopped by external flag.")
                            break
                        continue
                    except Exception as e:
                        print(f"Error receiving message: {e}")
                        break
    except Exception as e:
        context.chat_status = "error"
        context.response_queue.put({'user': "System", 'message': f"An error occurred: {str(e)}"})
    finally:
        print("Chat thread stopped.")

def run_chat_ws(ws, user_name, context, stop_event):
    # 使用 asyncio.run 运行异步函数
    asyncio.run(run_chat_ws_async(ws, user_name, context, stop_event))

def run_chat2_ws(ws, user_name, context):
    global portCounter

    def on_connect(iostream: IOWebsockets) -> None:
        userproxy = create_userproxy(context)
        chatmanager, assistants = create_groupchat2(userproxy) #针对父女场景创建的groupchat
        asyncio.run(initiate_chat(daughter, chatmanager, f"Hey,your food looks delicious."))
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
                    #若消息是字节类型，则将其解码为字符串
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
    """
    创建一个多智能体聊天组和对应的聊天管理器。

    此函数定义了智能体之间的交互逻辑图，并使用该图创建一个 GroupChat 对象，
    然后基于该 GroupChat 对象创建一个 GroupChatManager 对象。

    :param user_proxy: 用户代理智能体，代表用户参与多智能体聊天。
    :return: 一个元组，包含 GroupChatManager 对象和参与聊天的智能体列表。
    """
    # 定义代理间的交互逻辑图
    graph_dict = {user_proxy: [teacher],
                  teacher: [waiter],
                  waiter: [recorder],
                  recorder: [user_proxy],
                  }
    # 创建 GroupChat 对象，用于管理多智能体之间的聊天
    group_chat = GroupChat(
        agents=[user_proxy, recorder, waiter,teacher],
        messages=[], #初始消息为空
        max_round=25, #聊天的最大轮数
        allow_repeat_speaker=None, #是否允许重复发言的代理，默认设置
        speaker_transitions_type="allowed", 
        allowed_or_disallowed_speaker_transitions=graph_dict
    )
    # 创建 GroupChatManager
    chatmanager = GroupChatManager(
        groupchat=group_chat,
        llm_config=blue_config_transformed1,
        # 定义终止消息的条件，当消息内容以 "TERMINATE" 结尾时终止聊天
        is_termination_msg=lambda msg: msg.get("content", "").rstrip().endswith("TERMINATE"),
        code_execution_config=False, #是否启用代码执行功能，默认关闭
    )

    return chatmanager, [recorder, waiter, user_proxy]

def create_groupchat2(user_proxy):
    # 定义代理间的交互逻辑图
    graph_dict = {user_proxy: [teacher],
                  teacher: [father],
                  father: [daughter],
                  daughter: [user_proxy],
                  }
    group_chat = GroupChat(
        agents=[user_proxy, father, daughter,teacher],
        messages=[],
        max_round=10, # 与create_groupchat不同，这里设置为10
        allow_repeat_speaker=None,
        speaker_transitions_type="allowed",
        allowed_or_disallowed_speaker_transitions=graph_dict
    )
    # 创建 GroupChatManager
    chatmanager = GroupChatManager(
        groupchat=group_chat,
        llm_config=blue_config_transformed1,
        is_termination_msg=lambda msg: msg.get("content", "").rstrip().endswith("TERMINATE"),
        code_execution_config=False,
    )

    return chatmanager, [user_proxy, father, daughter,teacher]

@sock.route('/fast-food-restaurant/agent')
def agent_socket(ws):
    """WebSocket 路由入口"""
    handle_client(ws)

def main():
    app.run(host='0.0.0.0', port=5008, debug=True)

if __name__ == "__main__":
    main()
