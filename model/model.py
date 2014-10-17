from pprint import pprint
import sys



TIME_STEP = 0.1

def sign(a):
    if(a < 0): return -1
    elif(a == 0): return 0
    else: return 1

def same_sign(a, b):
    return (a >= 0 and b >= 0) or (a <= 0 and b <= 0)



    
class Direction:
    UP = 1
    STILL = 0
    DOWN = -1
    
    @staticmethod
    def between_points(start, end):
        if(start < end):
            return Direction.UP
        elif(end < start):
            return Direction.DOWN
        else:
            return Direction.STILL
    
    @staticmethod
    def between_floors(f1, f2):
        return Direction.between_points(f1.height_above_ground, f2.height_above_ground)
        
        
    @staticmethod
    def from_velocity(upspeed):
        if upspeed > 0:
            return Direction.UP
        elif upspeed < 0:
            return Direction.DOWN
        else:
            return Direction.STILL
       


"""------------------------------   STATE   ------------------------------------------"""

class State:
    MOVING = "moving"
    STOPPING = "stopping"
    OPENING_DOORS = "opening"
    LOAD_UNLOAD = "loading/unloading"
    IDLE = "idle"
    CLOSING_DOORS = "closing"
    STARTING = "starting"
    TURNING = "turning"

busy_states = [State.STOPPING, State.CLOSING_DOORS, State.LOAD_UNLOAD, State.OPENING_DOORS, State.STARTING]
    
state_transitions = {
    State.STOPPING:         State.OPENING_DOORS,
    State.OPENING_DOORS:    State.IDLE,
    State.LOAD_UNLOAD:      State.IDLE,
    State.CLOSING_DOORS:    State.STARTING,
    State.STARTING:         State.MOVING,
    State.TURNING:          State.MOVING
}

state_durations = { 
    State.STOPPING: 1.8,
    State.CLOSING_DOORS: 1.8,
    State.OPENING_DOORS: 1.8,
    State.STARTING: 1.8,
    State.TURNING: 1,
    State.LOAD_UNLOAD: None,
}

BOARDING_TIME = 1
EXIT_TIME = 1


"""------------------------------   ELEVATOR   ------------------------------------------"""

class Elevator:
    def __init__(self, start_floor, floors, speed, capacity):
        self.listeners = []
        self.direction = Direction.UP
        self.height_above_ground = start_floor.height_above_ground
        
        self.DEBUG_STRING = ""
        
        self._state = State.IDLE
        self._load_direction = Direction.STILL
        self._state_countdown = 0
        self._velocity = 0
        self._speed = speed #Positive constant, thats used to set velocity
        self._floors = floors
        self._current_floor = start_floor
        self._previous_floor = self._current_floor
        self._has_notified_halfway = False
        self._destination = None
        self._passengers = [] 
        self._capacity = capacity
        self._recorder = None
        
    def set_recorder(self, recorder):
        self._recorder = recorder
        if len(recorder.recorded_passengers) != 0:
            print "I RECEIVED NON EMPTY DATALISTENER!! BNOHOHOHO"
            sys.exit()
        

    def update(self):
        for person in self._passengers:
            person.update()
        
        self._state_countdown -= TIME_STEP
        if(self._state == State.MOVING):
            self._handle_halfway_to_next_floor()
            self._handle_passed_floor()
            if(self._is_close_to_arrival()):
                self._enter_state(State.STOPPING)
                return
            self.height_above_ground += self._velocity * TIME_STEP          
        elif(self._state in state_durations and self._state_countdown <= 0):
            self._enter_state(state_transitions[self._state])
            
    def _handle_passed_floor(self):
        if self._destination != None:
            try:
                next_floor = self._floors[self._previous_floor.index + self.direction]
            except Exception as e:
                print str(e) + "     index  = " + str(self._previous_floor.index+self.direction)
                print "prevfloor = " + str(self._previous_floor.index)
                print "direction = " + str(self.direction)
                print "destination = " + str(self._destination)
                print "State = " + str(self._state)
                print self.DEBUG_STRING
                sys.exit()
            
            went_past_next_floor = (self.direction*self.height_above_ground > 
                                    self.direction*next_floor.height_above_ground)
            if went_past_next_floor:
                self.DEBUG_STRING +=  "Elevator: Went past next floor, so I set previousfloor = " + str(next_floor) + "\n"
                self._previous_floor = next_floor
                self._has_notified_halfway = False
                
            
    def _handle_halfway_to_next_floor(self):
        if self._has_notified_halfway:
            return
        if self._destination != None:
            if self._destination.height_above_ground != self._previous_floor.height_above_ground:
                try:
                    next_floor = self._floors[self._previous_floor.index + self.direction]
                except Exception as e:
                    print e
                    print "prevfloor: " + str(self._previous_floor.index) + " direction: " + str(self.direction) + " destination: " + str(self._destination.index) + " state: " + self._state + " height above ground: " + str(self.height_above_ground)
                midpoint = (self._previous_floor.height_above_ground + next_floor.height_above_ground)/2
                halfway = self.direction*self.height_above_ground > self.direction*midpoint
                if halfway:
#                    print "Elevator state: " + str(self._state) + " ... notifying Halfway."
                    for listener in self.listeners:
                        listener.elevator_halfway_between_floors(self._previous_floor, next_floor)
                    self._has_notified_halfway = True
                
        
    def _is_close_to_arrival(self):
        move = self._velocity * TIME_STEP
        pos = self.height_above_ground
        d = self._destination.height_above_ground
        return not same_sign(pos + move - d, pos - d) or (pos + move == d)
    
    def set_destination(self, destination):
        if(self._state in busy_states):
            raise Exception("Cannot set _destination in state: " + str(self._state))
        if(destination == None):
            raise Exception("Cannot set destination = None")
        if self._current_floor != None and destination == self._current_floor:
            raise Exception("Cannot set destination = current floor (" + str(self._current_floor.index)+"), prev = "+str(self._previous_floor.index) + " Direction=" + str(self.direction))
        
        self._destination = destination
        old_direction = self.direction
        self.direction = Direction.between_points(self.height_above_ground, self._destination.height_above_ground)
        
        
        
        """ Example when this happens:
            1. Elevator is idle at floor0
            2. Destination is set to floor9
            3. Elevator enters MOVING but hasn't actually moved yet (height_above_ground is == floor0.height_above_ground)
            4. Destination is set to floor0
            5. Direction.between_points gives Direction.STILL
            
            That can't be allowed, since we will then enter TURNING and let previous_floor keep its old value.
            If destination is then set to floor9, direction will be 1 and previous_floor will be set to floors[0 - 1] (floor9)
            If direction is corrected to be Direction.DOWN after step5, and previous_floor to be 1, everything will be fine.    
        """
        if self.direction == Direction.STILL:
            self.direction = - old_direction
            
            
            
        if(self._state == State.IDLE):
            # if direction has changed, that's not a problem since previous_floor was set when elevator arrived here!
            self._enter_state(State.CLOSING_DOORS)
            
        elif(self.direction != old_direction):
            self.DEBUG_STRING +=  "elevator: enter state TURNING since: dir=" + str(self.direction) + "   dest=" + str(self._destination) + "height: " + str(self.height_above_ground) + "\n"
            self._enter_state(State.TURNING)
        
    def stop_at_next_floor(self):
        if self._state != State.MOVING:
            raise Exception("Can only stop at next floor, if in moving state")
        if self.direction == Direction.STILL:
            raise Exception("Cant stop at next floor when direction == Still")
        
        next_floor = self._floors[self._previous_floor.index + self.direction]
        self.set_destination(next_floor)
        #print "Elevator: will stop at " + str(next_floor) + " previous_floor = " + str(self._previous_floor)
        
       
    def _arrive_at_floor(self, destination):
        self.DEBUG_STRING += "prevfloor = " + str(self._previous_floor) + " and now arrive at floor " + str(destination.index)  + "\n"
        self._current_floor = self._destination
        self._destination = None
        self._velocity = 0
        self.height_above_ground = self._current_floor.height_above_ground
        for listener in self.listeners:
            listener.elevator_arrival(destination)
        self._previous_floor = destination
        self._has_notified_halfway = False
      
    def get_current_floor(self):
        if self._current_floor == None:
            raise Exception("current floor == None")
        return self._current_floor
         
    def is_idle(self):
        return self._state == State.IDLE
 
    def is_busy(self):
        return self._state in busy_states
    
    def has_room_for_more(self):
        return len(self._passengers) < self._capacity
    
    def is_empty(self):
        return len(self._passengers) == 0
     
    def start_load_unload(self, load_direction):
        if self._state != State.IDLE:
            raise Exception("State:" + self._state + ". Has to be idle to load/unload");
        self._load_direction = load_direction
        self._enter_state(State.LOAD_UNLOAD)
        
    def _enter_state(self, state): 
        self.DEBUG_STRING += "enter state " + state + "   height: " + str(self.height_above_ground) + "\n"
        old_state = self._state
        self._state = state  # Important to actually change state before notifying listeners!
        for listener in self.listeners:
            try:
                listener.elevator_state_change(old_state, self._state)
            except Exception as e:
                print "listener.elevator_state_change failed: " + str(e)
                sys.exit()
       
        if(state in state_durations):
            self._state_countdown = state_durations[state]
            
        if(state == State.MOVING):
            self._current_floor = None 
            self._velocity = self._speed * Direction.between_points(self.height_above_ground, self._destination.height_above_ground)        
        elif(state == State.STOPPING):
            self._arrive_at_floor(self._destination) 
        elif(state == State.TURNING):
            #print "Changed previousfloor from " + str(self._previous_floor) + " to " + str(self._floors[self._previous_floor.index - self.direction]) + " due to turning-state"
            self._previous_floor = self._floors[self._previous_floor.index - self.direction]
            self._has_notified_halfway = False
           
        elif(state == State.LOAD_UNLOAD):
            exiting_passengers = list(filter(lambda p: p.destination_index == self._current_floor.index, self._passengers))
            
            try:
                boarding_passengers = self._load(len(exiting_passengers))
            except Exception as e:
                print "boarding_passengers failed: "+ str(e)
                
            self._state_countdown = self._get_load_unload_countdown(exiting_passengers, boarding_passengers)
            self._unload(exiting_passengers)
            for listener in self.listeners:
                listener.elevator_load_unload(self._passengers[:])
        
    def _load(self, number_of_exiting_passengers):
        floor = self._current_floor
        boarding_passengers = floor.pop_people_waiting(self._load_direction, self._capacity - len(self._passengers) + number_of_exiting_passengers)
        for person in boarding_passengers:
            person.board_elevator()
            self._passengers.append(person)
        return boarding_passengers
            
    def _unload(self, exiting_passengers):
        for person in exiting_passengers:
            person.travelled_time += self._state_countdown / 2
            self._passengers.remove(person)
            self._recorder.record_passenger(person)
    
    def _get_load_unload_countdown(self, exiting_passengers, boarding_passengers):
        return len(exiting_passengers) * EXIT_TIME + len(boarding_passengers) * BOARDING_TIME
           
    def __str__(self):
        return "[State:" + self._state + ", Height:" + str(self.height_above_ground) + ", Floor:" + str(self._current_floor) + "]"







"""------------------------------   PERSON   ------------------------------------------"""    
        
class Person:
    def __init__(self, start_index, destination_index):
        self.start = start_index
        self.destination_index = destination_index
        self.waited_time = 0
        self.has_boarded = False
        self.travelled_time = 0
            
    def update(self):
        if(self.has_boarded):
            self.travelled_time += TIME_STEP
        else:
            self.waited_time += TIME_STEP
        
    def board_elevator(self):
        self.has_boarded = True
        self.travelled_time = 0

    def __str__(self):
        return "From " + str(self.start) + " to " + str(self.destination_index) + ". Wait:" + str(self.waited_time) + ", travel:" + str(self.travelled_time)
    
    def __repr__(self):
        return "From " + str(self.start) + " to " + str(self.destination_index) + ". Wait:" + str(self.waited_time) + ", travel:" + str(self.travelled_time)


"""------------------------------   FLOOR   ------------------------------------------"""    

class Floor:
    def __init__(self, index, height_above_ground, people_distribution):
        self.index = index
        self.height_above_ground = height_above_ground
        self._people_distribution = people_distribution
        self._people_waiting = {
                                Direction.DOWN: [],
                                Direction.UP: [],
                             }
        self.listeners = []
    
    def update(self):
        new_people = self._people_distribution.get_new_people()
            
        for person in new_people:
            
            self._handle_new_person(person)
        for key in self._people_waiting:
            for person in self._people_waiting[key]:
                person.update()
            
    def _handle_new_person(self, person):
        direction = Direction.between_points(self.index, person.destination_index)        
        self._people_waiting[direction].append(person)
        #print "FLOOR: Arrived new person. now length = " + str(len(self._people_waiting[direction]))
        if len(self._people_waiting[direction]) == 1:
            self._notify_button_pressed(direction)
            
    def get_number_of_people_waiting(self, direction):
        return len(self._people_waiting[direction])
        
    def _notify_button_pressed(self, direction):
        for listener in self.listeners:
            listener.floor_button_pressed(self, direction)
            
    def pop_people_waiting(self, boarding_direction, max_number_of_boarders):
        """ Giving boarding_direction == STILL is OK, and simply lets everyone aboard, no matter where they are going.
        """
        try:
            # Pops up to maximum number of boarders
            boarding_passengers = self._people_waiting[boarding_direction][:max_number_of_boarders] # Raises exception if direction == Direction.STILL
            # Removes the boarders from people waiting
            self._people_waiting[boarding_direction] = self._people_waiting[boarding_direction][max_number_of_boarders:]
        except:
            # Direction.STILL: pop one person from each direction until you've hit max
            # or run out of waiting people.
            boarding_passengers = []
            board_dir = Direction.UP
            while len(boarding_passengers) < max_number_of_boarders:
                if len(self._people_waiting[board_dir]) > 0:
                    boarding_passengers.append(self._people_waiting[board_dir].pop(0))
                
                if(len(self._people_waiting[board_dir]) == 0 and len(self._people_waiting[-board_dir]) == 0):
                    break
                
                board_dir *= -1            

        self._notify_people_boarding(boarding_direction)
        return boarding_passengers
    
    def _notify_people_boarding(self, direction):
        for listener in self.listeners:
            listener.floor_people_boarding(self, direction)
       
    def __str__(self):
        return str(self.index) + " [" + str(len(self._people_waiting[Direction.UP] + self._people_waiting[Direction.DOWN])) + "ppl]   [dist: " + str(self._people_distribution) + "]"
