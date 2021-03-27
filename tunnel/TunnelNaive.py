#!/usr/bin/env python3
from multiprocessing import Condition, Process, Value
from TunnelCommon import TunnelMonitor
from Car import DIRS

class TunnelNaive(TunnelMonitor):
    """
    Clase que implementa la primera solución al problema del Túnel.
    Los detalles de la implementación están en el fichero readme.md

    Atributos
    ---------
    _enter_condition : Condition
        Atributo privado. Condición para indicar si el túnel está vacío o no.
    _is_empty : Value('h')
        Atributo privado.
        - El valor 0 indica que no hay ningún coche en el túnel.
        - El valor 1 indica que hay un coche en el túnel.
    """

    def __init__(self, ncars:int = 100, interval:float=0.5):
        """
        Constructora de la clase TunnelNaive.

        Los parámetros de entrada son los mismos que para la constructora de la
        clase base TunnelMonitor.
        """
        TunnelMonitor.__init__(self, ncars, interval)
        self._is_empty = Value('h', 0)
        self._enter_condition = Condition(self._lock)

    def can_enter(self) -> bool:
        """Método que determina si se puede entrar en el túnel."""
        return self._is_empty.value == 0

    def wants_enter(self, _):
        """
        Método que usan los coches para indicar que quieren entrar en el túnel

        Parámetro
        ---------
            _
                Parámetro ignorado, necesario para que la interfaz de este
                método sea la misma para todos los monitores.
        """
        self._lock.acquire()
        self._enter_condition.wait_for(self.can_enter)
        self._is_empty.value = 1
        self._lock.release()

    def leaves_tunnel(self, _):
        """
        Método que usan los coches para indicar que van a salir del túnel

        Parámetro
        ---------
            _
                Parámetro ignorado, necesario para que la interfaz de este
                método sea la misma para todos los monitores.
        """
        self._lock.acquire()
        self._enter_condition.notify()
        self._is_empty.value = 0
        self._lock.release()


if __name__ == "__main__":
    import sys
    ncars = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    tunnel = TunnelNaive(ncars = ncars)
    tunnel.start()
