from server import Server
import json
import logging
from chatloghandler import ChatLogHandler
from chatlogger import ChatLogger

with open('settings.json', 'r') as file:
    conn_info = dict(json.load(file))

logging.setLoggerClass(ChatLogger)
logger = logging.getLogger('root')
logger.setLevel(logging.DEBUG)
logger.addHandler(ChatLogHandler(logging.DEBUG, conn_info))
        
s = Server(conn_info)
s.start()
