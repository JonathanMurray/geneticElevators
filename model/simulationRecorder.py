from model import Direction 
from pprint import pprint
 
   
class SimulationRecorder:
    
    def __init__(self):
        self.recorded_passengers = []
        self.max_wait_time = 0
        self.max_system_time = 0
        self.max_travel_time = 0
        self.fraction_served = 0
        self.total_number_of_people = 0
        
    def record_passenger(self, person):
        self.recorded_passengers.append(person)
        #print "SimulationRecorder: received passenger. Now length = " + str(len(self.recorded_passengers))
    
    def notify_end_of_simulation(self, floors, elevator):
        served_and_unserved_passengers = self.recorded_passengers[:]
        
        for floor in floors:
            served_and_unserved_passengers += floor._people_waiting[Direction.UP] + floor._people_waiting[Direction.DOWN]
        served_and_unserved_passengers += elevator._passengers
        
        self.NUM_ELEVATOR = len(elevator._passengers)
        self.NUM_FLOORS = 0
        for floor in floors:
            self.NUM_FLOORS += len(floor._people_waiting[Direction.UP] + floor._people_waiting[Direction.UP])
            
        self.total_number_of_people = len(served_and_unserved_passengers)
        if len(served_and_unserved_passengers) > 0:
            self.fraction_served = (float(len(self.recorded_passengers)) / float(len(served_and_unserved_passengers)))
        else:
            self.fraction_served = 0
        
        times = [(p.waited_time,p.travelled_time) for p in served_and_unserved_passengers]
        if len(times) > 0:
            self.max_wait_time = max(times, key=lambda t: t[0])[0]
            self.max_travel_time = max(times, key=lambda t: t[1])[1]
            m = max(times, key=lambda t: t[0]+t[1])
            self.max_system_time = m[0]+m[1]
            
        #self.print_nice_data() #TODO
            
    def __str__(self):
        return "total ppl: " + str(self.total_number_of_people) + " rec: " + str(len(self.recorded_passengers)) + ". floors: " + str(self.NUM_FLOORS) + ". elev: "+ str(self.NUM_ELEVATOR) + "."
    
        
    def print_data(self):
        pprint(self.recorded_passengers)
    
    def get_served_wait_times(self):
        times = []
        for p in self.recorded_passengers:
            times.append(p.waited_time)
        return times
        
    def get_served_travel_times(self):
        times = []
        for p in self.recorded_passengers:
            times.append(p.travelled_time)
        return times

    def get_served_total_times(self):
        times = []
        for p in self.recorded_passengers:
            times.append(p.waited_time + p.travelled_time)
        return times
    
    def print_nice_data(self):
        print("\n\n-- Served "+str(len(self.recorded_passengers))+" passengers. (" + str(self.fraction_served) + "%)")

        wait = self.get_served_wait_times()
        travel = self.get_served_travel_times()
        total = self.get_served_total_times()
        
        print"\n-- Wait times"
        print "Max:\t" + str(self.max_wait_time) +" s."
        print "Min:\t" +str(min(wait))+" s."
        print "Avg:\t"+str(sum(wait)/float(len(wait)))+" s."
        print "Avg squared:\t"+str(sum([w*w for w in wait])/float(len(wait)))+" s."
        
        print"\n-- Travel times"
        print "Max:\t" + str(self.max_travel_time) +" s."
        print "Min:\t" +str(min(travel))+" s."
        print "Avg:\t"+str(sum(travel)/float(len(travel)))+" s."
        print "Avg squared:\t"+str(sum([t*t for t in travel])/float(len(travel)))+" s."
        
        print"\n-- Total times"
        print "Max:\t" + str(self.max_system_time) +" s."
        print "Min:\t" +str(min(total))+" s."
        print "Avg:\t"+str(sum(total)/float(len(total)))+" s."
    
  