from multiprocessing import Process, Queue, Manager, Value
from client import Client
from db import DB
import selectors


class Worker:
    def __init__(self, worker_no: int, conn_info: dict, db: DB) -> None:
        self.worker_no = Manager().Value('i', worker_no)
        self.conn_info = conn_info
        self.queue_add = Queue()
        self.queue_chat = db.queue_chat
        self.channels = Manager().dict()

    def start(self):
        self.process = Process(target=self.run, args=(
            self.worker_no, self.conn_info, self.channels, self.queue_add, self.queue_chat))
        self.process.daemon = True
        self.process.start()

    # def start_stream(self, conn_info: dict, channels: dict, queue_add: Queue, queue_chat: Queue):
    #     asyncio.run(self.run_stream(conn_info, channels, queue_add, queue_chat))
    #     print('error')

    def run(self, worker_no: Value, conn_info: dict, channels: dict, queue_add: Queue, queue_chat: Queue):
        print('worker', worker_no.value, 'started')
        clients = []
        sel = selectors.DefaultSelector()

        while True:
            clients_remove = []
            for client in clients:
                if client.stopped:
                    clients_remove.append(client)

            for client in clients_remove:
                print('worker', worker_no.value, '-=', client.channel)
                sel.unregister(client.sck)
                clients.remove(client)
                del channels[client.channel]

            while not queue_add.empty():
                channel = queue_add.get()
                if channel not in channels:
                    print('worker', worker_no.value, '+=', channel)
                    client = Client(channel, conn_info, queue_chat)
                    sel.register(client.sck, selectors.EVENT_READ,
                                 client.receive)
                    client.connect()
                    clients.append(client)
                    channels[channel] = 0
            # 클라이언트의 접속 또는 접속된 클라이언트의 데이터 요청을 감시
            events = sel.select(timeout=1)
            for key, mask in events:
                callback = key.data  # 실행할 함수
                callback()  # 이벤트가 발생한 소켓을 인수로 실행할 함수를 실행한다.

    def add(self, channel):
        self.queue_add.put(channel)

    def size(self):
        return len(self.channels)

    def contains(self, channel):
        return channel in self.channels
