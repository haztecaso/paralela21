#!/usr/bin/env python3

from multiprocessing.connection import Client
from multiprocessing import Process, Manager, Lock
from datetime import datetime
from common import *
from client_ui import *
import sys, traceback

class ChatClient():
    def __init__(self, username, ip="127.0.0.1", port=6000,\
            authkey=b"secret password"):
        self.username = username
        self.addr     = (ip, int(port))
        self.authkey  = authkey

        self.conn     = None
        self.manager  = Manager()
        self.history  = self.manager.list()

        self.sender   = None
        self.receiver = None
        self.lock     = Lock()
        self.ui      = ChatClientUI(self.username, self.history)
        self.debug_history = self.manager.list()

    def debug(self, message):
        self.debug_history.append(message)
        self.ui.redraw_debug(self.debug_history)

    def start(self):
        """
        Create connection and processes for sending and receiving messages
        """
        # self.debug(f"STARTING CLIENT FOR USERNAME {self.username}")
        try:
            self.conn = Client(address=self.addr, authkey=self.authkey)
        except Exception as e:
            print(e)
        else:
            self.ui.start()
            self.ui.redraw()
            self.receiver = Process(target=self.receive_loop,\
                                    name=f"{self.username} receiver")
            self.sender   = Process(target=self.send_loop,\
                                    name=f"{self.username} sender")
            if self.connect():
                self.sender.start()
                self.receiver.start()
                self.sender.join()
                self.receiver.join()

    def connect(self):
        self.debug("Starting CONNECT")
        try:
            payload = encode_connect(self.username)
            self.send_payload(payload)
        except ValueError as e:
            self.debug(e)
            return False
        else:
            return True

    def close(self):
        if self.conn:
            self.send_payload(CLOSE)
            self.conn.close()
        self.conn = None

    def stop(self):
        self.close()
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

    def send_loop(self):
        self.debug("Starting send loop")
        while self.conn:
            self.debug("Starting send iter")
            message = self.ui.input()
            if message == "/quit":
                self.stop()
            elif len(message) > 0:
                try:
                    self.send_message(message)
                except ValueError as e:
                    self.debug(e)

    def receive_loop(self):
        self.debug("Starting receive loop")
        while self.conn:
            try:
                payload = self.conn.recv()
                if payload["code"] == 3:
                    self.add_message(payload)
            except Exception as e:
                self.debug(f"Error receiving message: {e}")

    def add_message(self, payload):
        assert payload["code"] == 3, "Code must be 3 (MESSAGE)"
        self.lock.acquire()
        self.history.append(payload) #TODO: optimize
        self.lock.release()
        self.ui.redraw()

    def send_message(self, message):
        timestamp = datetime.now()
        payload = encode_message(timestamp, message, self.username)
        self.add_message(payload)
        self.send_payload(payload)

    def send_payload(self, payload):
        try:
            self.conn.send(payload)
            # response = self.conn.recv()
        except Exception as e:
            self.debug(f"Error sending message: {e}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="chat client")
    parser.add_argument("-u", metavar="username",
                        help="user name", type=str)
    parser.add_argument("-i", metavar="ip", default="127.0.0.1",
                        help="server ip", type=str)
    parser.add_argument("-p", metavar="port", default=6000,
                        help="server port", type=int)
    args = parser.parse_args()
    if not args.u:
        args.u= input("username: ")
    client = ChatClient(args.u, args.i, args.p)
    try:
        client.start()
    except KeyboardInterrupt:
        client.stop()
