#!/usr/bin/env python3
"""
Adrián Lattes Grassi, 11 de Marzo de 2021

Primer intento de solución del problema de los filósofos usando semáforos. Cada
filósofo coge primero el tenedor de la izquierda, por lo que si todos los
filosofos han cogido un tenedor, se puede entrar en deadlock.
"""

from multiprocessing import Process, Lock, current_process
from time import sleep
from random import random

K = 1000
speed = 10000

current_philosopher = lambda: current_process().name

def think():
    print(f"{current_philosopher()} thinking.")
    sleep(random()/speed)

def eat():
    print(f"{current_philosopher()} eating.")
    sleep(random()/speed)

def live(forks, index):
    for i in range(K):
        think()

        print(f"{current_philosopher()} grabs left fork.")
        forks[index].acquire()
        print(f"{current_philosopher()} grabs right fork.")
        forks[(index+1)%5].acquire()

        eat()

        forks[index].release()
        forks[(index+1)%5].release()
        print(f"{current_philosopher()} finished eating.")

if __name__ == "__main__":
    forks = [Lock() for _ in range(5)]
    philosophers =[Process(target=live, name=f"Philosopher {i}",\
            args=(forks, i)) for i in range(5)]

    for f in philosophers:
        f.start()
    for f in philosophers:
        f.join()
