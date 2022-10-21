import logging
from datetime import datetime


class ChatLogger(logging.Logger):
    def chat(self, channel: str, msg: str, datetime: datetime):
        for handler in self.handlers:
            handler.chat(channel, msg, datetime)

    def start_push(self):
        for handler in self.handlers:
            handler.start_push()
