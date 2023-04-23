import time
import random
from multiprocessing import Lock, Condition, Process
from multiprocessing import Value

SOUTH = 1
NORTH = 0
#Habrá 25 coches en cada dirección, 50 en total cambiamos este número para que
#el resultado no se tan largo
NCARS = 25
NPED = 5
TIME_CARS_NORTH = 0.5  # a new car enters each 0.5s
TIME_CARS_SOUTH = 0.5  # a new car enters each 0.5s
TIME_PED = 5 # a new pedestrian enters each 5s
TIME_IN_BRIDGE_CARS = (1, 0.5) # normal 1s, 0.5s
TIME_IN_BRIDGE_PEDESTRGIAN = (3, 0,5) # normal 1s, 0.5s


class Monitor():
    def __init__(self):
        self.mutex = Lock()
        self.patata = Value('i', 0)
       #Número de coches del norte,sur y peatones pasando por el puente
        self.coches_norte = Value('i', 0)
        self.coches_sur = Value('i', 0)
        self.peatones = Value('i', 0)
       #variables para ver cuantos elementos de cada tipo están esperando
        self.coches_norte_esperando = Value('i', 0)
        self.coches_sur_esperando = Value('i', 0)
        self.peatones_esperando = Value('i', 0)
       #Variables condición que se tienen que cumplir para que puedan entrar al puente
        self.cocheN = Condition(self.mutex)
        self.cocheS = Condition(self.mutex)
        self.ped = Condition(self.mutex)
       
        self.turno = Value('i', -1)
        '''
        Para mejorarla práctica y no tener problemas de inanición creamos un sistema de turnos
        asignando los siguientes valores:
            -1 no hay nadie esperando
            0 los coches con dirección norte pueden pasar
            1 los coches con dirección sur pueden pasar
            2 los peatones pueden pasar
        '''
        
    #Estas 6 funciones siquientes equivalen a las condiciones que definen el invariante planteado a papel
    #Son las conndiciones que se tienen que cumplir para que se pueda entrar en el puente
    def no_hay_coches_norte(self):
        return self.coches_norte.value == 0
   
    def no_hay_coches_sur(self):
        return self.coches_sur.value == 0
   
    def no_hay_peatones(self):
        return self.peatones.value == 0
   
    def pasan_Cnorte(self):
        return self.no_hay_peatones() and self.no_hay_coches_sur() and (self.turno.value == 0 or self.turno.value == -1 or (self.coches_sur_esperando.value <= 5 and self.peatones_esperando.value <= 3))      
   
    def pasan_Csur(self):
        return self.no_hay_peatones() and self.no_hay_coches_norte() and (self.turno.value == 1 or self.turno.value == -1 or (self.coches_norte_esperando.value <= 5 and self.peatones_esperando.value <= 3))
               
    def pasan_peatones(self):
       return (self.no_hay_coches_norte() and self.no_hay_coches_sur()) and (self.turno.value == 2 or self.turno.value == -1 or(self.coches_norte_esperando.value <= 5 and self.coches_sur_esperando.value <= 5))


    def wants_enter_car(self, direction: int) -> None:
        self.mutex.acquire()
        self.patata.value += 1
       
        if direction == NORTH:
            self.coches_norte_esperando.value +=1#si un coche quire pasar se suma 1 a los que estan esperando
            self.cocheN.wait_for(self.pasan_Cnorte)#si cimple las condiciones entra en el puente
            self.coches_norte_esperando.value -=1#restamos el coche al numero de coches esperando
       
            if self.turno.value == -1: #si no hay nadie esperando le cedemos
                self.turno.value = 0   #el turno a los del norte
            self.coches_norte.value += 1  #añadimos uno al nº de coches del norte en el puente
        else:                            #analogo pero con los coches del sur
            self.coches_sur_esperando.value +=1
            self.cocheS.wait_for(self.pasan_Csur)
            self.coches_sur_esperando.value -=1
       
            if self.turno.value == -1: 
                self.turno.value = 1  
            self.coches_sur.value += 1
       
        self.mutex.release()

    def leaves_car(self, direction: int) -> None:
        self.mutex.acquire()
        self.patata.value += 1
       
        if direction == NORTH:
            self.coches_norte.value -= 1 #restamos un coche del norte por salir del puente
           
            if self.turno.value == 0:
                if self.peatones_esperando != 0:
                    self.turno.value = 2   # EL turno cambia al de los peatones si hay algien esperando
                elif self.coches_sur_esperando != 0:
                    self.turno.value = 1   # Si no cambia a los coches del sur
                else:
                    self.turno.value = -1  # si no hay nadie esperando el turno se marcaría como vacío 
                                           #y el turno entonces volvería a los del norte como aparece en la función anterior

            if self.coches_norte.value == 0:
                self.ped.notify_all()
                self.cocheS.notify_all()    #Cuando ya no hay mas coches pasando, se lo notificamos a las demás variables                
        else:
            self.coches_sur.value -= 1
           
            if self.turno.value == 1:
                if self.coches_norte_esperando.value != 0:
                    self.turno.value = 0
                elif self.peatones_esperando.value != 0:
                    self.turno.value = 2
                else:
                    self.turno.value = -1
           
            if self.coches_sur.value == 0:
                self.cocheN.notify_all()
                self.ped.notify_all()  
       
        self.mutex.release()
       
    #Las siguientes funciones son análogas que las de los coches pero sin distinguir direcciones
    def wants_enter_pedestrian(self) -> None:
        self.mutex.acquire()
        self.patata.value += 1
       
        self.peatones_esperando.value += 1
        self.ped.wait_for(self.pasan_peatones)
        self.peatones_esperando.value -= 1
       
        if self.turno.value == -1:
            self.turno.value = 2
           
        self.peatones.value += 1
       
        self.mutex.release()

    def leaves_pedestrian(self) -> None:
        self.mutex.acquire()
        self.patata.value += 1
        self.peatones.value -= 1
       
        if self.turno.value == 2:
            if self.coches_sur_esperando.value != 0:
                self.turno.value = 1          
            elif self.coches_norte_esperando.value != 0:
                self.turno.value = 0          
            else:
                self.turno.value = -1
       
        if self.peatones.value == 0:
            self.cocheS.notify_all() 
            self.cocheN.notify_all()
        self.mutex.release()

    def __repr__(self) -> str:
        return f'Monitor: {self.patata.value}'
#los valores del tiempo que tardan son aleatorios dentro de que sigue una distribución normal:
def delay_car_north() -> None:
    a=random.normalvariate(TIME_IN_BRIDGE_CARS[0],TIME_IN_BRIDGE_CARS[1])
    if a <0:
        a=0
    time.sleep(a)
    
def delay_car_south()-> None:
    a=random.normalvariate(TIME_IN_BRIDGE_PEDESTRGIAN [0],TIME_IN_BRIDGE_PEDESTRGIAN [1])
    if a <0:
        a=0
    time.sleep(a)

def delay_pedestrian() -> None:
    a=random.normalvariate(TIME_IN_BRIDGE_CARS[0],TIME_IN_BRIDGE_CARS[1])
    if a <0:
        a=0
    time.sleep(a)

def car(cid: int, direction: int, monitor: Monitor)  -> None:
    print(f"car {cid} heading {direction} wants to enter. {monitor}")
    monitor.wants_enter_car(direction)
    print(f"car {cid} heading {direction} enters the bridge. {monitor}")
    if direction==NORTH :
        delay_car_north()
    else:
        delay_car_south()
    print(f"car {cid} heading {direction} leaving the bridge. {monitor}")
    monitor.leaves_car(direction)
    print(f"car {cid} heading {direction} out of the bridge. {monitor}")

def pedestrian(pid: int, monitor: Monitor) -> None:
    print(f"pedestrian {pid} wants to enter. {monitor}")
    monitor.wants_enter_pedestrian()
    print(f"pedestrian {pid} enters the bridge. {monitor}")
    delay_pedestrian()
    print(f"pedestrian {pid} leaving the bridge. {monitor}")
    monitor.leaves_pedestrian()
    print(f"pedestrian {pid} out of the bridge. {monitor}")



def gen_pedestrian(monitor: Monitor) -> None:
    pid = 0
    plst = []
    for _ in range(NPED):
        pid += 1
        p = Process(target=pedestrian, args=(pid, monitor))
        p.start()
        plst.append(p)
        time.sleep(random.expovariate(1/TIME_PED))

    for p in plst:
        p.join()

def gen_cars(direction: int, time_cars, monitor: Monitor) -> None:
    cid = 0
    plst = []
    for _ in range(NCARS):
        cid += 1
        p = Process(target=car, args=(cid, direction, monitor))
        p.start()
        plst.append(p)
        time.sleep(random.expovariate(1/time_cars))

    for p in plst:
        p.join()


def main():
    monitor = Monitor()
    gcars_north = Process(target=gen_cars, args=(NORTH, TIME_CARS_NORTH, monitor))
    gcars_south = Process(target=gen_cars, args=(SOUTH, TIME_CARS_SOUTH, monitor))
    gped = Process(target=gen_pedestrian, args=(monitor,))
    gcars_north.start()
    gcars_south.start()
    gped.start()
    gcars_north.join()
    gcars_south.join()
    gped.join()


if __name__ == '__main__':
    main()