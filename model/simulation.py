
from visualization import init_visualization, draw
import time, pprint
import pygame.locals
from simulationRecorder import SimulationRecorder
from model import Elevator


class DebugModelListener:
    def __init__(self, elevator, floors):
        elevator.listeners.append(self)
        for start_floor in floors:
            start_floor.listeners.append(self)
            
    def floor_button_pressed(self, floor, direction):
        print("\t\t\t\t\t\t\t\tReceived button " + str(direction) + " (floor" + str(floor.index) + ")")
    
    def floor_people_boarding(self, floor, direction):
        pass
        
    def elevator_state_change(self, old_state, new_state):
        print("      State change: " + old_state + " -> " + new_state)
            
                 
    def elevator_load_unload(self, passengers):
        print("Passengers on elevator: " + str(len(passengers)))
        pprint.pprint(passengers)
    
    def elevator_arrival(self, destination):
        # print(time_str() + "ARRIVAL: " + str(destination))
        pass
    
    def elevator_halfway_between_floors(self, early_floor, late_floor):
        print("Elevator just passed halfway between " + str(early_floor) + " and " + str(late_floor))
        


def event_from_visualization(event):
    """ Reacts to keypresses from visualization. Adjusts sleep time 
           Since sleep_seconds is global, its not possible to have several 
           graphical simulations running at different speeds.
    """
    global sleep_seconds
    if event.type == pygame.locals.KEYDOWN:
        if event.key == pygame.locals.K_DOWN:
            if sleep_seconds < 0.01:
                sleep_seconds += 0.005
            elif sleep_seconds < 0.05:
                sleep_seconds += 0.01
            elif sleep_seconds < 0.2:
                sleep_seconds += 0.05
            elif sleep_seconds < 1:
                sleep_seconds += 0.1
        elif event.key == pygame.locals.K_UP:
            if sleep_seconds > 1:
                sleep_seconds -= 0.1
            elif sleep_seconds > 0.2:
                sleep_seconds -= 0.05
            elif sleep_seconds > 0.05:
                sleep_seconds -= 0.01
            elif sleep_seconds > 0.005:
                sleep_seconds -= 0.005
            else:
                sleep_seconds = 0
 
def run_simulation(elevator_controller, floors, start_floor_index=0,
                   _sleep_seconds=0, number_of_steps= -1, visualization=True, debug=False,
                   speed=3, capacity=10,
                   print_results=True, _chromosome_controller=False):
    
    """ Runs a simulation on elevator/floors with given controller.
        Returns a simulation_recorder object that has data about the simulation
    """
    
    global sleep_seconds
    sleep_seconds = _sleep_seconds
    simulation_recorder = SimulationRecorder()
    elevator = Elevator(floors[start_floor_index], floors, speed, capacity)
    elevator.set_recorder(simulation_recorder)
    elevator_controller.register_elevator_and_floors(elevator, floors)
    
    if debug:
        DebugModelListener(elevator, floors)
    if visualization:
        init_visualization(elevator, floors, elevator_controller, _event_callback=event_from_visualization, _chromosome_controller=_chromosome_controller)
       
        
    i = 0
    while True:
        update_model_and_controller(elevator, floors, elevator_controller)
        time.sleep(sleep_seconds)
        if visualization:
            if not draw():
                break
        if number_of_steps != -1 and i >= number_of_steps:
            break
        i += 1
    
    simulation_recorder.notify_end_of_simulation(floors, elevator)
    if print_results:
        try:
            simulation_recorder.print_nice_data();
        except _:
            pass
        
    return simulation_recorder
    
        
        
    
    
    
    
def update_model_and_controller(elevator, floors, controller):

    elevator.update()   
    for floor in floors:
        floor.update()
    controller.update()

    
    
    
    

    
    
