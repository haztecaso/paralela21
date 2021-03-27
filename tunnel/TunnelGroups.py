#!/usr/bin/env python3
from multiprocessing import Condition, Process, Value, Array
from TunnelCommon import TunnelMonitor
from Car import DIRS

class TunnelGroups(TunnelMonitor):
    """
    Clase que implementa la tercera solución al problema del Túnel.
    Los detalles de la implementación están en el fichero readme.md

    Atributos
    ---------
    _enter_condition : Condition
        Atributo privado. Condición para indicar si el túnel está vacío o no.
    _current_dir : Value('h')
        Atributo privado. Valor de tipo short (int) que indica en que dirección
        están circulando los coches actualmente.
        - El valor -1 indica que no hay ningún coche en el túnel
        - El valor 0 indica que los coches están circulando hacia DIRS[0]
        - El valor 1 indica que los coches están circulando hacia DIRS[1]
    _current_ncars : Value('i')
        Atributo privado. Valor de tipo int que indica cuantos coches están
        circulando actualmente por el túnel.
    _waiting_cars : Array('i', 2)
        Atributo privado. Array de ints que almacena cuantos coches están
        esperando para entrar en el túnel de cada lado. La posición 0 se
        corresponde a la dirección DIRS[0] y la 1 a DIRS[1].
    _current_max_ncars : Value('i')
        Atributo privado. Valor de tipo int que indica cuantos coches pueden
        pasar como máximo en el turno actual. El valor cero indica que no hay un
        máximo actual.
    """

    def __init__(self, ncars:int = 100, interval:float = 0.05):
        """
        Constructora de la clase TunnelNaive.

        Los parámetros de entrada son los mismos que para la constructora de la
        clase base TunnelMonitor.
        """
        TunnelMonitor.__init__(self, ncars, interval)
        self._current_dir = Value('h', -1)
        self._current_ncars = Value('i', 0)
        self._current_max_ncars = Value('i', 0)
        self._waiting_cars = Array('i', [0,0])
        self._enter_condition = Condition(self._lock)

    def can_enter(self, direction : str) -> bool:
        """
        Método que determina si se puede entrar en el túnel.

        Parámetro
        ---------
        direction
            Dirección desde la que se quiere entrar.
        """
        dir_index = DIRS.index(direction)
        current_dir = self._current_dir.value
        no_collision_risk = current_dir == -1 or  current_dir == dir_index
        max_ncars = self._current_max_ncars.value
        current_ncars = self._current_ncars.value
        dont_exceed_max = True if max_ncars == 0 else current_ncars <= max_ncars
        return no_collision_risk and dont_exceed_max

    def wants_enter(self, direction:str):
        """
        Método que usan los coches para indicar que quieren entrar en el túnel

        Parámetro
        ---------
        direction
            Dirección del coche que quiere entrar
        """
        self._lock.acquire()
        dir_index = DIRS.index(direction)
        self._waiting_cars[dir_index] += 1

        # Como quiero pasar parámetros a la función can_enter, ya no puedo usar
        # un wait_for. Por tanto uso un while, que como indica la documentación es
        # equivalente al wait_for: https://docs.python.org/3/library/threading.html#threading.Condition.wait_for
        while not self.can_enter(direction):
            self._enter_condition.wait()

        dir_index2 = (dir_index+1)%2
        if self._current_max_ncars == 0 and self._waiting_cars[dir_index2]!=0:
            self._current_max_ncars.value = self._waiting_cars[dir_index].value
        self._waiting_cars[dir_index] -= 1
        if self._current_dir.value == -1:
            self._current_dir.value = DIRS.index(direction)
        self._current_ncars.value += 1
        self._lock.release()

    def leaves_tunnel(self, direction:str):
        """
        Método que usan los coches para indicar que van a salir del túnel

        Parámetro
        ---------
        direction
            Dirección del coche que quiere entrar
        """
        self._lock.acquire()
        self._enter_condition.notify()
        self._current_ncars.value -= 1
        if self._current_ncars.value == 0:
            self._current_dir.value = -1
            self._current_max_ncars = 0
        self._lock.release()


if __name__ == "__main__":
    import sys
    ncars = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    tunnel = TunnelGroups(ncars = ncars)
    tunnel.start()
