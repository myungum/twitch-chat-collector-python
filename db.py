from pymongo import MongoClient
from datetime import datetime
from threading import Thread
from multiprocessing import Queue
import time


class DB:
    def __init__(self, conn_info: dict) -> None:
        self.queue_chat = Queue()
        self.thread = Thread(
            target=self.__push, args=(conn_info, 'chat', self.queue_chat, 1))
        self.thread.daemon = True
        self.thread.start()

    def __push(self, conn_info: dict, collection_name: str, queue_chat: Queue, period: int):
        db_host = conn_info['db_host']
        db_port = conn_info['db_port']
        db_name = conn_info['db_name']

        client = MongoClient(host=db_host, port=db_port)
        collection = client[db_name][collection_name]

        while True:
            start_time = datetime.now()

            if not queue_chat.empty():
                docs = []
                while not queue_chat.empty():
                    doc = queue_chat.get()
                    docs.append(doc)
                print('{} | '.format(len(docs)), end='', flush=True)
                collection.insert_many(docs)

            elapsed_time = datetime.now() - start_time
            if period > elapsed_time.seconds:
                time.sleep(period - elapsed_time.seconds)
