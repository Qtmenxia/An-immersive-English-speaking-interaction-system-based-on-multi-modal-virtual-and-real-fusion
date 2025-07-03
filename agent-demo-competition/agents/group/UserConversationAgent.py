import asyncio
import autogen
import time

from tools.ClientContext import ClientContext


class MyConversableAgent(autogen.ConversableAgent):
    def __init__(self, context: ClientContext, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.context = context  # 保存ClientContext对象作为成员变量

    async def a_get_human_input(self, prompt: str) -> str:
        start_time = time.time()
        self.context.chat_status = "inputting"
        while True:
            if not self.context.user_queue.empty():
                input_value = self.context.user_queue.get()
                self.context.chat_status = "Chat ongoing"
                return input_value

            if time.time() - start_time > 600:
                self.context.chat_status = "ended"
                print("ended")
                return "exit"
            await asyncio.sleep(1)
