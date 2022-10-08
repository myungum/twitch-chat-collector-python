# source
# https://blog.naver.com/PostView.nhn?blogId=wideeyed&logNo=222033147585
# https://stackoverflow.com/questions/641420/how-should-i-log-while-using-multiprocessing-in-python

import logging
from pymongo import MongoClient
from datetime import datetime
from multiprocessing import Queue
from threading import Thread
import traceback
import time
import sys


class LogHandler(logging.Handler):
    def __init__(self, level=logging.DEBUG, conn_info: dict = None) -> None:
        logging.Handler.__init__(self, level)

        self.queue = Queue()

        db_host = conn_info['db_host']
        db_port = conn_info['db_port']
        db_name = conn_info['db_name']
        self.client = MongoClient(host=db_host, port=db_port)
        self.collection = self.client[db_name]['log']

        self.thread = Thread(target=self.__push, args=(self.queue, ))
        self.thread.daemon = True
        self.thread.start()

    def __push(self, queue: Queue):
        while True:
            try:
                time.sleep(1)
                docs = [queue.get()]
                while not queue.empty():
                    docs.append(queue.get())
                self.collection.insert_many(docs)
            except (KeyboardInterrupt, SystemExit):
                raise
            except EOFError:
                break
            except:
                traceback.print_exc(file=sys.stderr)

    def emit(self, record):
        now = datetime.now()
        print('[{}] {} {} > {} : {}'.format(now, record.levelname, record.filename, record.funcName, record.msg))

        doc = {
            'file': record.filename,  # // 파일명
            'process': record.processName,  # // 프로세스명
            'thread': record.threadName,  # // 쓰레드명
            'function': record.funcName,  # // 함수명
            'level': record.levelno,  # // 로그레벨(ex. 10)
            'levelName': record.levelname,  # // 로그레벨명(ex. DEBUG)
            'message': record.msg,  # // 오류 메시지
            'datetime': datetime.now(),  # // 현재일시
        }
        self.queue.put_nowait(doc)
