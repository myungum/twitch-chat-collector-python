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


class LogHandler(logging.Handler):
    CHAT_LOG_LEVEL_NAME = 'CHAT'
    CHAT_LOG_LEVEL_NO = 60
    PUSH_PERIOD = 1

    def __init__(self, level=logging.DEBUG, conn_info: dict = None, period=PUSH_PERIOD) -> None:
        logging.Handler.__init__(self, level)

        self.queue_log = Queue()
        self.queue_chat = Queue()
        self.period: int = period

        db_host = conn_info['db_host']
        db_port = conn_info['db_port']
        db_name = conn_info['db_name']
        client = MongoClient(host=db_host, port=db_port)

        self.thread_log = Thread(target=self.__push, args=(
            False, client[db_name]['log'], self.queue_log))
        self.thread_log.daemon = True
        self.thread_log.start()

        self.thread_chat = Thread(target=self.__push, args=(
            True, client[db_name]['chat'], self.queue_chat))
        self.thread_chat.daemon = True
        self.thread_chat.start()

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

                elapsed_time = datetime.now() - start_time
                if self.period > elapsed_time.seconds:
                    time.sleep(self.period - elapsed_time.seconds)
            except (KeyboardInterrupt, SystemExit, EOFError):
                return
            except:
                traceback.print_exc(file=sys.stderr)

    def emit(self, record):
        now = datetime.now()

        # chat log
        if record.levelno == LogHandler.CHAT_LOG_LEVEL_NO:
            doc = {
                'message': record.msg,
                'datetime': now
            }
            self.queue_chat.put_nowait(doc)
        # normal log
        else:
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
