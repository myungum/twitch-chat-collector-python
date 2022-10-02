import socket
from db import DB
from datetime import datetime
from multiprocessing import Process, Queue
import asyncio


class Client:
    def __init__(self, host: str, port: int, token: str, user_name: str, channel: str, db: DB, status: dict) -> None:
        status['host'] = host
        status['port'] = port
        status['token'] = token
        status['user_name'] = user_name
        status['channel'] = channel
        status['stopped'] = False
        self.status = status

        self.channel = channel
        self.db = db
        self.is_stopped = False

    def stopped(self):
        return self.status['stopped']

    def start(self):
        self.process = Process(target=self.__run, args=(self.status, self.db.queue_chat))
        self.process.daemon = True
        self.process.start()

    def stop(self):
        self.process.terminate()
        self.process.join()
        self.is_stopped = True

    def __run(self, status: dict, queue_chat: Queue):
        async def receive(status: dict, queue_chat: Queue):
            host = status['host']
            port = status['port']
            token = status['token']
            user_name = status['user_name']
            channel = status['channel']
            reader: asyncio.StreamReader
            writer: asyncio.StreamWriter
            
            def split(data):
                for i in range(len(data) - 1):
                    if data[i] == b'\r'[0] and data[i + 1] == b'\n'[0]:
                        return i 
                return -1
            
            try:
                reader, writer = await asyncio.open_connection(host, port)

                writer.write('CAP REQ :twitch.tv/commands\r\n'.encode('utf-8'))
                writer.write('PASS {}\r\n'.format(token).encode('utf-8'))
                writer.write('NICK {}\r\n'.format(user_name).encode('utf-8'))
                writer.write('JOIN #{}\r\n'.format(channel).encode('utf-8'))
                await writer.drain()

                buffer = bytearray()
                while True:
                    buffer += await reader.read(1024 * 64)
                    idx = split(buffer)
                    if idx != -1:
                        message, buffer = buffer[:idx].decode('utf-8'), buffer[idx+2:]

                        # ping/pong
                        if message[:4] == 'PING':
                            writer.write('PONG{}\r\n'.format(message[4:]).encode('utf-8'))
                            await writer.drain()

                        queue_chat.put({
                            'channel': channel,
                            'message': message,
                            'datetime': datetime.now()
                            })


            except Exception as e:
                print(str(e))
                status['stopped'] = True
        asyncio.run(receive(status, queue_chat))
