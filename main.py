from server import Server
import json
import logging
from loghandler import LogHandler


with open('settings.json', 'r') as file:
    conn_info = dict(json.load(file))

logger = logging.getLogger('root')
logger.setLevel(logging.DEBUG)
logHandler = LogHandler(logging.DEBUG, conn_info)
logger.addHandler(logHandler)
        
s = Server(conn_info)
s.start()
