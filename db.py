from pymongo import MongoClient
from datetime import datetime
from threading import Thread
from multiprocessing import Queue
import time

PUSH_PERIOD = 1


class DB:
    def __init__(self, conn_info: dict, period: int = PUSH_PERIOD) -> None:
        self.period = period
        self.queue_chat = Queue()

        db_host = conn_info['db_host']
        db_port = conn_info['db_port']
        db_name = conn_info['db_name']
        self.client = MongoClient(host=db_host, port=db_port)
        self.collection = self.client[db_name]['chat']

        self.thread = Thread(target=self.__push)
        self.thread.daemon = True
        self.thread.start()

    def __push(self):
        try:
            while True:
                start_time = datetime.now()

                if not self.queue_chat.empty():
                    docs = []
                    while not self.queue_chat.empty():
                        doc = self.queue_chat.get()
                        docs.append(doc)
                    print('{} | '.format(len(docs)), end='', flush=True)
                    self.collection.insert_many(docs)

                elapsed_time = datetime.now() - start_time
                if self.period > elapsed_time.seconds:
                    time.sleep(self.period - elapsed_time.seconds)
        except KeyboardInterrupt:
            return
