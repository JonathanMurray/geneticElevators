from model import Floor
from distributions import DownwardDistribution, UpwardDistribution, CachedDistribution

class StandardScenario:
    name = "StandardScenario"
    def __init__(self, number_of_steps, number_of_floors):
        self.floors = [Floor(0, 0, CachedDistribution(UpwardDistribution(number_of_floors, arrival_probability=0.008), number_of_steps))]
        for i in range(number_of_floors - 1):
            self.floors.append(Floor(i + 1, (i + 1) * 4, CachedDistribution(DownwardDistribution(i + 1, number_of_floors, arrival_probability=0.008, down_probability=0.75), number_of_steps)))
        self.number_of_steps = number_of_steps

class MorningRushScenario:
    """
    A lot of traffic on bottom floor going up, very little on others.
    
    """    
    name = "MorningRushScenario"
    def __init__(self, number_of_steps, number_of_floors):
        self.number_of_steps = number_of_steps
        self.floors = [Floor(0, 0, CachedDistribution(UpwardDistribution(number_of_floors, arrival_probability=0.08), number_of_steps))]
        for i in range(number_of_floors - 1):
            self.floors.append(Floor(i + 1, (i + 1) * 4, CachedDistribution(DownwardDistribution(i + 1, number_of_floors, arrival_probability=0.001), number_of_steps)))
        
class EveningRushScenario:
    """
    A lot of traffic going down from all floors, very little up
    
    """
    name = "EveningRushScenario"
    def __init__(self, number_of_steps, number_of_floors):
        self.number_of_steps = number_of_steps
        self.floors = [Floor(0, 0, CachedDistribution(UpwardDistribution(number_of_floors, arrival_probability=0.000), number_of_steps))]
        for i in range(number_of_floors - 1):
            self.floors.append(Floor(i + 1, (i + 1) * 4, CachedDistribution(DownwardDistribution(i + 1, number_of_floors, arrival_probability=0.015), number_of_steps)))
            
class EndOfTheWorldScenario:
    """
    Everyone's going everywhere EN MASSE!!!!!!!!!!!!!!
    
    """
    name = "EndOfTheWorldScenario"
    def __init__(self, number_of_steps, number_of_floors):
        self.number_of_steps = number_of_steps
        self.floors = [Floor(0, 0, CachedDistribution(UpwardDistribution(number_of_floors, arrival_probability=0.03), number_of_steps))]
        for i in range(number_of_floors - 1):
            self.floors.append(Floor(i + 1, (i + 1) * 4, CachedDistribution(DownwardDistribution(i + 1, number_of_floors, arrival_probability=0.03, down_probability=0.5), number_of_steps)))
            
            
            
            
            