from multiprocessing import Process, Queue, Manager, Value
from client import Client
from selectors import DefaultSelector, EVENT_READ
import logging
from logging import Logger
from twitchapi import Channel


class Worker:
    def __init__(self, worker_no: int, conn_info: dict, channels: dict) -> None:
        self.worker_no = worker_no
        self.name = 'worker {}'.format(worker_no)
        self.conn_info = conn_info
        self.channels = channels
        self.logger: Logger = logging.getLogger('root')
        self.queue_add = Manager().Queue()
        self.queue_remove = Manager().Queue()
        self.viewer_count = Value('i', 0)

    def start(self):
        self.process = Process(target=self.run, args=(self.worker_no, self.name, self.channels, self.queue_add, self.queue_remove))
        self.process.daemon = True
        self.process.start()

    def run(self, worker_no: int, name: str, channels: dict, queue_add: Queue, queue_remove: Queue):
        print('{} started'.format(name))
        logger = logging.getLogger('root')
        selector = DefaultSelector()
        clients = dict()

        try:
            while True:
                # register
                while not queue_add.empty():
                    channel: Channel = queue_add.get()
                    client = Client(channel)

                    client.worker = self
                    clients[client.channel.name] = client
                    selector.register(client.sck, EVENT_READ, client.receive)
                    client.connect()
                    logger.debug('{} += {} → {} viewers'.format(name, channel.name, self.viewer_count.value))
                # unregister
                while not queue_remove.empty():
                    channel_name: str = queue_remove.get()
                    if channel_name in clients:
                        client: Client = clients[channel_name]

                        client.stop()
                        selector.unregister(client.sck)
                        del clients[client.channel.name]                    
                        logger.debug('{} -= {} → {} viewers'.format(name, channel.name, self.viewer_count.value))
                # get read events
                events = selector.select(timeout=1)
                for key, mask in events:
                    receive = key.data  # callback function
                    receive()
        except KeyboardInterrupt:
            pass
        except Exception as e:
            logger.error(str(e))

    def update_viewer_count(self, channel: Channel):
        try:
            new_viewer_count = channel.viewer_count
            old_viewer_count = self.channels[channel.name][0]
            self.viewer_count.value += (new_viewer_count - old_viewer_count)
            self.channels[channel.name][0] = new_viewer_count
        except Exception as e:
            self.logger.error(str(e))
    
    # will execute on other process
    def add(self, channel: Channel):
        try:
            self.channels[channel.name] = [channel.viewer_count, self.worker_no, False]
            self.viewer_count.value += channel.viewer_count
            self.queue_add.put(channel)
        except Exception as e:
            self.logger.error(str(e))
    
    def remove(self, channel_name: str):
        try:
            viewer_count = self.channels[channel_name][0]
            del self.channels[channel_name]
            self.viewer_count.value += viewer_count
            self.queue_remove.put(channel_name)
        except Exception as e:
            self.logger.error(str(e))
