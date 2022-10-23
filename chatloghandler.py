# source
# https://blog.naver.com/PostView.nhn?blogId=wideeyed&logNo=222033147585
# https://stackoverflow.com/questions/641420/how-should-i-log-while-using-multiprocessing-in-python

import logging
from pymongo import MongoClient
from pymongo.collection import Collection
from datetime import datetime
from multiprocessing import Queue
from threading import Thread
import traceback
import time
import sys


class ChatLogHandler(logging.Handler):
    PUSH_PERIOD = 1

    def __init__(self, level=logging.DEBUG, conn_info: dict = None, period=PUSH_PERIOD) -> None:
        logging.Handler.__init__(self, level)

        self.conn_info = conn_info
        self.queue_log = Queue()
        self.queue_chat = Queue()
        self.period: int = period
        self.is_running = False
        self.threads = []

    def start_push_thread(self, console: bool, collection: Collection, queue: Queue):
        thread = Thread(target=self.__push, args=(console, collection, queue))
        thread.daemon = True
        thread.start()
        self.threads.append(thread)

    def start_push(self):
        if not self.is_running:
            self.is_running = True
            db_host = self.conn_info['db_host']
            db_port = self.conn_info['db_port']
            db_name = self.conn_info['db_name']
            client = MongoClient(host=db_host, port=db_port)

            self.start_push_thread(False, client[db_name]['log'], self.queue_log)
            self.start_push_thread(True, client[db_name]['chat'], self.queue_chat)

    def __push(self, console: bool, collection: Collection, queue: Queue):
        while True:
            try:
                start_time = datetime.now()

                docs = []
                while not queue.empty():
                    docs.append(queue.get())
                if console:
                    print('{} | '.format(len(docs)), end='', flush=True)
                if len(docs) > 0:
                    collection.insert_many(docs)

                elapsed_time = (datetime.now() - start_time).total_seconds()
                time.sleep(max(self.period - elapsed_time, 0))
            except (KeyboardInterrupt, SystemExit, EOFError):
                return
            except:
                traceback.print_exc(file=sys.stderr)

    def chat(self, channel: str, msg: str, datetime: datetime):
        doc = {
            'channel': channel,
            'message': msg,
            'datetime': datetime
        }
        self.queue_chat.put_nowait(doc)

    def emit(self, record):
        now = datetime.now()
        print('[{}] {} {} > {} : {}'.format(now, record.levelname,
                                            record.filename, record.funcName, record.msg))

        doc = {
            'file': record.filename,  # // 파일명
            'process': record.processName,  # // 프로세스명
            'thread': record.threadName,  # // 쓰레드명
            'function': record.funcName,  # // 함수명
            'level': record.levelno,  # // 로그레벨(ex. 10)
            'levelName': record.levelname,  # // 로그레벨명(ex. DEBUG)
            'message': record.msg,  # // 오류 메시지
            'datetime': now,  # // 현재일시
        }
        self.queue_log.put_nowait(doc)
