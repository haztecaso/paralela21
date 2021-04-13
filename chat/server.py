#!/usr/bin/env python3
from multiprocessing.connection import Listener
from multiprocessing import Process, Manager, AuthenticationError
from common import *
from time import sleep
from datetime import datetime

class ChatServer():
    def __init__(self, ip="127.0.0.1", port=6000, authkey=b"secret password"):
        self.addr = (ip, int(port))
        self.authkey = authkey
        self.manager = Manager()
        self.clients = self.manager.dict()
        self.listener = None

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
        try:
            payload = conn.recv()
            assert payload["code"] == 1, "First message must be CONNECT"
            username = self.connect(payload, client_ip, conn)
            if username:
                # conn.send(ACK)
                p = Process(target=self._client_loop, args=(username,),\
                        name=f"{username} listener")
                p.daemon = True
                p.start()
        except Exception as e:
            print(f"Error in registration: {type(e).__name__} [{e}]")

    def _client_loop(self, username):
        conn = self.clients[username]["conn"]
        while username in self.clients:
            try:
                payload = conn.recv()
                # conn.send(ACK)
            except Exception as e:
                if type(e) is EOFError:
                    print(f"Connection down :(")
                else:
                    print(f"Error: {e}")
                self.client_close(username)
            else:
                self._parse_payload(username, payload)

    def _parse_payload(self, username, payload):
        try:
            if payload["code"] == 0:
                self.client_close(username)
            elif payload["code"] == 3:
                self.broadcast_message(username, payload)
        except Exception as e:
            print(f"Error parsing payload: {e}")
            print(f"payload = {payload}")

    def connect(self, payload, client_ip, conn):
        username = decode_connect(payload)
        if username not in self.clients:
            print(f"{username} CONNECTED")
            self.clients[username] = { "conn" : conn, "ip" : client_ip }
            payload = encode_message(datetime.now(),f"{username} joined the room.","SERVER")
            self.broadcast_message("SERVER", payload)
            conn.send(ACK)
            return username
        else:
            message = f"{username} is already connected!"
            print(message)
            conn.send(encode_error(message, True))
            conn.close()
            return False

    def client_close(self, username):
        if username in self.clients:
            conn = self.clients[username]["conn"]
            conn.close()
            print(f"{username} DISCONNECTED")
            del self.clients[username]
        else:
            print(f"{username} is not in current")

    def close_all(self):
        print("Closing all connections")
        for username in self.usernames():
            self.client_close(username)

    def stop(self):
        self.close_all()

    def broadcast_message(self, username, payload):
        timestamp, message, _ = decode_message(payload)
        print(f"[{username}] {message}")
        for username2, data in self.clients.items():
            if not username2 == username:
                data["conn"].send(payload)


if __name__ == "__main__":
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
