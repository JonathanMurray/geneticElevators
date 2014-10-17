from model import  Direction, State
from random import random, randint
import sys
from pprint import pprint
from globals import NUMBER_OF_SITUATIONS      

class ChromosomeController:
    def __init__(self, chromosome):
        self.situation_string = []
        self.command_string = ""
        self.situation_index = -1
        self.situation_counter = [0] * NUMBER_OF_SITUATIONS
        
        self._chromosome = chromosome
        self._is_time_for_command = False
        
        
        
        
    def register_elevator_and_floors(self, elevator, floors):    
        self._elevator = elevator
        self._elevator.listeners.append(self)
        self._floors = floors
        for start_floor in self._floors:
            start_floor.listeners.append(self)
        self._elevator_buttons = [False] * len(floors)
        
        
        
        
        
        
        
                  
    def update_situation_index(self):
         
        travelling_forward = travelling_backward = 0
        waiting_ahead = waiting_behind = 0
        floors_ahead = self._get_relevant_floors(self._elevator.direction)
        floors_behind = self._get_relevant_floors(-self._elevator.direction)
        for floor in floors_ahead:
            if self._elevator_buttons[floor.index]:
                travelling_forward += 1
            waiting_ahead += floor.get_number_of_people_waiting(Direction.UP) + floor.get_number_of_people_waiting(Direction.DOWN)
        for floor in floors_behind:
            if self._elevator_buttons[floor.index]:
                travelling_backward += 1   
            waiting_behind += floor.get_number_of_people_waiting(Direction.UP) + floor.get_number_of_people_waiting(Direction.DOWN)
        
        if(waiting_ahead > waiting_behind):
            wait_index = 2
        elif waiting_ahead == waiting_behind:
            wait_index = 1
        else:
            wait_index = 0
        
        if (travelling_forward > travelling_backward):
            travel_index = 2
        elif travelling_forward == travelling_backward:
            travel_index = 1
        else:
            travel_index = 0
            
        proximity_index = 0  
        if(len(floors_ahead) > 0 and floors_ahead[0].get_number_of_people_waiting(Direction.UP) + 
             floors_ahead[0].get_number_of_people_waiting(Direction.DOWN) > 0):
            proximity_index += 0b1000
        if(len(floors_behind) > 0 and floors_behind[0].get_number_of_people_waiting(Direction.UP) + 
             floors_behind[0].get_number_of_people_waiting(Direction.DOWN) > 0):
            proximity_index += 0b0100
        if len(floors_ahead) > 0 and self._elevator_buttons[floors_ahead[0].index]:
            proximity_index += 0b0010
        if len(floors_behind) > 0 and self._elevator_buttons[floors_behind[0].index]:
            proximity_index += 0b0001
        
        if self._elevator.has_room_for_more():
            capacity_index = 1
        else:
            capacity_index = 0
            
        self.memorize_situation_string(wait_index, proximity_index, travel_index, capacity_index)
        self.situation_index = proximity_index * 18 + wait_index * 6 + travel_index * 2 + capacity_index 
        """
                                    16                  3                 3               2                 
        """   
        
        
        
    def memorize_situation_string(self, wait_index, proximity_index, travel_index, capacity_index):
        self.situation_string = []
        if wait_index == 2:
            self.situation_string += ["v", "v"]
        else:
            self.situation_string += ["", ""]
        if travel_index == 2:
            self.situation_string += ["^", "^"]
        else:
            self.situation_string += ["", ""]
          
        self.situation_string += [""]
        
        
        above_line = ""
        
        if proximity_index & 0b1000 == 0b1000:
            above_line += "v"
        else:
            above_line += " "
        if proximity_index & 0b0010 == 0b0010:
            above_line += "^"
        else:
            above_line += " "
        self.situation_string += [above_line]
                                
        if self._elevator.has_room_for_more():
            self.situation_string += ["[ ]"]            
        else:
            self.situation_string += ["[X]"]
        
        under_line = ""    
        if proximity_index & 0b0100 == 0b0100:
            under_line += "^"
        else:
            under_line += " "
            
        if proximity_index & 0b0001 == 0b0001:
            under_line += "v"
        else:
            under_line += " "
            
        self.situation_string += [under_line]
        
        self.situation_string += [""]
            
        if wait_index == 0:
            self.situation_string += ["^", "^"]
        else:
            self.situation_string += ["", ""]
        if travel_index == 0:
            self.situation_string += ["v", "v"]
        else:
            self.situation_string += ["", ""]
                
       
        
        
    def update(self):
        if self._is_time_for_command:
            self._do_some_command()
            self._is_time_for_command = False
        
            
            
    def _get_relevant_floors(self, direction):
        dir_to_floor = lambda f: Direction.between_points(self._elevator.height_above_ground, f.height_above_ground)
        relevant_floors = list(filter(lambda f: dir_to_floor(f) == direction, self._floors))
        relevant_floors.sort(key=lambda f: f.height_above_ground * direction)
        # print "relevant floors in direction:" + str(direction)
        # pprint(relevant_floors)
        return relevant_floors
        

        
    def elevator_state_change(self, old_state, new_state):
        if old_state == State.OPENING_DOORS:
            try: 
                self._elevator.start_load_unload(Direction.STILL)
            except: 
                pass
        if old_state == State.LOAD_UNLOAD:
            self._is_time_for_command = True
            
        self.situation_memorized = self.update_situation_index()
      
                       
    def elevator_load_unload(self, passengers):
        self._elevator_buttons = [False] * len(self._floors)
        for passenger in passengers:
            self._elevator_buttons[passenger.destination_index] = True

    
    def elevator_arrival(self, destination):
        pass
        
    def floor_button_pressed(self, floor, direction):    
        elevator = self._elevator
        # Someone arrived at the floor where the elevator is currently idling
        if elevator.is_idle() and elevator.has_room_for_more() and elevator.get_current_floor() == floor:
            # Just load that bastard regardless of where he/she's going
            elevator.start_load_unload(direction)
        # Someone arrived at a floor and the elevator is not busy (it's moving or turning)
        elif not self._elevator.is_busy():
            # Re-evaluates the current destination
            self._is_time_for_command = True
        
        
    def floor_people_boarding(self, floor, direction):
        pass
    
    def elevator_halfway_between_floors(self, early_floor, late_floor):
        self._is_time_for_command = True
    
    
    def _do_some_command(self):
        self.update_situation_index()     
        self.situation_counter[self.situation_index] += 1
            
        # print "Situation index: " + str(self.situation_index)
        if self._chromosome == None:
            print "Chromosome == None"
            sys.exit()
        try:
            command = self._chromosome[self.situation_index]
        except Exception as e:
            print str(e) + "   index=" + str(self.situation_index)
#        print "Command: " + str(command)
        try:
            if command == 0:
                # print "Controller: stop" 
                self.command_string = "Stop at next"
                self._command_stop_at_next()
            elif command == 1:
                self._command_go_forward()
                self.command_string = "Go forward"
            else:
                if not (self._elevator._state == State.MOVING and not self._elevator.is_empty()):
                    self._command_turn_around() 
                    self.command_string = "Turn around"
                else:
                    self._command_go_forward()
                    self.command_string = "Go forward (wanted to turn around)"
        except Exception as e:
            print "COMMAND " + str(command) + " FAILED  in _do_some_command: " + str(e)
            pass
            
            
    
    def _command_stop_at_next(self):
        if self._elevator._state == State.MOVING:
            self._elevator.stop_at_next_floor()
        elif self._elevator._current_floor != None:
            try: 
                next_floor = self._floors[self._elevator._current_floor.index + self._elevator.direction]
                if not self._elevator.is_busy():
                    self._elevator.set_destination(next_floor)
            except Exception: 
                # print "ERROR in _command_stop_at_next: " + str(e)
                pass
                """ Next floor not found. Already at top/bottom floor. """
        
    def _command_go_forward(self):
        self._goto_most_distant(self._elevator.direction)
        
    def _command_turn_around(self):
        self._goto_most_distant(-self._elevator.direction)
        
    def _goto_most_distant(self, direction):
        if direction == Direction.DOWN:
            destination = self._floors[0]
        else:
            destination = self._floors[len(self._floors) - 1]
            
#        print "in _goto_most_diostant:  destination = " + str(destination)
        if self._elevator._current_floor != destination and not self._elevator.is_busy():
            self._elevator.set_destination(destination)
        else:
            # print "Already at top/bottom floor. Can't go further..."
            pass
        
        
    
    
    def __str__(self):
        return "Controller: " + str(self._chromosome)
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
