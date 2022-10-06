from multiprocessing import Process, Queue, Manager, Value
from client import Client
import selectors
import logging
from loghandler import LogHandler


class Worker:
    def __init__(self, worker_no: int, conn_info: dict, queue_chat: Queue) -> None:
        self.worker_no = Manager().Value('i', worker_no)
        self.conn_info = conn_info
        self.queue_add = Queue()
        self.queue_chat = queue_chat
        self.channels = Manager().dict()

    def start(self):
        self.process = Process(target=self.run, args=(
            self.worker_no, self.conn_info, self.channels, self.queue_add, self.queue_chat))
        self.process.daemon = True
        self.process.start()

    def run(self, worker_no: Value, conn_info: dict, channels: dict, queue_add: Queue, queue_chat: Queue):
        print('worker', worker_no.value, 'started')
        clients = []
        sel = selectors.DefaultSelector()
         # logger
        logger = logging.getLogger('root')
        logger.setLevel(logging.DEBUG)
        logHandler = LogHandler(
            level=logging.DEBUG, db_host=conn_info['db_host'], db_port=conn_info['db_port'], db_name=conn_info['db_name'])
        logger.addHandler(logHandler)

        while True:
            clients_remove = []
            for client in clients:
                if client.stopped:
                    clients_remove.append(client)

            for client in clients_remove:
                logger.debug('worker {} -= {}'.format(worker_no.value, client.channel))
                sel.unregister(client.sck)
                clients.remove(client)
                del channels[client.channel]

            while not queue_add.empty():
                channel = queue_add.get()
                if channel not in channels:
                    logger.debug('worker {} -= {}'.format(worker_no.value, channel))
                    client = Client(channel, conn_info, queue_chat)
                    sel.register(client.sck, selectors.EVENT_READ,
                                 client.receive)
                    client.connect()
                    clients.append(client)
                    channels[channel] = 0
            # get read events
            events = sel.select(timeout=1)
            for key, mask in events:
                receive = key.data  # callback function
                receive()

    def add(self, channel):
        self.queue_add.put(channel)

    def size(self):
        return len(self.channels)

    def contains(self, channel):
        return channel in self.channels
