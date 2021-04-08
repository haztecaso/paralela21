#!/usr/bin/env python3
from multiprocessing.connection import Client
from random import random
from time import sleep

from multiprocessing.connection import Listener
from multiprocessing import Process
import sys

def client_listener(info, conn):
    print(f"Opening listener at {info}")
    cl = Listener(address=(info['address'], info['port']),
            authkey=info['authkey'])
    conn.send(info)
    print('........client listener starting')
    print('........accepting connections')
    while True:
        conn = cl.accept()
        print(f'........connection accepted from {cl.last_accepted}')
        m = conn.recv()
        print(f'........message received from server: {m}')

def main(server_address, info):
    print('trying to connect')
    with Client(address=(server_address, 6000),
            authkey=b'secret password server') as conn:
        cl = Process(target=client_listener, args=(info,conn))
        cl.start()
        connected = True
        while connected:
            value = input("Send message: ")
            print("connection continued")
            conn.send(value)
            connected = value !='quit'
        cl.terminate()
    print("end client")

if __name__ == '__main__':
    server_address = "127.0.0.1"
    client_address = "127.0.0.1"
    client_port = 6001
    if len(sys.argv) > 1:
        client_port = int(sys.argv[1])
    if len(sys.argv) > 2:
        client_address = sys.argv[2]
    if len(sys.argv) > 3:
        server_address = sys.argv[3]
    info = {
            'address' : client_address,
            'port' : client_port,
            'authkey': b'secret client server'
            }
    main(server_address, info)
