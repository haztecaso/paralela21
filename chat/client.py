#!/usr/bin/env python3

from multiprocessing.connection import Client
from multiprocessing import Process, Manager, Lock
from datetime import datetime
from message import *
import curses, curses.textpad
import os
import sys, traceback

class ChatClient():
    def __init__(self, username, ip="127.0.0.1", port=6000, authkey=b'secret password'):
        self.username = username
        self.addr = (ip, int(port))
        self.authkey = authkey
        self.conn = None
        self.manager = Manager()
        self.history = self.manager.list()
        self.sender = None
        self.receiver = None
        self.lock = Lock()
        self.tui = ChatClientTUI(self.username)
        self.debug_history = self.manager.list()

    def debug(self, message):
        self.debug_history.append(message)
        self.tui.redraw_debug(self.debug_history)

    def start(self):
        """
        Create connection and processes for sending and receiving messages
        """
        # debug(f"STARTING CLIENT FOR USERNAME {self.username}")
        try:
            self.conn = Client(address=self.addr, authkey=self.authkey)
        except ConnectionRefusedError as e:
            print("Connection refused :(")
        else:
            self.tui.start()
            self.tui.redraw(self.history)
            self.receiver = Process(target=self.receive_loop, name=f"{username} receiver")
            self.sender = Process(target=self.send_loop, name=f"{username} sender")
            if self.connect():
                self.sender.start()
                self.receiver.start()
                self.sender.join()
                self.receiver.join()
        # self.send_loop()

    def connect(self):
        """
        Send CONNECT message to server and check if
        """
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
            self.tui.stop()

    def send_loop(self):
        self.debug("Starting send loop")
        while self.conn:
            self.debug("Starting send iter")
            message = self.tui.input()
            if message == '/quit':
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
                if payload['code'] == 3:
                    self.add_message(payload)
            except Exception as e:
                self.debug(f"Error receiving message: {e}")

    def add_message(self, payload):
        assert payload['code'] == 3, 'Code must be 3 (MESSAGE)'
        self.lock.acquire()
        self.history.append(payload) #TODO: optimize
        self.lock.release()
        self.tui.redraw(self.history)

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


class ChatClientTUI():
    def __init__(self, username, debug = False):
        self.history_window = None
        self.prompt_window = None
        self.debug = debug
        if self.debug:
            self.debug_window = None
        self.screen = None

    def start(self):
        self._start_curses()
        self.init_history_window()
        self.init_prompt_window()
        if self.debug:
            self.init_debug_window()

    def stop(self):
        self._stop_curses()

    def _start_curses(self):
        assert self.screen == None, "Curses is already running"
        self.screen = curses.initscr()
        curses.cbreak()
        self.screen.keypad(1)

    def _stop_curses(self):
        if self.screen is not None:
            curses.nocbreak()
            self.screen.keypad(0)
            self.screen = None
            curses.endwin()

    def redraw(self, history):
        self.screen.refresh()
        self.redraw_history(history)
        self.redraw_prompt()

    def init_history_window(self):
        rows, cols = ChatClientTUI.terminal_size()
        if self.debug:
            cols = cols//2
        self.history_window = curses.newwin(rows-1, cols, 0, 0)

    def redraw_history(self, history):
        self.history_window.clear()
        self.history_window.border(0)
        rows = ChatClientTUI.terminal_size()[0]
        row = rows - 3
        i = len(history) - 1
        while row >= 1 and i > 0:
            payload = history[i]
            timestamp, message, username = decode_message(payload)
            timestamp = timestamp.strftime("%T")
            self.history_window.move(row,1)
            self.history_window.addstr(f"{timestamp} [{username}] {message}")
            row -= 1
            i -= 1
        self.history_window.refresh()

    def init_prompt_window(self):
        rows, cols = ChatClientTUI.terminal_size()
        self.prompt_window = curses.newwin(1, cols, rows-1, 0)
        self.prompt_window.keypad(1)
        self.prompt_window.addstr(f'{username}> ')

    def redraw_prompt(self):
        self.prompt_window.refresh()

    def reset_prompt(self):
        self.prompt_window.clear()
        self.prompt_window.addstr(f'{username}> ')
        self.redraw_prompt()

    def input(self):
        message = str(self.prompt_window.getstr(),'utf-8')
        self.reset_prompt()
        return message

    def init_debug_window(self):
        if self.debug:
            rows, cols = ChatClientTUI.terminal_size()
            self.debug_window = curses.newwin(rows-1, cols//2+1, 0, 0)

    def redraw_debug(self, debug_history):
        if self.debug:
            self.debug_window.clear()
            rows = ChatClientTUI.terminal_size()[0]
            row = rows - 3
            for message in debug_history:
                if row < 1:
                    break
                self.debug_window.move(row,1)
                self.debug_window.addstr(f"{message}")

    @staticmethod
    def terminal_size():
        rows, cols = os.popen('stty size', 'r').read().split()
        return (int(rows), int(cols))

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        username = sys.argv[1]
    else:
        username = input('username: ')
    server = ChatClient(username)
    try:
        server.start()
    except KeyboardInterrupt:
        server.stop()
