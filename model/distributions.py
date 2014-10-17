import random
from model import Person, TIME_STEP

class DownwardDistribution:
    def __init__(self, floor_index, number_of_floors, arrival_probability=0.012, down_probability=1):
        self._floor_index = floor_index
        self._other_nonzero = []
        self._arrival_probability = arrival_probability
        self._down_probability = down_probability
        for i in range(number_of_floors):
            if i > 0 and i != floor_index:
                self._other_nonzero.append(i)
                
    def get_new_people(self):
        if random.random() < self._arrival_probability * TIME_STEP: 
            if random.random() < self._down_probability:
                # Going down
                return [Person(self._floor_index, 0)]
            else:
                # Going up instead
                random_index = self._other_nonzero[random.randint(0, len(self._other_nonzero) - 1)]
                return [Person(self._floor_index, random_index)]
        else:
            return []
        
    def __str__(self):
        return "DownwardDistribution"
        
        
        
class UpwardDistribution:
    def __init__(self, number_of_floors, arrival_probability=0.012):
        self._number_of_floors = number_of_floors
        self._arrival_probability = arrival_probability
    def get_new_people(self):
        if random.random() < self._arrival_probability * TIME_STEP:
            return [Person(0, random.randint(2, self._number_of_floors) - 1)]
        else:
            return []
        
    def __str__(self):
        return "UpwardDistribution"
        
        
        
class CachedDistribution:
    def __init__(self, distribution, number_of_steps):
        self._arrival_steps = []
        self._arrivals = []
        self._num_arrivals_this_far = 0
        self._step = 0
        self._prepare_distribution(distribution, number_of_steps)
        
                
    def _prepare_distribution(self, distribution, number_of_steps):
        new_people_tmp = []
        for i in range(number_of_steps):
            new_people_tmp.append(distribution.get_new_people())
            if len(new_people_tmp[len(new_people_tmp) - 1]) > 0:
                self._arrival_steps.append(i)
                self._arrivals.append(new_people_tmp[len(new_people_tmp) - 1])
        
        
    def get_new_people(self):
        if self._step in self._arrival_steps:
            self._step += 1
            self._num_arrivals_this_far += 1
            # print "STEP " + str(self._step) + "  arrived new person"
            return self._arrivals[self._num_arrivals_this_far - 1]
        else:
            self._step += 1
            return []
       
    def reset(self):
        self._step = 0
        self._num_arrivals_this_far = 0
            
    def __str__(self):
        return "Cached[" + str(len(self._arrival_steps)) + "]"
        
        
        
