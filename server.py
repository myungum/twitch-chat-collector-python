from twitchapi import TwitchAPI, Channel
import time
from multiprocessing import Manager, Queue
from worker import Worker
import multiprocessing
import logging


UPDATE_PERIOD = 60  # 1 minutes
MAX_CHANNEL = 300


class Server:
    def __init__(self, conn_info: dict,
                 max_channel=MAX_CHANNEL) -> None:
        self.conn_info = Manager().dict(conn_info)
        self.channels = Manager().dict()
        self.queue_remove = Queue()
        self.api = TwitchAPI(self.conn_info)

        self.workers = []
        self.max_channel = max_channel
        self.logger = logging.getLogger('root')

    def get_lazy_worker(self):
        return min(self.workers, key=lambda worker: worker.viewer_count.value)

    def update_channel(self, channel: Channel):
        if channel.name in self.channels:
            worker_no = self.channels[channel.name][1]
            worker: Worker = self.workers[worker_no]
            worker.update_viewer_count(channel)

    def try_add(self, channel: Channel):
        if not channel.name in self.channels:
            worker: Worker = self.get_lazy_worker()
            worker.add(channel)

    def remove(self, channel_name: str):
        if channel_name in self.channels:
            worker_no = self.channels[channel_name][1]
            worker: Worker = self.workers[worker_no]
            worker.remove(channel_name)

    def start(self):
        self.logger.info('server start')

        for i in range(multiprocessing.cpu_count()):
            worker = Worker(i, self.conn_info, self.channels, self.queue_remove)
            worker.start()
            self.workers.append(worker)

        self.logger.info('{} workers are created'.format(len(self.workers)))
        self.logger.start_push()

        while True:
            # add
            live_channels = self.api.get_channels(max_channel=self.max_channel)
            for channel in live_channels:
                self.update_channel(channel)
            for channel in live_channels:
                self.try_add(channel)
                time.sleep(0.1)
            # remove
            while not self.queue_remove.empty():
                channel_name = self.queue_remove.get()
                self.remove(channel_name)
