from server import Server
import json


with open('settings.json', 'r') as file:
    conn_info = dict(json.load(file))

s = Server(conn_info)
s.start()
