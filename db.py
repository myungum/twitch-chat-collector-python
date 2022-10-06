from pymongo import MongoClient
from datetime import datetime
from threading import Thread
from multiprocessing import Queue
import time


class DB:
    def __init__(self, db_host: str, db_port: int, db_name: str, status: dict) -> None:
        status['db_host'] = db_host
        status['db_port'] = db_port
        status['db_name'] = db_name
        self.status = status

        # log
        self.queue_chat = Queue()
        self.client = MongoClient(host=db_host, port=db_port)
        
        self.thread = Thread(
            target=self.__push, args=(status, 'chat', self.queue_chat, 1))
        self.thread.daemon = True
        self.thread.start()

    def __push(self, status: dict, collection_name: str, queue_chat: Queue, period: int):
        db_host = status['db_host']
        db_port = status['db_port']
        db_name = status['db_name']

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
