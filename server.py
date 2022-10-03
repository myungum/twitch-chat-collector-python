from db import DB
import time
from multiprocessing import Manager
from worker import Worker


class Server:
    def __init__(self, chat_host: str, chat_port: int,
                 chat_token: str, chat_user_name: str,
                 db_host: str, db_port: int, db_name: str) -> None:
        self.manager = Manager()
        self.conn_info = self.manager.dict({
            'chat_host': chat_host,
            'chat_port': chat_port,
            'chat_token': chat_token,
            'chat_user_name': chat_user_name,
            'db_host': db_host,
            'db_port': db_port,
            'db_name': db_name
        })
        self.clients = self.manager.dict()

        self.db = DB(db_host, db_port, db_name, dict())
        self.workers = []

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
        for i in range(10):  # (multiprocessing.cpu_count()):
            worker = Worker(i, self.conn_info, self.db)
            worker.start()
            self.workers.append(worker)

        print(len(self.workers), 'workers ready')

        while True:
            # add
            channels = self.db.get_live_channels()[:100]
            for channel in channels:
                if not self.contains(channel):
                    self.add(channel)
                time.sleep(0.1)

            time.sleep(1)
            print('.', end='')

    def stop(self):
        for channel, client in self.clients.items():
            client.stop()
