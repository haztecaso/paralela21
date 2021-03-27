#!/usr/bin/env python3
from multiprocessing import Lock, Process
from random import randint, expovariate
from time import sleep
from Car import DIRS, Car


class TunnelMonitor():
    """
    Clase base para un monitor de un túnel. En esta clase están definidos los
    atributos y métodos comunes en todas las implementaciones de las distintas
    versiones del monitor. De este modo se evita la repetición de código.

    Atributos
    ---------
    cars : list[Car]
        Lista de coches que están pasando o han pasado ya por el túnel
    ncars : int
        Número de coches que pasarán por el túnel
    interval : float
        Intervalo medio de tiempo (en segundos) de entrada de los coches en el
        túnel
    _lock : Lock
        Atributo privado. Lock para proteger las secciones críticas.
    """

    def __init__(self, ncars:int = 100, interval:float = 0.05):
        """
        Constructora de la clase TunnelMonitor.

        Parámetros
        ----------
        ncars
            Número de coches que pasarán por el túnel, con el que se inicializa el
            atributo ncars.
        interval
            Intervalo medio de tiempo de entrada de los coches, con el que se
            inicializa el atributo interval.
        """
        self.cars = []
        self.ncars = ncars
        self.interval = interval
        self._lock = Lock()

    def start(self):
        """
        Método principal de la clase, en el que se ejecuta el bucle principal del
        túnel, que va creando los coches, teniendo en cuenta los atributos ncars y
        interval.

        Las direcciones en las que viajan los coches se asignan aleatoriamente.
        """
        for i in range(self.ncars):
            direction = DIRS[0] if randint(0,1) else DIRS[1]
            new_car = self.addCar(direction)
            new_car.start()
            # A new car enters every {self.interval} seconds
            sleep(expovariate(1/self.interval))

    def addCar(self, direction : str) -> Car:
        """
        Método para crear un coche que viaja en una dirección

        Parámetro
        ---------
        direction
            Dirección en la que viaja el coche, que se pasa como parámetro a la
            constructora de la clase Car. Por tanto su valor debe pertenecer a la
            lista DIRS.
        """
        car_id = randint(0,1000000)
        while car_id in [car.id for car in self.cars]:
            car_id = randint(0,1000000)
        new_car = Car(car_id, direction, self)
        self.cars.append(new_car)
        return new_car

    def wants_enter(self, direction:str):
        """
        Método que usan los coches para indicar que quieren entrar en el túnel.
        La implementación de este método es responsabilidad de las subclases.

        Parámetro
        ---------
        direction
            Dirección del coche que quiere entrar
        """
        raise NotImplementedError("This class is not meant to be used directly!")

    def leaves_tunnel(self, direction:str):
        """
        Método que usan los coches para indicar que van a salir del túnel.
        La implementación de este método es responsabilidad de las subclases.

        Parámetro
        ---------
        direction
            Dirección del coche que quiere entrar
        """
        raise NotImplementedError("This class is not meant to be used directly!")

    def __repr__(self) -> str:
        """Representación del TunnelMonitor."""
        return f"TunnelMonitor with {self.ncars} cars."
