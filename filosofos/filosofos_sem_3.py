#!/usr/bin/env python3
"""
Adrián Lattes Grassi, 12 de Marzo de 2021

Tercera solución del problema de los filósofos usando semáforos.
Misma solución que en el primer intento, salvo que introducimos un semáforo para
evitar que haya más de cuatro filósofos sentados en la mesa a la vez y de este
modo evitar la situación que generaba el deadlock.

Además he creado un proceso info que se encarga de informar de cuantas veces ha
comido cada filosofo.
"""

from multiprocessing import Process, current_process, Lock, BoundedSemaphore,\
        Array
from time import sleep
from random import random
from os import system

K = 100
speed = 100

current_philosopher = lambda: current_process().name

def think():
    # print(f"{current_philosopher()} thinking.")
    sleep(random()/speed)

def eat():
    # print(f"{current_philosopher()} eating.")
    sleep(random()/speed)

def live(index, room, forks, eat_counter):
    for i in range(K):
        # print(f"{current_philosopher()} sits at the table.")
        room.acquire()

        think()

        # print(f"{current_philosopher()} grabs left fork.")
        forks[index].acquire()
        # print(f"{current_philosopher()} grabs right fork.")
        forks[(index+1)%5].acquire()

        eat()
        eat_counter[index] += 1

        forks[index].release()
        forks[(index+1)%5].release()

        # print(f"{current_philosopher()} finished eating andgets up from the "\
        #         +"table.")
        room.release()

def print_info(eat_counter):
    while True:
        system("clear")
        exit = True
        for i in range(5):
            count = eat_counter[i]
            if count < K:
                exit = False
            print(f"Philosopher {i} has eaten {count} times.")
        if exit:
            break

if __name__ == "__main__":
    room = BoundedSemaphore(4)
    forks = [Lock() for _ in range(5)]
    eat_counter = Array('i', [0 for _ in range(5)])
    philosophers=[Process(target=live,name=f"Philosopher {i}",\
            args=(i,room,forks,eat_counter)) for i in range(5)]

    info = Process(target=print_info, name=f"info", args=(eat_counter,))
    info.start()

    for f in philosophers:
        f.start()
