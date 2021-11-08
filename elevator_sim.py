class FloorQueue:
    '''
    A queue on a floor of our building
    '''
    
    def __init__(self, floor):
        self.queue = []
        self.floor = floor
        self.next_arrival_time = None

    def length(self):
        '''
        Returns the length of the queue
        '''
        return len(self.queue)

    def is_empty(self):
        '''
        Returns True if the queue contains no elements,
        and False otherwise.
        '''
        return len(self.queue) == 0

    def enqueue(self, value):
        '''
        Enqueue a value in the queue (i.e., add the value
        at the back of the queue).

        Returns: True if the value was enqueue; False if
        it wasn't enqueued because the queue has reached
        its maximum capacity.
        '''
        self.queue.append(value)

    def dequeue(self):
        '''
        Dequeue a value from the queue (i.e., remove the
        element at the front of the queue, and remove it
        from the queue)

        Returns: The dequeued value
        '''

        return self.queue.pop(0)

    def __repr__(self):
        '''
        Returns a string representation of the queue.
        '''
        s = ""

        for v in reversed(self.queue):
            s += " --> " + str(v)

        s += " -->"

        return s

class Passenger:
    '''
    A passenger using our elevator system
    '''

    def __init__(self, pid, floor, arrival_time):
        self.pid = pid
        self.floor = floor
        self.arrival_time = arrival_time
        self.departure_time = None

    def get_wait(self):
        if self.departure_time is None:
            return None
        else:
            return self.departure_time - self.arrival_time

    def get_floor(self):
        return self.floor
        
    def __str__(self):
        return "Passenger({}, {}, {})".format(self.pid, self.floor, self.arrival_time)
    
    def __repr__(self):
        return str(self)

class Elevator:
    '''
    An elevator in our elevator bank
    '''

    def __init__(self, elev_id, default_floors, floors, max_capacity):
        self.elev_id = elev_id
        self.default_floors = default_floors
        self.in_use = False
        self.direction = None
        self.current_floor = None
        self.max_capacity = max_capacity
        self.passengers = []
        self.floors = floors
        self.next_stop_time = None
        self.called_floor = None
        self.last_time_used = None
    
    def get_num_passengers(self):
        return len(self.passengers)

    def is_empty(self):
        return len(self.passengers) == 0

    def get_open_spots(self):
        return self.max_capacity - len(self.passengers)

    def get_distance(self, floor):
        return abs(self.current_floor - floor)

    def at_default(self):
        return self.current_floor in self.default_floors

    def load(self, floor):
        open_spots = self.get_open_spots()
        count = 0
        for index, passenger in enumerate(floor.queue):
            if index < open_spots:
                self.passengers.append(passenger)
                count +=1
        self.passengers = sorted(self.passengers, key = lambda passenger: 
        passenger.floor)
        
        for i in range(count):
            floor.dequeue()


    def unload(self):
        for passenger in self.passengers:
            if passenger.floor == self.current_floor:
                self.passengers.remove(passenger)

    def max_desired_floor(self):
        return max(passenger.floor for passenger in self.passengers)

    
class ElevatorBank:
    '''
    A bank of elevators
    '''

    def __init__(self, num_elevators, num_floors, default_floors,
    move_speed = 1, max_capacity = 10):
        
        floor_list = []
        for i in range(num_floors):
            floor_list.append(FloorQueue(i))

        elev_list = []
        for i in range(num_elevators):
            elev_list.append(Elevator(i, default_floors, floor_list, 
            max_capacity))

        self.elevators = elev_list
        self.num_elevators = num_elevators
        self.floors = floor_list
        self.num_floors = num_floors
        self.default_floors = default_floors
        self.move_speed = move_speed
        self.call_list = []
        self.active_calls = []

    def all_in_use(self):
        for elevator in self.elevators:
            if not elevator.in_use:
                return False
        return True

    def get_closest(self, floor):
        best = None
        for elevator in self.elevators:
            if not elevator.in_use:
                if best == None:
                    best = elevator
                else: 
                    if elevator.get_distance(floor) < best.get_distance(floor):
                        best = elevator
        return best

    def move_elevator(self, elevator, floor):
        elevator.current_floor = floor

    def place_elevator_call(self, floor):
        self.call_list.append(floor)

    def get_next_stop(self):
        next = None
        for elevator in self.elevators:
            if next == None:
                if elevator.next_stop_time != None:
                    next = elevator.next_stop_time
            elif next != None and elevator.next_stop_time != None:
                if elevator.next_stop_time < next:
                    next = elevator.next_stop_time
        return next


    def closest_unoccupied_default(self, elevator):
        unocc_default_list = self.default_floors.copy()
        for elevator in self.elevators:
            if elevator.at_default():
                unocc_default_list.remove(elevator.current_floor)
        if len(unocc_default_list) == 0:
            return min(abs(elevator.current_floor - floor) for floor in
            self.default_floors)
        else:
            return min(abs(elevator.current_floor - floor) for floor in 
            unocc_default_list)

from sympy import *
import random

def simulate_elevators(num_elevators, num_floors, default_floors, default_reset_time, 
    move_speed, max_capacity, max_time, up_freq_expr, down_freq_expr, min_freq, sigma):

    x = Symbol('x')
    f_up = parse_expr(up_freq_expr)
    f_down = parse_expr(down_freq_expr)
    f_up = lambdify(x, f_up)
    f_down = lambdify(x, f_down)

    bank = ElevatorBank(num_elevators, num_floors, default_floors,
    move_speed, max_capacity)

    t = 0

    for index, floor in enumerate(default_floors):
        bank.elevators[index].current_floor = floor

    bank.floors[1].next_arrival_time = min(round(abs(random.gauss((1/re(f_down(t))), sigma))), min_freq)

    bank.floors[0].next_arrival_time = min(round(abs(random.gauss((1/re(f_up(t))), sigma))), min_freq)

    completed_rides = []
    pid = 0
    
    t = round(min(bank.floors[0].next_arrival_time, bank.floors[1].next_arrival_time))

    for elevator in bank.elevators:
        elevator.last_time_used = t

    while t < max_time:

        # print(t)

        for elevator in bank.elevators:
            if (t - elevator.last_time_used) < default_reset_time and \
                elevator.current_floor not in default_floors:
                floor = bank.closest_unoccupied_default(elevator)
                bank.move_elevator(elevator, floor)
                # print('moved elevator', elevator.elev_id, 'to default floor', floor)

        #For adding someone to floor 0
        if t == round(bank.floors[0].next_arrival_time):
            passenger = Passenger(pid, random.randrange(1, num_floors), t)
            bank.floors[0].enqueue(passenger)
            # print('added passenger', pid, 'to floor', 0)
            pid += 1

            bank.floors[0].next_arrival_time = t + min(round(abs(random.gauss((1/re(f_up(t))), 
            sigma))), min_freq)

        #For adding someone to residential floors
        if t == round(bank.floors[1].next_arrival_time):
            passenger = Passenger(pid, 0, t)
            floor = bank.floors[random.randrange(1, num_floors)]
            floor.enqueue(passenger)
            # print('added passenger', pid, 'to floor', floor.floor)
            pid += 1

            bank.floors[1].next_arrival_time = t + min(round(abs(random.gauss((1/re(f_down(t))), 
            sigma))), min_freq)

        #For calling an elevator to waiting passengers        
        for floor in bank.floors:
            if not floor.is_empty() and floor.floor not in bank.call_list and \
                floor.floor not in bank.active_calls:
                bank.place_elevator_call(floor.floor)
                # print('placed call to', floor.floor)
                # print('call list:', bank.call_list)
        
        #For assigning elevators to called floors
        if not bank.all_in_use():
            floors_to_remove = []
            for called_floor in bank.call_list:
                elevator = bank.get_closest(called_floor)
                floor = bank.floors[called_floor]

                floor_diff = elevator.get_distance(called_floor)
                elevator.next_stop_time = t + bank.move_speed*floor_diff
                elevator.called_floor = called_floor
                # print('assigned elevator', elevator.elev_id, 'to call from floor', called_floor)
                elevator.in_use = True

                floors_to_remove.append(called_floor)
                bank.active_calls.append(called_floor)

                if bank.all_in_use():
                    break
            for rm_floor in floors_to_remove:
                bank.call_list.remove(rm_floor)
                # print('call list:', bank.call_list)

        #For processing a non idle elevator at its stop
        for elevator in bank.elevators:
            if elevator.next_stop_time == None:
                check = None
            else:
                check = round(elevator.next_stop_time)
            if t == check:
                
                #For elevators dropping off passengers
                if not elevator.is_empty():
                    bank.move_elevator(elevator, elevator.passengers[0].floor)
                    for passenger in elevator.passengers:
                        if passenger.floor == elevator.current_floor:
                            passenger.departure_time = t
                            completed_rides.append(passenger)
                            elevator.passengers.remove(passenger)
                            # print('dropped passenger', passenger.pid, 'at floor', elevator.current_floor)
                    elevator.in_use = False

                #For elevators that were called to a floor
                if elevator.is_empty() and elevator.called_floor != None:
                    bank.move_elevator(elevator, elevator.called_floor)
                    floor = bank.floors[elevator.current_floor]
                    bank.active_calls.remove(elevator.called_floor)

                    elevator.load(floor)
                    elevator.in_use = True
                    elevator.called_floor = None
                    # print('elevator', elevator.elev_id, 'arrives at floor', elevator.current_floor, ', picks up passengers')

                    floor_diff = abs(called_floor - elevator.passengers[0].floor)
                    elevator.next_stop_time = t + bank.move_speed*floor_diff
                
                #For elevators that just dropped off passengers and load more
                if elevator.is_empty() and elevator.called_floor == None:
                    floor = bank.floors[elevator.current_floor]
                    if not floor.is_empty() and floor.floor not in bank.active_calls:
                        elevator.load(floor)
                        elevator.in_use = True
                        # print('elevator', elevator.elev_id, 'picks up passengers from floor', elevator.current_floor)
                        floor_diff = abs(called_floor - elevator.passengers[0].floor)
                        elevator.next_stop_time = t + bank.move_speed*floor_diff

                        if floor.floor in bank.call_list:
                            bank.call_list.remove(floor.floor)
                    
                    else:
                        elevator.last_time_used = t
                        elevator.next_stop_time = None

        # print('next elev stop:', bank.get_next_stop())
        # print('next down pass:', bank.floors[1].next_arrival_time)
        # print('next up pass:', bank.floors[0].next_arrival_time)
        prev_t = t

        if bank.get_next_stop() == None:
            t = min(bank.floors[0].next_arrival_time, 
            bank.floors[1].next_arrival_time)
        else:
            t = min(bank.floors[0].next_arrival_time, 
            bank.floors[1].next_arrival_time, bank.get_next_stop())
        
        non_completed_rides = []
        for floor in elevator.floors:
            non_completed_rides += floor.queue

        # if t == prev_t:
        #     break
    
    wait_sum = sum(passenger.departure_time - passenger.arrival_time 
    for passenger in completed_rides)
    
    return wait_sum/len(completed_rides)

def run_trials(num_elevators, num_floors, default_floors, default_reset_time, 
    move_speed, max_capacity, max_time, up_freq_expr, down_freq_expr, sigma, min_freq,
    num_trials):

    waits = 0
    
    for i in tqdm(range(num_trials)):
        waits += simulate_elevators(num_elevators, num_floors, default_floors, default_reset_time, 
        move_speed, max_capacity, max_time, up_freq_expr, down_freq_expr, min_freq, sigma)

    return waits/num_trials

import itertools
import click
from tqdm import tqdm

def compute_product_list(num_elevators, num_floors):
    rv = []
    for tup in itertools.product(range(num_floors), repeat = num_elevators):
        if tuple(reversed(tup)) not in rv:
            rv.append(tup)
    return rv

@click.command()
@click.option('--num-elevators', type = int, help = 'number of elevators in the bank')
@click.option('--num-floors', type = int, help = 'number of floors serviced')
@click.option('--default-reset-time', type = int, help = 'time before an elevator resets to a resting floor')
@click.option('--move-speed', type = int, help = 'time for elevator to move one floor')
@click.option('--max-capacity', default = 10, type = int, help = 'max capacity of an elevator')
@click.option('--max-time', type = int, help = 'maximum time for the simulation to run per trial (seconds)')
@click.option('--up-freq-expr', type = str, help = 'function for up call frequency')
@click.option('--down-freq-expr', type = str, help = 'function for down call frequency')
@click.option('--min-freq', type = int, help = 'the minimum frequency for elevator calls')
@click.option('--sigma', type = int, help = 'standard deviation for elevator call times')
@click.option('--num-trials', type = int, help = 'number of trials to complete per option')
@click.option('--compare-floors', default = None, type = tuple, help = '(optional) the default floors to compare to')

def cmd(num_elevators, num_floors, default_reset_time, 
    move_speed, max_capacity, max_time, up_freq_expr, down_freq_expr, min_freq, sigma,
    num_trials, compare_floors):
    
    wait_dict = {}

    for default_tuple in tqdm(compute_product_list(num_elevators, num_floors)):
        default_floors = list(default_tuple)

        wait_dict[default_tuple] = float(run_trials(num_elevators, num_floors, 
        default_floors, default_reset_time, move_speed, max_capacity, 
        max_time, up_freq_expr, down_freq_expr, min_freq, sigma, num_trials))
    
    best = min(wait_dict, key = wait_dict.get)
    
    print('Full wait dictionary:', wait_dict)
    print('Optimal default floors:', best)
    print('Average wait time:', wait_dict[best])
    if compare_floors != None:
        diff = wait_dict[best] - wait_dict[compare_floors]
        print('Optimal is better than entered floors by', diff, 't per ride')
    return best, wait_dict[best]

if __name__ == '__main__':
    cmd()
