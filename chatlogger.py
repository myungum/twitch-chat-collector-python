import logging

class ChatLogger(logging.Logger):
    def chat(self, channel, msg):
        for handler in self.handlers:
            handler.chat(channel, msg)
    
    def start_push(self):
        for handler in self.handlers:
            handler.start_push()