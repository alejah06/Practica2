# -*- coding: utf-8 -*-


from multiprocessing import Process
from multiprocessing import Condition, Lock
from multiprocessing import Value
from multiprocessing import current_process
import time, random

NORTH = "north"
SOUTH = "south"
max_waitlist = 5
K = 10
NCARS = 20
NPED = 10



class Monitor():
    def __init__(self):
        self.mutex = Lock()
        self.cars_north = Value('i', 0)
        self.cars_south = Value('i', 0)
        self.sem_ped = Condition(self.mutex)
        self.sem_north = Condition(self.mutex)
        self.sem_south = Condition(self.mutex)
        self.pedestrians = Value('i', 0)
        self.pedestrians_w = Value('i', 0)
        self.pedestrians_counter = Value('i', 0)
        self.cars_north_w = Value('i', 0)
        self.cars_south_w = Value('i', 0)
        self.counter_north = Value('i', 0)
        self.counter_south = Value('i', 0)
        
        
    def cars_can_go_north(self):
        return (self.cars_south.value == 0 and self.pedestrians.value == 0) and \
            (self.counter_north.value < max_waitlist or (self.cars_south_w.value == 0\
             and self.pedestrians_w.value == 0))
    def cars_can_go_south(self):
        return (self.cars_north.value == 0 and self.pedestrians.value == 0) and \
            (self.counter_south.value < max_waitlist or (self.cars_north_w.value == 0\
             and self.pedestrians_w.value == 0))
    
    def pedestrians_can_cross(self):
        return (self.cars_north.value == 0 and self.cars_south.value == 0) and \
            (self.pedestrians_counter.value < max_waitlist or (self.cars_north_w.value == 0\
            and self.cars_south_w.value == 0))
        

    
    def pedestrian_wants_to_cross(self):
        self.mutex.acquire()
        self.pedestrians_w.value += 1
        self.sem_ped.wait_for(self.pedestrians_can_cross)
        self.pedestrians.value += 1
        self.pedestrians_w.value -= 1
        self.pedestrians_counter.value += 1
        self.mutex.release()
    
    def car_wants_to_cross(self, direction):
        self.mutex.acquire()
        if direction == NORTH:
            self.cars_north_w.value += 1
            self.sem_north.wait_for(self.cars_can_go_north)
            self.cars_north.value += 1
            self.cars_north_w.value -= 1
            self.counter_north.value += 1
            self.mutex.release()
        if direction == SOUTH:
            self.cars_south_w.value += 1
            self.sem_south.wait_for(self.cars_can_go_south)
            self.cars_south.value += 1
            self.cars_south_w.value -= 1
            self.counter_south.value += 1
            self.mutex.release()
            
    def car_crossed(self, direction):
        self.mutex.acquire()
        if direction == NORTH:
            self.cars_north.value -= 1
            if self.cars_north.value == 0:
                self.pedestrians_counter.value = 0
                if self.pedestrians_w.value == 0:
                    self.counter_south.value = 0
                
            self.sem_north.notify_all()
            self.sem_south.notify_all()
            self.sem_ped.notify_all()
        if direction == SOUTH:
            self.cars_south.value -= 1
            if self.cars_south.value == 0:
                self.counter_north.value = 0
                if self.cars_north_w.value == 0: 
                    self.pedestrians_counter.value = 0
                
            self.sem_north.notify_all()
            self.sem_south.notify_all()
            self.sem_ped.notify_all()
        self.mutex.release()
    
    def pedestrian_crossed(self):
        self.mutex.acquire()
        self.pedestrians.value -= 1
        if self.pedestrians.value == 0:
            self.counter_south.value = 0
            if self.cars_south_w.value == 0:
                self.counter_north.value = 0
                
            self.sem_north.notify_all()
            self.sem_south.notify_all()
            self.sem_ped.notify_all()
            
        self.mutex.release()
            
            
            
            
def delay(d=3):
    time.sleep(random.random()/d)
            
def car(monitor: Monitor, direction):
    for k in range(K):
        delay()
        print(f"Coche {current_process().name} quiere cruzar en direccion {direction}")
        monitor.car_wants_to_cross(direction)
        print(f"Coche {current_process().name} cruzando en direccion {direction}")
        delay()
        monitor.car_crossed(direction)
        print(f"Coche {current_process().name} ha cruzado el puente en direccion {direction}")
        
def pedestrian(monitor: Monitor):
    for k in range(K):
        delay()
        print(f"Peaton {current_process().name} quiere cruzar")
        monitor.pedestrian_wants_to_cross()
        print(f"Peaton {current_process().name} cruzando")
        delay()
        monitor.pedestrian_crossed()
        print(f"Peaton {current_process().name} ha cruzado el puente")
        
def main():
    monitor = Monitor()
    list_cars = [ Process(target=car,args=(monitor, NORTH)) if random.randint(0,1)==1 \
                 else Process(target=car,args=(monitor, SOUTH)) \
                 for i in range(NCARS)]
    list_ped = [ Process(target=pedestrian,args=(monitor,))\
                for i in range(NPED)]
    for p in list_cars + list_ped:
        p.start()
    for p in list_cars + list_ped:
        p.join()
        
if __name__ == '__main__':
    main()
    
        
                
        