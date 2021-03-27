#!/usr/bin/env python3
"""
Adrián Lattes Grassi, 11 de Marzo de 2012

Segunda solución del problema de los filósofos usando semáforos.
Misma solución que en el primer intento, salvo que el filósofo número cuatro
coge primero el tenedor de la derecha, para así evitar la situación que generaba
el deadlock.

Además he creado un proceso info que se encarga de informar de cuantas veces ha
comido cada filosofo.
"""

from multiprocessing import Process, Lock, current_process, Array
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

def live(index, forks, eat_counter, lefty=True):
    for i in range(K):
        think()

        if lefty:
            # print(f"{current_philosopher()} grabs left fork.")
            forks[index].acquire()
            # print(f"{current_philosopher()} grabs right fork.")
            forks[(index+1)%5].acquire()

        else:
            # print(f"{current_philosopher()} grabs right fork.")
            forks[(index+1)%5].acquire()
            # print(f"{current_philosopher()} grabs left fork.")
            forks[index].acquire()

        eat()
        eat_counter[index] += 1

        forks[index].release()
        forks[(index+1)%5].release()
        # print(f"{current_philosopher()} finished eating.")

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
    forks=[Lock() for _ in range(5)]
    eat_counter = Array('i', [0 for _ in range(5)])
    philosophers=[Process(target=live,name=f"Philosopher {i}",\
            args=(i, forks,eat_counter)) for i in range(4)]
    philosophers.append(Process(target=live,name=f"Philosopher 4",\
            args=(4, forks, eat_counter, False)))

    info = Process(target=print_info, name=f"info", args=(eat_counter,))
    info.start()

    for f in philosophers:
        f.start()
