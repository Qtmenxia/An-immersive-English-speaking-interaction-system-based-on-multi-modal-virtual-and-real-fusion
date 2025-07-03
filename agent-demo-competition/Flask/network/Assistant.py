from flask_sock import Sock
import json
from agents.command.AssistantAgent import english_learning_agent
from Flask.app import app

sock = Sock(app)

# 维护连接的客户端列表
client_list = []


def get_response_from_agent(user_input):
    state, reply = english_learning_agent.receive_user_input(user_input)
    return state, reply


@sock.route('/Assistant/agent')
def fastfood_agent_socket(ws):
    # 将客户端添加到连接列表
    client_list.append(ws)

    # 从连接的 URL 中提取用户名
    user_name = ws.environ.get('QUERY_STRING', '')
    if isinstance(user_name, bytes):
        user_name = user_name.decode('utf-8')
    user_name = user_name.split('=')[1] if 'userName' in user_name else 'Guest'
    print(f'User {user_name} connected')

    # 向客户端发送欢迎消息
    response = {
        'type': 'chat',
        'data': f'Welcome {user_name}!'
    }
    ws.send(json.dumps(response))  # 发送数据

    try:
        while True:
            # 等待接收客户端的消息
            data = ws.receive()
            print(f'Received message: {data}')

            if data:
                # 解析收到的消息

                data_dict = json.loads(data, strict=False)

                # 判断消息类型并处理
                if data_dict.get('type') == 'chat':
                    user_input = data_dict.get('data')
                    # 调用 Agent 模块来生成回复
                    state, response_text = get_response_from_agent(user_input)
                    response = {
                        'type': 'chat',
                        'data': response_text
                    }
                    ws.send(json.dumps(response))
                    response = {
                        'type': 'command',
                        'data': state
                    }
                elif data_dict.get('type') == 'command':
                    command = data_dict.get('command')
                    command_data = data_dict.get('data', {})
                    # TODO: 根据指令进行相应操作
                    response = {
                        'type': 'command',
                        'data': f'Command received: {command}'
                    }
                else:
                    response = {
                        'type': 'chat',
                        'data': 'Unknown message type'
                    }

                # 将处理后的响应发送回客户端
                ws.send(json.dumps(response))

    except Exception as e:
        print(f'Error: {e}')

    finally:
        # 连接关闭时，移除客户端
        client_list.remove(ws)
        print(f'User {user_name} disconnected')

if __name__ == '__main__':
    app.run(debug=True)
