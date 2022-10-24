from multiprocessing import Process, Queue, Manager
from client import Client
from selectors import DefaultSelector, EVENT_READ
import logging
from logging import Logger
from twitchapi import Channel


class Worker:
    def __init__(self, worker_no: int, conn_info: dict, channels: dict, queue_remove: Queue) -> None:
        self.worker_no = worker_no
        self.name = 'worker {}'.format(worker_no)
        self.conn_info = conn_info
        self.channels = channels
        self.logger: Logger = logging.getLogger('root')
        self.queue_add = Manager().Queue()
        self.queue_remove = queue_remove
        self.viewer_count = 0

    def start(self):
        self.process = Process(target=self.run)
        self.process.daemon = True
        self.process.start()

    def run(self):
        print('{} started'.format(self.name))
        logger = logging.getLogger('root')
        selector = DefaultSelector()
        clients = dict()

        try:
            while True:
                # register
                while not self.queue_add.empty():
                    client: Client = self.queue_add.get()
                    client.worker = self
                    clients[client.channel.name] = client
                    selector.register(client.sck, EVENT_READ, client.receive)
                    client.connect()
                # unregister
                for channel_name in list(clients.keys()):
                    client: Client = clients[channel_name]
                    client.check_timeout()
                    if client.stopped:
                        client.stop()
                        del clients[client.channel.name]
                        selector.unregister(client.sck)
                        client.close()    
                        self.queue_remove.put(client.channel.name)          
                # get read events
                events = selector.select(timeout=1)
                for key, mask in events:
                    receive = key.data  # callback function
                    receive()
        except KeyboardInterrupt:
            pass

    def update_viewer_count(self, channel: Channel):
        try:
            new_viewer_count = channel.viewer_count
            old_viewer_count = self.channels[channel.name][0]
            if new_viewer_count != old_viewer_count:
                self.viewer_count += (new_viewer_count - old_viewer_count)
                self.channels[channel.name] = [new_viewer_count, self.worker_no]
                self.logger.debug('{} {}({}→{}) → {} viewers'.format(self.name, channel.name, old_viewer_count, new_viewer_count, self.viewer_count))
        except Exception as e:
            self.logger.error(str(e))
    
    # will execute on other process
    def add(self, channel: Channel):
        try:
            self.channels[channel.name] = [channel.viewer_count, self.worker_no]
            self.viewer_count += channel.viewer_count
            self.logger.debug('{} += {}({}) → {} viewers'.format(self.name, channel.name, channel.viewer_count, self.viewer_count))
            self.queue_add.put(Client(channel))
        except Exception as e:
            self.logger.error(str(e))
    
    def remove(self, channel_name: str):
        try:
            viewer_count = self.channels[channel_name][0]
            del self.channels[channel_name]
            self.viewer_count -= viewer_count
            self.logger.debug('{} -= {}({}) → {} viewers'.format(self.name, channel_name, viewer_count, self.viewer_count))
        except Exception as e:
            self.logger.error(str(e))
