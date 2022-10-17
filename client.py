import socket
import logging


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

    def connect(self):
        try:
            self.sck.connect((self.host, self.port))
            self.sck.send('CAP REQ :twitch.tv/commands\r\n'.encode('utf-8'))
            self.sck.send('PASS {}\r\n'.format(self.token).encode('utf-8'))
            self.sck.send('NICK {}\r\n'.format(self.user_name).encode('utf-8'))
            self.sck.send('JOIN #{}\r\n'.format(self.channel).encode('utf-8'))
        except Exception as e:
            self.error(e)
            self.stop()

    def stop(self):
        if not self.stopped:
            self.stopped = True
            self.sck.close()
            self.logger.info(
                '({}) Connection has been closed'.format(self.channel))

    def error(self, e: Exception):
        self.logger.error('({}) {}'.format(self.channel, str(e)))

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
                self.logger.chat(self.channel, message)

        except ConnectionError as e:
            self.stop()
        except Exception as e:
            self.error(e)
            self.stop()
