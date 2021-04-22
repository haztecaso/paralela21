#!/usr/bin/env python3
from multiprocessing.connection import Client
from multiprocessing import Process, Manager, Lock
from datetime import datetime
import logging

from messages import *
from client_ui import *

class ChatClient():
    def __init__(self, username, ip="127.0.0.1", port=6000,\
            authkey=b"secret password"):
        self.username = username
        self.addr     = (ip, int(port))
        self.authkey  = authkey

        self.conn     = None
        self.manager  = Manager()
        self.history  = MessageHistory(manager = self.manager)

        self.sender   = None
        self.receiver = None
        self.lock     = Lock()
        self.ui      = ChatClientUI(self.username, self.history)

    def log(self, msg, **args):
        level = args.get('level', 'debug')
        if level == 'debug':
            logging.debug(msg)
        elif level == 'info':
            logging.info(msg)

    def start(self):
        """
        Create connection and processes for sending and receiving messages
        """
        self.log(f"STARTING CLIENT (username: {self.username})", level = 'info')
        try:
            self.conn = Client(address=self.addr, authkey=self.authkey)
        except Exception as e:
            print(f"[ERROR] {e}")
        else:
            self.receiver = Process(target=self._receive_loop,
                                    name=f"{self.username} receiver")
            self.sender = Process(target=self._send_loop,
                                    name=f"{self.username} sender")
            if self.connect():
                self.ui.start()
                self.sender.start()
                self.receiver.start()
                self.sender.join()
                self.receiver.join()
            else:
                self.stop()

    def connect(self):
        # self.log("STARTING CONNECT")
        try:
            message = Message(type = CONNECT, username = self.username)
            self.send_payload(message.encode())
            response = self.conn.recv()
            history = response.get('history')
            for message in decode_history(history):
                self.append_history(message)
        except ValueError as e:
            # self.log(e)
            return False
        else:
            if response['type_code'] == ERROR['code']:
                response = Message(payload = response)
                message = response.get('message')
                critical = response.get('critical')
                print(f"[ERROR] {message}")
                if critical:
                    return False
            return True

    def stop(self):
        try:
            if type(self.sender) is Process:
                self.sender.terminate()
            if type(self.receiver) is Process:
                self.receiver.terminate()
        except:
            pass
        finally:
            self.ui.stop()
            import sys
            sys.exit()
        if self.conn:
            self.send_payload(CLOSE)
            self.conn.close()
            self.conn = None

    def _send_loop(self):
        self.log("Starting send loop")
        self.sender
        while self.conn:
            message = self.ui.input()
            if len(message) > 0:
                try:
                    self.send_message(message)
                except ValueError as e:
                    self.log(e)

    def _receive_loop(self):
        self.log("Starting receive loop")
        while self.conn:
            if self.conn.poll():
                try:
                    message = Message(payload = self.conn.recv())
                    self.update_history(message)
                except Exception as e:
                    self.log(f"Error receiving message: {e}")

    def append_history(self, message):
        self.lock.acquire()
        self.history.add(message)
        self.lock.release()

    def update_history(self, message):
        self.append_history(message)
        self.ui.redraw()

    def send_message(self, message):
        self.log(f"{message}", level='info')
        message = Message(type=MESSAGE, username = self.username, message = message)
        self.update_history(message)
        self.send_payload(message.encode())

    def send_payload(self, payload):
        try:
            self.conn.send(payload)
            # response = self.conn.recv()
        except Exception as e:
            self.log(f"Error sending message: {e}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="chat client")
    parser.add_argument("-u", metavar="username",
                        help="user name", type=str)
    parser.add_argument("-i", metavar="ip", default="127.0.0.1",
                        help="server ip", type=str)
    parser.add_argument("-p", metavar="port", default=6000,
                        help="server port", type=int)
    parser.add_argument('-l', dest='logging', action='store_true')
    args = parser.parse_args()
    if not args.u:
        args.u = input("username: ")
    if args.logging:
        FORMAT = '%(asctime)s:%(levelname)s:%(process)d:%(message)s'
        logging.basicConfig(filename='client.log', format=FORMAT, level=logging.DEBUG)
    try:
        client = ChatClient(args.u, args.i, args.p)
        client.start()
    except KeyboardInterrupt:
        client.stop()
