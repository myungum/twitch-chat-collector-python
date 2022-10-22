import socket
import logging
from collections import deque
from datetime import datetime
from twitchapi import Channel

HISTORY_SIZE = 30


class Client:
    def __init__(self, channel: Channel):
        self.channel = channel
        self.logger = logging.getLogger('root')
        self.sck = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.stopped = False
        self.buffer = bytearray()
        self.history = deque(maxlen=HISTORY_SIZE)
        self.worker = None

    def connect(self):
        try:
            self.sck.connect((self.channel.host, self.channel.port))
            self.sck.send('CAP REQ :twitch.tv/commands\r\n'.encode('utf-8'))
            self.sck.send('PASS {}\r\n'.format(self.channel.token).encode('utf-8'))
            self.sck.send('NICK {}\r\n'.format(self.channel.user_name).encode('utf-8'))
            self.sck.send('JOIN #{}\r\n'.format(self.channel.name).encode('utf-8'))
        except Exception as e:
            self.error(e)
            self.stop()

    def stop(self):
        if not self.stopped:
            self.stopped = True
            self.sck.close()
            self.logger.info(
                '({}) Connection has been closed'.format(self.channel.name))

    def error(self, e: Exception):
        self.logger.error('({}) {}'.format(self.channel.name, str(e)))

    def chats_per_sec(self):
        if len(self.history) <= 1:
            return 0

        seconds = (self.history[-1] - self.history[0]).total_seconds()
        if seconds == 0:
            return 0

        return len(self.history) / seconds

    def receive(self):
        try:
            # receive data
            received = self.sck.recv(1024 * 8)

            # disconnected
            if len(received) == 0 or self.stopped:
                self.stop()
                return

            # add data to buffer
            self.buffer += received
            args = self.buffer.split(b'\r\n')
            self.buffer = args[-1]
            for arg in args[:-1]:
                message = arg.decode('utf-8')
                # ping/pong
                if message[:4] == 'PING':
                    self.sck.send('PONG{}\r\n'.format(
                        message[4:]).encode('utf-8'))
                # push to db
                now = datetime.now()
                self.logger.chat(self.channel.name, message, now)
                self.history.append(now)

        except ConnectionError as e:
            self.stop()
        except Exception as e:
            self.error(e)
            self.stop()
