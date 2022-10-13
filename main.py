from server import Server
import json
import logging
from loghandler import LogHandler


with open('settings.json', 'r') as file:
    conn_info = dict(json.load(file))

# custom logging level
logging.addLevelName(LogHandler.CHAT_LOG_LEVEL_NO, LogHandler.CHAT_LOG_LEVEL_NAME)

logger = logging.getLogger('root')
logger.setLevel(logging.DEBUG)
assert logger.isEnabledFor(LogHandler.CHAT_LOG_LEVEL_NO)
logHandler = LogHandler(logging.DEBUG, conn_info)
logger.addHandler(logHandler)
        
s = Server(conn_info)
s.start()
