from model import  Direction, State
      
class PaternosterController:
    def __init__(self):   
        pass
 
    def register_elevator_and_floors(self, elevator, floors):
        self._elevator = elevator
        self._elevator.listeners.append(self)
        self._floors = floors
        self._elevator_buttons = [False] * len(floors)
        for start_floor in self._floors:
            start_floor.listeners.append(self)

    def update(self):
        pass
        
    def elevator_state_change(self, old_state, new_state):
        if old_state == State.OPENING_DOORS:
            try: 
                probable_next_dest = self._get_preferred_destination(self._elevator.direction) #Raises exception if none found
                d_height = probable_next_dest.height_above_ground
                load_direction = Direction.between_points(self._elevator.height_above_ground, d_height)
                self._elevator.start_load_unload(load_direction)
            except: 
                #print("Found no preferred destination.")
                #self._elevator.start_load_unload(Direction.STILL)
                pass
            
        elif old_state == State.LOAD_UNLOAD:
            # We've finished loading and should decide where to go
            try:
                preferred_destination = self._get_preferred_destination(self._elevator.direction)
            except:
                # No preferred destination could be found;
                # nobody's waiting in the elevator or at any floor.
                #print "Just stay here and idle."
                return
            if self._elevator._current_floor == preferred_destination:
                self._elevator.start_load_unload(Direction.STILL)
            else:
                self._elevator.set_destination(preferred_destination)
            
            
                
         
    def elevator_load_unload(self, passengers):
        self._elevator_buttons = [False] * len(self._floors)
        for passenger in passengers:
            self._elevator_buttons[passenger.destination_index] = True
      
    
    def _get_preferred_destination(self, preferred_direction):
        # If there's no preferred direction, use up
        if preferred_direction == Direction.STILL:
            preferred_direction = Direction.UP
            
        try: return self._get_preferred_destination_exclusive(preferred_direction)
        except: return self._get_preferred_destination_exclusive(-preferred_direction)
    
    def _get_preferred_destination_exclusive(self, direction):
        dir_to_floor = lambda f: Direction.between_points(self._elevator.height_above_ground, f.height_above_ground)
        
        """TODO: Do we still need the Direction.STILL check? """
        relevant_floors = list(filter(lambda f: dir_to_floor(f) == direction or dir_to_floor(f) == Direction.STILL, self._floors))
        relevant_floors.sort(key = lambda f: f.height_above_ground * direction)
        
        # First check floor buttons in the elevator's direction, on floors in its direction
        # (up buttons on floor's above the elevator if Direction.UP)
        # Also check if anyone inside the elevator wants to go that way
        for floor in relevant_floors:
            i = floor.index
            if self._elevator_buttons[i] or (self._elevator.has_room_for_more() and floor.get_number_of_people_waiting(direction)):
                return floor
        # Then check if anyone's pressed a floor button in the other direction
        # (still floors in the elevator's direction)
        for floor in relevant_floors:
            if self._elevator.has_room_for_more() and floor.get_number_of_people_waiting(-direction):
                return floor
        
        # Raise exception if no floor was found
        raise Exception("No preferred destination found.")

    
    def elevator_arrival(self, destination):
        #print(time_str() + "ARRIVAL: " + str(destination))
        pass
        
    def floor_button_pressed(self, floor, direction):    
        elevator = self._elevator
        # Someone arrived at the floor where the elevator is currently idling
        if elevator.is_idle() and elevator.get_current_floor() == floor:
            # Just load that bastard regardless of where he/she's going
            elevator.start_load_unload(direction)
        # Someone arrived at a floor and the elevator is not busy (it's moving or turning)
        elif not self._elevator.is_busy():
            # Re-evaluates the current destination
            preferred_destination = self._get_preferred_destination(self._elevator.direction)
            if preferred_destination != self._elevator._current_floor:
                self._elevator.set_destination(preferred_destination)
            elif elevator.is_idle():
                self._elevator.start_load_unload(Direction.STILL)
                
        
        
    def floor_people_boarding(self, floor, direction):
        pass
    
    def elevator_halfway_between_floors(self, early_floor, late_floor):
        pass
    
    