from flask import Flask, render_template, request, jsonify

from agents.chat.fastfoodAgent import agent_server_npc

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/fast_food')
def fast_food():
    return render_template('fast_food.html')


def get_response_from_agent(user_input):
    reply = agent_server_npc.generate_reply(
        messages=[{"content": user_input, "role": "user"}]
    )
    return reply


@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get('message')
    # 调用agent 模块来处理对话
    response = get_response_from_agent(user_input)  # 替换为实际的调用
    return jsonify({'response': response})


if __name__ == '__main__':
    app.run(debug=True)


