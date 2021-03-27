#!/usr/bin/env python3
"""
Adrián Lattes Grassi, 12 de Marzo de 2021

Solución del problema de los filósofos con un monitor.

Además he creado un proceso info que se encarga de informar de cuantas veces ha
comido cada filosofo.
"""

from multiprocessing import Process, Value, Lock, Condition
from time import sleep
from random import random
from os import system

K = 50
speed = 10

class ForkMonitor:
    """
    Implementación inspirada en el algoritmo 7.5 del libro de M. Ben-Ari.
    """
    def __init__(self):
        self.lock = Lock()
        self.freeForks = [2 for _ in range(5)]
        self.okToEat = [Condition(self.lock) for _ in range(5)]

    def takeForks(self,i):
        self.lock.acquire()
        while self.freeForks[i] < 2:
            self.okToEat[i].wait()
        self.freeForks[(i+1)%5] -= 1
        self.freeForks[(i-1)%5] -= 1
        self.lock.release()

    def releaseForks(self,i):
        self.lock.acquire()
        self.freeForks[(i+1)%5] += 1
        self.freeForks[(i-1)%5] += 1
        if self.freeForks[(i+1)%5] == 2:
            self.okToEat[(i+1)%5].notify()
        if self.freeForks[(i-1)%5] == 2:
            self.okToEat[(i-1)%5].notify()

        self.lock.release()


class Philosopher:
    def __init__(self, monitor, index):
        self.index = index
        self.name = f"Philosopher {index}"
        self.eat_counter = Value('i',0)
        self._monitor = monitor
        self._process = Process(target=self.live, name=self.name)

    def print_info(self):
        print(f"{self.name} has eaten {self.eat_counter.value} times.")

    def think(self):
        sleep(random()/speed)

    def eat(self):
        self.eat_counter.value += 1
        sleep(random()/speed)

    def live(self):
        for _ in range(K):
            self.think()
            self._monitor.takeForks(self.index)
            self.eat()
            self._monitor.releaseForks(self.index)

    def is_alive(self):
        return (self.eat_counter.value < K)

    def start(self):
        self._process.start()
        
def print_info(philosophers):
    while True:
        system("clear")
        exit = True
        for i in range(5):
            p = philosophers[i]
            p.print_info()
            if p.is_alive():
                exit = False
        if exit:
            break

def main():
    monitor = ForkMonitor()
    philosophers = [Philosopher(monitor, n) for n in range(5)]

    info = Process(target=print_info, name=f"info", args=(philosophers,))
    info.start()

    for p in philosophers:
        p.start()

if __name__ == '__main__':
    main()
