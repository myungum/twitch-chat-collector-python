from twitchapi import TwitchAPI
from db import DB
import time
from multiprocessing import Manager
from worker import Worker
import multiprocessing
import logging
from loghandler import LogHandler

UPDATE_PERIOD = 60  # 1 minutes
MAX_CHANNEL = 300


class Server:
    def __init__(self, conn_info: dict,
                 max_channel=MAX_CHANNEL) -> None:
        self.manager = Manager()
        self.conn_info = self.manager.dict(conn_info)
        self.clients = self.manager.dict()

        self.api = TwitchAPI(self.conn_info)
        self.db = DB(conn_info)
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
            worker = Worker(i, self.conn_info, self.db.queue_chat)
            worker.start()
            self.workers.append(worker)

        self.logger.info('{} workers ready'.format(len(self.workers)))

        while True:
            # add
            channels = self.api.get_channels(max_channel=self.max_channel)
            for channel in channels:
                if not self.contains(channel):
                    self.add(channel)
                time.sleep(0.1)
            time.sleep(UPDATE_PERIOD)

    def stop(self):
        for channel, client in self.clients.items():
            client.stop()
