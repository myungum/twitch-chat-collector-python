from db import DB
from client import Client
import time
import asyncio

class Server:
    def __init__(self, chat_host: str, chat_port: int,
                 chat_token: str, chat_user_name: str,
                 db_host: str, db_port: int, db_name: str) -> None:
        self.chat_host = chat_host
        self.chat_port = chat_port
        self.chat_token = chat_token
        self.chat_user_name = chat_user_name

        self.db = DB(db_host, db_port, db_name, dict())
        self.clients = dict()

    def start(self):
        while True:
            # add
            channels = self.db.get_live_channels()
            for channel in channels:
                if channel not in self.clients:
                    client = Client(self.chat_host, self.chat_port, self.chat_token,
                                    self.chat_user_name, channel, self.db, dict())
                    client.start()
                    self.clients[client.channel] = client
                    time.sleep(1)

            # remove
            stopped_channels = []
            for channel, client in self.clients.items():
                if client.stopped():
                    stopped_channels.append(channel)
            for channel in stopped_channels:
                del self.clients[channel]

            time.sleep(1)

    def stop(self):
        for channel, client in self.clients.items():
            client.stop()