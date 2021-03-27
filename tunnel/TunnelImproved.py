#!/usr/bin/env python3
from multiprocessing import Condition, Process, Value
from TunnelCommon import TunnelMonitor
from Car import DIRS

class TunnelImproved(TunnelMonitor):
    """
    Clase que implementa la segunda solución al problema del Túnel.
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
        self._enter_condition = Condition(self._lock)

    def can_enter(self, direction : str) -> bool:
        """
        Método que determina si se puede entrar en el túnel.

        Parámetro
        ---------
        direction
            Dirección desde la que se quiere entrar.
        """
        return self._current_dir.value == -1 or \
                self._current_dir.value == DIRS.index(direction)

    def wants_enter(self, direction:str):
        """
        Método que usan los coches para indicar que quieren entrar en el túnel

        Parámetro
        ---------
        direction
            Dirección del coche que quiere entrar
        """
        self._lock.acquire()
        # Como quiero pasar parámetros a la función can_enter, ya no puedo usar
        # un wait_for. Por tanto uso un while, que como indica la documentación es
        # equivalente al wait_for: https://docs.python.org/3/library/threading.html#threading.Condition.wait_for
        while not self.can_enter(direction):
            self._enter_condition.wait()
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
        self._lock.release()


if __name__ == "__main__":
    import sys
    ncars = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    tunnel = TunnelImproved(ncars = ncars)
    tunnel.start()
