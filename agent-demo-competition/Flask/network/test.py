from websockets.sync.client import connect as ws_connect
from datetime import datetime
import autogen
from autogen.io.websockets import IOWebsockets


# 仅作模拟 TODO 确认与VR端传输端口后作更新
def websocket_connection(port: int):
    def on_connect(iostream: IOWebsockets) -> None:
        print(f" - on_connect(): Connected to client using IOWebsockets {iostream}", flush=True)
        print(" - on_connect(): Receiving message from client.", flush=True)

        # 1. Receive Initial Message
        initial_msg = iostream.input()

        # 2. Setup agents and register functions
        agent, user_proxy = setup_agents_and_register_functions(iostream, initial_msg)

        # 3. Handle agent response
        handle_agent_response(iostream, agent, user_proxy, initial_msg)

    with IOWebsockets.run_server_in_thread(on_connect=on_connect, port=port) as uri:
        print(f" - WebSocket server running on {uri}.", flush=True)

        with ws_connect(uri) as websocket:
            print(f" - Connected to server on {uri}", flush=True)
            print(" - Sending message to server.", flush=True)
            websocket.send("Check out the weather in Paris and write a poem about it.")

            while True:
                message = websocket.recv()
                message = message.decode("utf-8") if isinstance(message, bytes) else message
                print(message, end="", flush=True)

                if "TERMINATE" in message:
                    print()
                    print(" - Received TERMINATE message. Exiting.", flush=True)
                    break


config_list = [{"model": "gpt-3.5-turbo", "api_key": "sk-9MEPSX1IHIrlX7nP4b1b55849fE54535Af6e30Ae2dFdDe14",
                "base_url": "https://api.v3.cm/v1"}]

def setup_agents_and_register_functions(iostream: IOWebsockets, initial_msg: str):
    agent = autogen.ConversableAgent(
        name="chatbot",
        system_message="Complete a task given to you and reply TERMINATE when the task is done. If asked about the weather, use tool 'weather_forecast(city)' to get the weather forecast for a city.",
        llm_config={
            "config_list": config_list,
            "stream": True,
        },
    )

    user_proxy = autogen.UserProxyAgent(
        name="user_proxy",
        system_message="A proxy for the user.",
        is_termination_msg=lambda x: x.get("content", "") and x.get("content", "").rstrip().endswith("TERMINATE"),
        human_input_mode="NEVER",
        max_consecutive_auto_reply=10,
        code_execution_config=False,
    )

    # Define weather forecast function
    def weather_forecast(city: str) -> str:
        return f"The weather forecast for {city} at {datetime.now()} is sunny."

    # Register function
    autogen.register_function(
        weather_forecast, caller=agent, executor=user_proxy, description="Weather forecast for a city"
    )

    return agent, user_proxy


def handle_agent_response(iostream: IOWebsockets, agent, user_proxy, initial_msg: str):
    print(f" - on_connect(): Initiating chat with agent {agent} using message '{initial_msg}'", flush=True)
    user_proxy.initiate_chat(agent, message=initial_msg)


if __name__ == "__main__":
    websocket_connection(port=8765)
