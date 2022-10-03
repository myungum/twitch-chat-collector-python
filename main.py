from server import Server

with open('setting.txt', 'r') as f:
    db_host, db_port, db_name = f.readline().split()
    chat_host, chat_port = f.readline().split()
    token, user_name = f.readline().split()
    client_id, client_secret = f.readline().split()

s = Server(chat_host, int(chat_port), token,
           user_name, db_host, int(db_port), db_name)
s.start()
