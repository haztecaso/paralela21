#!/usr/bin/env python3
from multiprocessing.connection import Listener
from multiprocessing import Process, Manager, AuthenticationError
import sqlite3, json
from time import sleep
from datetime import datetime

from messages import *

class ChatServer():
    def __init__(self, ip="127.0.0.1", port=6000, authkey=b"secret password"):
        self.addr = (ip, int(port))
        self.authkey = authkey
        self.manager = Manager()
        self.clients = self.manager.dict()
        self.listener = None
        self.db = ServerData()
        self.history = MessageHistory(manager = self.manager,
                messages = self.db.select_messages(n=100))

    def usernames(self):
        users = []
        for username in self.clients:
            users.append(username)
        return users

    def start(self):
        try:
            self.listener = Listener(address=self.addr, authkey=self.authkey)
        except OSError as e:
            print(e)
        else:
            ip, port = self.addr
            print(f"Server listening on {ip}:{port}")
            while True:
                self._listen()
            self.listener.close()

    def _listen(self):
        try:
            conn = self.listener.accept()
            client_ip = self.listener.last_accepted[0]
        except AuthenticationError as e:
            print("Authentication error")
            return
        username = None
        try:
            payload = conn.recv()
            assert payload["type_code"] == CONNECT['code'],\
                "First message must be of type CONNECT"
            username = self.connect(payload, client_ip, conn)
        except EOFError as eof:
            print("Error receiving connection message.")
        except AssertionError as e:
            print(e)
        finally:
            if username:
                p = Process(target=self._client_loop, args=(username,),\
                        name=f"{username} listener")
                p.daemon = True
                p.start()

    def _client_loop(self, username):
        conn = self.clients[username]["conn"]
        while username in self.clients:
            try:
                payload = conn.recv()
            except Exception as e:
                if type(e) is EOFError:
                    print(f"Connection down :(")
                else:
                    print(f"Error: {e}")
                self.client_close(username)
            else:
                self._parse_payload(username, payload)

    def _parse_payload(self, username, payload):
        message = Message(payload = payload)
        try:
            if message.type == CLOSE:
                self.client_close(username)
            elif message.type == MESSAGE:
                self.broadcast_message(message)
        except Exception as e:
            print(f"Error parsing payload: {e}")
            print(f"payload = {payload}")

    def connect(self, payload, client_ip, conn):
        message = Message(payload = payload)
        assert message.type == CONNECT, 'message must be of type CONNECT'
        username = message.get('username')
        if username not in self.clients:
            self.clients[username] = { "conn" : conn, "ip" : client_ip }
            message = Message(type=SERVER_INFO, key = "join", value=username) 
            self.broadcast_message(message, [username])
            response = Message(type=MESSAGE_HISTORY, history = self.history, max_size = 0)
            conn.send(response.encode())
            print(f"[SEND DATA] Sending message history to {username}")
            return username
        else:
            message = Message(type=ERROR,
                              message=f"{username} is already connected!",
                              critical = True)
            print(message)
            conn.send(message.encode())
            conn.close()
            return False

    def client_close(self, username):
        if username in self.clients:
            conn = self.clients[username]["conn"]
            conn.close()
            message = Message(type = SERVER_INFO, key="leave", value = username)
            self.broadcast_message(message)
            del self.clients[username]
        else:
            print(f"{username} is not in current")

    def close_all(self):
        print("Closing all connections")
        for username in self.usernames():
            self.client_close(username)

    def stop(self):
        self.close_all()

    def broadcast_message(self, message, excluded_users = []):
        excluded_users += [message.get('username')]
        if message.type == MESSAGE:
            self.history.add(message)
            self.db.insert_message(message)
        for username, data in self.clients.items():
            if not username in excluded_users:
                data["conn"].send(message.encode())
        print(f"[BROADCAST]\n{message}")

class ServerData():
    def __init__(self, db_file = "server.db"):
        self.conn = None
        self.db_file = db_file
        try:
            self.conn = sqlite3.connect(db_file) 
        except sqlite3.Error as e:
            print("sqlite3.Error:",e)
        self.create_tables()

    def exec_query(self, query, params=()):
        try:
            c = self.conn.cursor()
            c.execute(query, params)
            self.conn.commit()
        except sqlite3.Error as e:
            print("sqlite3.Error:",e)
        rows = c.fetchall()
        return rows

    def exec_queries(self, queries, params_list=[]):
        assert len(queries) == len(params)
        c = self.conn.cursor()
        for i in range(len(queries)):
            try:
                c.execute(query, params)
            except sqlite3.Error as e:
                print("sqlite3.Error:",e)
        self.conn.commit()
        rows = c.fetchall()
        return rows

    def insert_message(self, message):
        content = json.dumps(message.encode())
        timestamp = message.get('timestamp').timestamp()
        self.exec_query("INSERT INTO messages(timestamp, content) VALUES(?,?)",
                        (timestamp, content))

    def select_messages(self, **kwargs):
        n = kwargs.get('n', 0)
        from_timestamp = kwargs.get('from_timestamp', None)
        query = "SELECT content FROM messages "
        params = []
        if from_timestamp:
            assert type(from_timestamp) is datetime
            query += " WHERE timestamp > ?"
            params.append(from_timestamp.timestamp())
        query += " ORDER BY timestamp"
        if n > 0:
            query += " LIMIT ?"
            params.append(n)
        query += ";"
        rows = self.exec_query(query,params)
        return [Message(payload = json.loads(row[0])) for row in rows]

    def create_tables(self):
        self.create_messages()
        self.create_users()

    def create_messages(self):
        self.exec_query("""CREATE TABLE IF NOT EXISTS messages (
                id integer PRIMARY KEY,
                timestamp real NOT NULL,
                content text NOT NULL
                );""")

    def create_users(self):
        self.exec_query("""CREATE TABLE IF NOT EXISTS users (
                id integer PRIMARY KEY,
                username text NOT NULL,
                hash_salt text NOT NULL,
                hashed_pass text NOT NULL,
                last_host text NOT NULL
                );
                """)
        

def main():
    import argparse
    parser = argparse.ArgumentParser(description="chat server")
    parser.add_argument("-i", metavar="ip", default="127.0.0.1",
                        help="server ip", type=str)
    parser.add_argument("-p", metavar="port", default=6000,
                        help="server port", type=int)
    args = parser.parse_args()
    if args.i == "all":
        args.i = "0.0.0.0"
    elif args.i == "auto":
        import urllib.request
        args.i = urllib.request.urlopen('https://ident.me').read().decode('utf8')
    server = ChatServer(args.i, args.p)
    try:
        server.start()
    except KeyboardInterrupt:
        print(": KeyboardInterrupt")
        server.stop()

if __name__ == "__main__":
    main()
