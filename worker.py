from multiprocessing import Process, Queue, Manager, Value
from client import Client
import selectors
import logging
from loghandler import LogHandler


class Worker:
    def __init__(self, worker_no: int, conn_info: dict) -> None:
        self.name = 'worker {}'.format(worker_no)
        self.conn_info = conn_info
        self.queue_add = Queue()
        self.channels = Manager().dict()

    def start(self):
        self.process = Process(target=self.run, args=(self.name, self.conn_info, self.channels, self.queue_add))
        self.process.daemon = True
        self.process.start()

    def run(self, name: str, conn_info: dict, channels: dict, queue_add: Queue):
        print('{} started'.format(name))
        clients = []
        sel = selectors.DefaultSelector()
        logger = logging.getLogger('root')
        
        try:
            while True:
                clients_remove = []
                for client in clients:
                    if client.stopped:
                        clients_remove.append(client)

                for client in clients_remove:
                    logger.debug('{} -= {}'.format(name, client.channel))
                    sel.unregister(client.sck)
                    clients.remove(client)
                    del channels[client.channel]

                while not queue_add.empty():
                    channel = queue_add.get()
                    if channel not in channels:
                        logger.debug('{} += {}'.format(name, channel))
                        client = Client(channel, conn_info)
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
        except KeyboardInterrupt:
            pass

    def add(self, channel):
        self.queue_add.put(channel)

    def size(self):
        return len(self.channels)

    def contains(self, channel):
        return channel in self.channels
