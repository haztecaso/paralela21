from multiprocessing import Lock, Condition, Process, Value
from random import random, randint, expovariate
from time import sleep


DIRS = ['North','South'] # Direcciones en las que viajan los coches


def bold(s:str) -> str:
    """Utilidad para imprimir un str en negrita."""
    return f"\033[1m{s}\033[0m"


def delay(t:int):
    """
    Utilidad para esperar una cantidad tiempo aleatoria. Sirve para simular el
    movimiento de los coches

    Parámetro
    ---------
    t
        tiempo máximo (en segundos) del delay
    """
    sleep(random()*t)


class Car():
    """
    Clase para los coches

    Atributos
    ---------
    monitor : TunnelMonitor
        Monitor del túnel por el que viaja el coche
    id : int
        Identificador del coche. El método TunnelMonitor.addCar se encarga de que
        este identifiador sea único.
    dir : str
        Dirección del coche. Es un valor de tipo str que pertenece a la lista DIRS.
    process : Process
        Proceso del coche. Se puede arrancar con el método start.
    """

    def __init__(self, car_id: int, direction: str, monitor):
        """
        Constructora de la clase car.

        Parámetros
        ----------
        car_id
            Identificador del coche, con el que se inicializa el atributo id. El
            método TunnelMonitor.addCar se encarga de que este identifiador sea
            único.
        direction
            Valor de la dirección del coche, con el que se inicializa el atributo
            dir. Debe ser un valor perteneciente a la lista DIRS.
        monitor
            Monitor del túnel por el que viaja el coche, con el que se inicializa
            el atributo monitor.
        """

        self.id = car_id
        assert direction in DIRS, "direction must be in DIRS"
        self.dir = direction
        self.process = Process(target=self._run, name=f"Car {self.license_plate()}")
        self.monitor = monitor

    def _run(self):
        # Método privado que es ejecutado por el atributo process.
        delay(0.1)
        print(f"{self} {bold('wants to enter')} the tunnel")
        self.monitor.wants_enter(self.dir)
        print(f"{self} {bold('enters')} the tunnel")
        delay(0.01)
        self.monitor.leaves_tunnel(self.dir)
        print(f"{self} {bold('is out')} of the tunnel")

    def start(self):
        """.Método para iniciar el proceso del coche."""
        self.process.start()

    def __repr__(self) -> str:
        """Representación del coche."""
        return f"Car {self.license_plate()} heading {self.dir}"

    def license_plate(self) -> str:
        """
        Devuelve la matrícula correspondiente (en el formato de España) al id del
        coche.
        """
        numeros = f"{self.id % 10000:04d}"
        letras = "".join([chr(66+int(i)) for i in f"{self.id // 1000:03d}"])
        return numeros+letras
