import os
import curses, curses.textpad
from common import *

class ChatClientUI():
    def __init__(self, username, history, debug = False):
        self.username = username
        self.history = history
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
        self.redraw()

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

    def redraw(self):
        self.screen.refresh()
        self.redraw_history()
        self.redraw_prompt()

    def init_history_window(self):
        rows, cols = ChatClientUI.terminal_size()
        if self.debug:
            cols = cols//2
        self.history_window = curses.newwin(rows-1, cols, 0, 0)

    def redraw_history(self):
        self.history_window.clear()
        self.history_window.border(0)
        rows, cols = ChatClientUI.terminal_size()
        self.history_window.resize(rows-1, cols)
        row = rows - 3
        i = len(self.history) - 1
        while row >= 1 and i >= 0:
            message = self.history.messages[i]
            if message.type == MESSAGE:
                timestamp = message.get('timestamp').strftime("%T")
                username = message.get('username')
                message = message.get('message')
                self.history_window.move(row,1)
                self.history_window.addstr(f"{timestamp} [{username}] {message}")
            elif message.type == ERROR:
                message = message.get('message')
                # critical = message.get('critical')
                self.history_window.move(row,1)
                self.history_window.addstr(f"[ERROR] {message}")
            row -= 1
            i -= 1
        self.history_window.refresh()

    def init_prompt_window(self):
        rows, cols = ChatClientUI.terminal_size()
        self.prompt_window = curses.newwin(1, cols, rows-1, 0)
        self.prompt_window.keypad(1)
        self.prompt_window.addstr(f"{self.username}> ")

    def redraw_prompt(self):
        rows, cols = ChatClientUI.terminal_size()
        self.prompt_window.resize(1, cols)
        self.prompt_window.refresh()

    def reset_prompt(self):
        self.prompt_window.clear()
        self.prompt_window.addstr(f"{self.username}> ")
        self.redraw_prompt()

    def input(self):
        message = str(self.prompt_window.getstr(),"utf-8")
        self.reset_prompt()
        return message

    def init_debug_window(self):
        if self.debug:
            rows, cols = ChatClientUI.terminal_size()
            self.debug_window = curses.newwin(rows-1, cols//2+1, 0, 0)

    def redraw_debug(self, debug_history):
        if self.debug:
            self.debug_window.clear()
            rows = ChatClientUI.terminal_size()[0]
            row = rows - 3
            for message in debug_history:
                if row < 1:
                    break
                self.debug_window.move(row,1)
                self.debug_window.addstr(f"{message}")

    @staticmethod
    def terminal_size():
        rows, cols = os.popen("stty size", "r").read().split()
        return (int(rows), int(cols))
