import socket
from datetime import datetime
from multiprocessing import Queue
import traceback
import logging
from loghandler import LogHandler


class Client:
    def __init__(self, channel: str, conn_info: dict) -> None:
        super().__init__()
        self.channel = channel
        self.host = conn_info['chat_host']
        self.port = conn_info['chat_port']
        self.token = conn_info['chat_token']
        self.user_name = conn_info['chat_user_name']
        self.logger = logging.getLogger('root')
        self.sck = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.stopped = False
        self.buffer = bytearray()

    def split(self, data):
        for i in range(len(data) - 1):
            if data[i] == b'\r'[0] and data[i + 1] == b'\n'[0]:
                return i
        return -1

    def connect(self):
        try:
            self.sck.connect((self.host, self.port))
            self.sck.send('CAP REQ :twitch.tv/commands\r\n'.encode('utf-8'))
            self.sck.send('PASS {}\r\n'.format(self.token).encode('utf-8'))
            self.sck.send('NICK {}\r\n'.format(self.user_name).encode('utf-8'))
            self.sck.send('JOIN #{}\r\n'.format(self.channel).encode('utf-8'))
        except Exception as e:
            self.logger.error('({}) {}'.format(self.channel, str(e)))
            self.stopped = True

    def receive(self):
        try:
            # receive data
            received = self.sck.recv(1024 * 8)

            # disconnected
            if len(received) == 0:
                self.logger.info('({}) Connection has been closed'.format(self.channel))
                self.stopped = True
                return

            # add data to buffer
            self.buffer += received
            while not self.stopped:
                idx = self.split(self.buffer)
                if idx == -1:
                    return

                message, self.buffer = self.buffer[:idx].decode(
                    'utf-8'), self.buffer[idx+2:]
                # ping/pong
                if message[:4] == 'PING':
                    self.sck.send('PONG{}\r\n'.format(
                        message[4:]).encode('utf-8'))

                # push to db
                self.logger.log(LogHandler.CHAT_LOG_LEVEL_NO, message)
        except ConnectionError as e:
            self.logger.info('({}) {}'.format(self.channel, str(e)))
            self.stopped = True
        except Exception as e:
            self.logger.error('({}) {}'.format(self.channel, str(e)))
            self.stopped = True
