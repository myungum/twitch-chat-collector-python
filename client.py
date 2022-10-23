import socket
import logging
from datetime import datetime
from twitchapi import Channel

TIMEOUT = 600  # 10 minutes


class Client:
    def __init__(self, channel: Channel):
        self.channel = channel
        self.logger = logging.getLogger('root')
        self.sck = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.stopped = False
        self.buffer = bytearray()
        self.worker = None
        self.received_time = datetime.now()

    def connect(self):
        try:
            self.sck.connect((self.channel.host, self.channel.port))
            self.sck.send('CAP REQ :twitch.tv/commands\r\n'.encode('utf-8'))
            self.sck.send('PASS {}\r\n'.format(self.channel.token).encode('utf-8'))
            self.sck.send('NICK {}\r\n'.format(self.channel.user_name).encode('utf-8'))
            self.sck.send('JOIN #{}\r\n'.format(self.channel.name).encode('utf-8'))
        except Exception as e:
            self.logger.error('({}) {}'.format(self.channel.name, str(e)))
            self.stop()

    def stop(self, reason=None):
        if not self.stopped:
            self.stopped = True
            reason = '' if reason is None else '({})'.format(reason)
            log_msg = 'Connection with {} has been closed{}'.format(self.channel.name, reason)
            self.logger.info(log_msg)

    def close(self):
        self.stop()
        self.sck.close()

    def check_timeout(self):
        if self.stopped:
            return
        if (datetime.now() - self.received_time).total_seconds() < TIMEOUT:
            return
        self.stop('timeout')

    def receive(self):
        try:
            # receive data
            received = self.sck.recv(1024 * 8)

            # disconnect
            if len(received) == 0:
                self.stop('by remote')
            if self.stopped:
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
                self.received_time = now
        except ConnectionError as e:
            self.stop()
        except Exception as e:
            self.logger.error('({}) {}'.format(self.channel.name, str(e)))
            self.stop()
