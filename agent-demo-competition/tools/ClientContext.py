import queue


class ClientContext:
    """每个客户端的上下文信息，包括状态、队列和 WebSocket"""

    def __init__(self, ws):
        self.ws = ws
        self.clientName = ''
        self.chat_status = "waiting"
        self.chat_queue = queue.Queue()
        self.response_queue = queue.Queue()
        self.user_queue = queue.Queue()

    def clear_queues(self):
        """清空上下文中的队列"""
        self.chat_queue.queue.clear()
        self.response_queue.queue.clear()
        self.user_queue.queue.clear()