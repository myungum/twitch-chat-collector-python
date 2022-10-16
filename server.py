from twitchapi import TwitchAPI
import time
from multiprocessing import Manager
from worker import Worker
import multiprocessing
import logging


UPDATE_PERIOD = 60  # 1 minutes
MAX_CHANNEL = 300


class Server:
    def __init__(self, conn_info: dict,
                 max_channel=MAX_CHANNEL) -> None:
        self.conn_info = Manager().dict(conn_info)
        self.api = TwitchAPI(self.conn_info)

        self.workers = []
        self.max_channel = max_channel
        self.logger = logging.getLogger('root')

    def contains(self, channel):
        for worker in self.workers:
            if worker.contains(channel):
                return True
        return False

    def add(self, channel):
        sorted_workers = [(worker.size(), worker) for worker in self.workers]
        sorted_workers.sort(key=lambda w: w[0])
        lazy_worker = sorted_workers[0][1]
        lazy_worker.add(channel)

    def start(self):
        self.logger.info('server start')
        
        for i in range(multiprocessing.cpu_count()):
            worker = Worker(i, self.conn_info)
            worker.start()
            self.workers.append(worker)

        self.logger.info('{} workers are created'.format(len(self.workers)))
        self.logger.start_push()

        while True:
            # add
            channels = self.api.get_channels(max_channel=self.max_channel)
            for channel in channels:
                if not self.contains(channel):
                    self.add(channel)
                time.sleep(0.1)
            time.sleep(UPDATE_PERIOD)
