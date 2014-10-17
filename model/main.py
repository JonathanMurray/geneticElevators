from model import Floor, Elevator, Direction
from chromosomeController import ChromosomeController
from paternosterController import PaternosterController
from distributions import UpwardDistribution, DownwardDistribution, CachedDistribution
from simulation import run_simulation
import random
from pprint import pprint
from math import pow, sqrt
from multiprocessing import Process, Queue
from scenario_factory import StandardScenario, MorningRushScenario, EveningRushScenario, EndOfTheWorldScenario
import copy
import sys
import time
from globals import *

situation_counter = [0]*NUMBER_OF_SITUATIONS
MUTATION_RATE = 1/float(10)
highest_fitness = 0
best_chromosome = None
current_visualization_process = None
startTimeStr = str(time.asctime(time.localtime(time.time())))


class StagedScenario:
    def __init__(self, scenario):
        self.name = scenario.name
        self.floors = scenario.floors
        self.number_of_steps = scenario.number_of_steps
        
    def evaluate_controller(self, controller, sleep_seconds=0, graphics=True, debug=False, print_results=False, _chromosome_controller=False):
        """ Changes the state of the scenario.
            To use the same scenario for several controllers, make deepcopies of it.
        """
        recorder = run_simulation(controller, self.floors, _sleep_seconds=sleep_seconds,
                       number_of_steps=self.number_of_steps, visualization=graphics, print_results=print_results, debug=debug,
                       _chromosome_controller=_chromosome_controller)
        fitness = get_recorder_fitness(recorder)
        return fitness
        

def evaluate_paternoster(_scenario, sleep=0, graphics=False, debug=False, print_results=False):
    scenario = copy.deepcopy(_scenario)
    elevator_controller = PaternosterController()
    return scenario.evaluate_controller(elevator_controller, graphics=graphics, debug=debug, print_results=print_results)


def evaluate_chromosome(chromosome, _scenario, queue, graphics=False, sleep=0, debug=False, print_results=False):
    elevator_controller = ChromosomeController(chromosome)
    scenario = copy.deepcopy(_scenario)
    result = scenario.evaluate_controller(elevator_controller, graphics=graphics, debug=debug, sleep_seconds=sleep, _chromosome_controller=True, print_results=print_results)
    if(queue == None):
        return result
    else:
        queue.put((chromosome, result))
        
def evaluate_chromosome_versatile(chromosome, _scenarios, queue, graphics=False, sleep=0, debug=False, print_results=False):
    """
    Evaluates a chromosome in all different scenarios in _scenarios (list)
    and returns/queues a list/tuple looking like this:
        [result1, result2, ..., resultn]
    or
        (chromosome, result1, result2, ..., resultn)
    
    """
    elevator_controller = ChromosomeController(chromosome)
    scenarios = copy.deepcopy(_scenarios)
    results = {"situation_counter":[0]*NUMBER_OF_SITUATIONS}
    scenario_number = 1
    for scenario in scenarios:
        results[scenario.name + str(scenario_number)] = (scenario.evaluate_controller(elevator_controller, graphics=graphics, debug=debug, sleep_seconds=sleep, _chromosome_controller=True, print_results=print_results))
        scenario_number +=1
        for i in range(len(situation_counter)):
            results["situation_counter"][i] += elevator_controller.situation_counter[i]

    
    results["chromosome"] = chromosome
    
    results["combined"] = 0
    for i in range(len(_scenarios)-2):
        results["combined"] += results[EveningRushScenario.name + str(i+1)]
    results["combined"] += results[EveningRushScenario.name + str(len(_scenarios))]/3 + results[EveningRushScenario.name + str(len(_scenarios)-1)]/3  #Last one has 1/3 weight
    queue.put(results)



def get_recorder_fitness(simulation_recorder):
    wait_times = simulation_recorder.get_served_wait_times()
    travel_times = simulation_recorder.get_served_travel_times()
    fraction_served = simulation_recorder.fraction_served
    number_served = len(simulation_recorder.get_served_total_times())
    if fraction_served == 0:
        return 0
    elif fraction_served < 0.5:
        return fraction_served / 10000000
    else:
        fitness = (1000000*pow(fraction_served,5) / 
                    (avg([pow(t, 2) for t in wait_times] + [pow(t, 2) for t in travel_times]) * 
                    simulation_recorder.max_system_time))
        return fitness
    
    
     
        
def avg(v):
    if len(v) == 0:
        return 0
    return float(sum(v)) / float(len(v))

def crossover(parent1, parent2):
    breakpoint = random.randint(0, len(parent1) - 1)
    if random.random() < 0.5:
        parent1, parent2 = parent2, parent1
    child = parent1[:breakpoint] + parent2[breakpoint:]
  
    return child


def crossover2(parent1, parent2):
    
    num_breakpoints = 5
    breakpoints = []
    parents = [parent1, parent2]
    parent_i = random.randint(0, 1) 
    for i in range(num_breakpoints):
        breakpoints.append(random.randint(1, len(parent1) - 1))
    breakpoints.sort()
    
    child = parents[parent_i][:breakpoints[0]]
    
    parent_i = (parent_i + 1) % 2
    for i in range(num_breakpoints - 1):
        child += parents[parent_i][breakpoints[i]:breakpoints[i + 1]]
        parent_i = (parent_i + 1) % 2
    child += parents[parent_i][breakpoints[len(breakpoints) - 1]:]
   
    return child


def print_winner_results(r):
    print "=== Winner ==="
    print "Chromosome:", r["chromosome"]
    print "Combined fitness: ", r["combined"]

def next_generation(population, scenarios, generation_number, display_winner=False, log_file=None):
    global best_chromosome
    global highest_fitness
    global situation_counter
    
    
    #Replace one of the scenarios with a new randomized one
    scenarios[-1] = StagedScenario(EveningRushScenario(13000, 10))
    scenarios[-2] = StagedScenario(EveningRushScenario(13000, 10))
    
    queue = Queue()
    
    for organism in population:
        process = Process(target=evaluate_chromosome_versatile, args=(organism, scenarios, queue))
        process.daemon = True
        process.start()
    
    results = [queue.get() for organism in population] 
    # Sort by SUM OF ALL RESULTS, that is "combined"
    results.sort(key=lambda result: result["combined"])
    
    generation_situation_counter = [0]*NUMBER_OF_SITUATIONS
    for result in results:    
        for i in range(len(generation_situation_counter)):
            generation_situation_counter[i] += result["situation_counter"][i]
            
    print "Counter: ", generation_situation_counter
    counter_log = open("logs/"+"log"+" counter.txt", "a");
    counter_log.write(str(generation_situation_counter)[1:-1]+"\r\n")
    counter_log.close()
    
    # Print everything
    for r in results[-20:]:
        print r["chromosome"]
    
    print_winner_results(results[-1])
    avg_result = float(sum([(r["combined"]) for r in results])) / len(results)
    print "Average chromosome combined fitness: " + str(avg_result)
    
    best_chrom_string = ""
    if((results[-1]["combined"]) > highest_fitness):
        print "* New best! *"
        # Highest fitness COMBINED
        highest_fitness = results[-1]["combined"]
        best_chromosome = results[-1]["chromosome"] 
        best_chrom_string = str(best_chromosome)
    popsize = len(results)
    
    print "Best ever: ", highest_fitness
    
    
    pater = 0
    for s in scenarios[:len(scenarios)-2]:
        pater += evaluate_paternoster(s)
    pater += evaluate_paternoster(scenarios[-1])/3 + evaluate_paternoster(scenarios[-2])/3#last one weight 1/3
    print "Paternoster: ", pater
    
    # Write to log file
    if(log_file):
        log_file = get_log_file()
        log_file.write(str(avg_result) + ";" + 
                       str(results[-1]["combined"]) +";" + 
                       str(pater) + ";" + 
                       best_chrom_string + ";" +
                       "\n")
        log_file.flush()
        log_file.close()
    
    if display_winner:
        global current_visualization_process
        if current_visualization_process != None:
            current_visualization_process.terminate()
        current_visualization_process = Process(target=evaluate_chromosome,
                                                args=(results[-1]["chromosome"], scenarios[2], None),  # TODO
                                                kwargs={'graphics':True})
        current_visualization_process.daemon = True
        current_visualization_process.start()

    new_population = [] 
    

    for _ in range(popsize*3/8-1):
        result = results[random.randint(popsize/2, popsize-1)]
        new_population.append(crossover2(results[-1]["chromosome"], result["chromosome"]))
    for _ in range(popsize*1/8):
        result = results[random.randint(0, popsize-1)]
        new_population.append(crossover2(results[-1]["chromosome"], result["chromosome"]))
    for _ in range(popsize*2/8-1):
        result = results[random.randint(popsize/2-1, popsize-2)]
        new_population.append(crossover2(results[-2]["chromosome"], result["chromosome"]))
    for _ in range(popsize*1/8):
        result1 = results[random.randint(popsize*3/4, popsize-1)]
        result2 = results[random.randint(popsize*3/4, popsize-1)]
        new_population.append(crossover2(result1["chromosome"], result2["chromosome"]))
    for _ in range(popsize*1/8-2):
        result1 = results[random.randint(0, popsize-1)]
        result2 = results[random.randint(0, popsize-1)]
        new_population.append(crossover2(result1["chromosome"], result2["chromosome"]))
    #for _ in range(2):
    #    new_population += [results[random.randint(popsize*3/4, popsize-1)]["chromosome"]]
    new_population += [results[-1]["chromosome"]] + [results[-2]["chromosome"]] + [results[-3]["chromosome"]] + [results[-4]["chromosome"]]
    
    
    if len(new_population) != len(population):
        raise Exception("Something happened with pop!  org-len=  " + str(len(population)) + "   len(new_gen) = " + str(len(new_population)) + "  len(results) = " + str(len(results)))

    for ind in new_population:
        for i in range(len(ind)):
            if random.random() < MUTATION_RATE:
                ind[i] = random.randint(0, NUMBER_OF_COMMANDS - 1)

    return new_population


def test_paternoster():
    for _ in range(50):
        scenario = StagedScenario(EveningRushScenario(15000, 10))
        result = evaluate_paternoster(scenario, graphics=True)
        print "result: " + str(result)
        if result > 0.3:
            evaluate_paternoster(scenario, graphics=True, print_results=True)
            break
        
def test_daniels():
    d = [0, 2, 2, 2, 2, 1, 0, 2, 1, 0, 2, 1, 2, 1, 0, 1, 2, 1, 1, 0, 2, 1, 2, 2, 2, 2, 1, 0, 2, 0, 0, 0, 2, 1, 2, 1, 1, 1, 2, 0, 1, 0, 2, 2, 2, 1, 0, 0, 1, 0, 2, 1, 0, 0, 0, 1, 0, 2, 0, 2, 1, 0, 2, 2, 0, 1, 1, 1, 1, 1, 0, 0, 0, 2, 2, 0, 1, 2, 0, 2, 0, 0, 0, 2, 0, 2, 1, 2, 0, 1, 0, 2, 1, 0, 2, 1, 1, 1, 2, 0, 2, 1, 0, 2, 1, 1, 2, 0, 1, 0, 2, 1, 0, 1, 1, 1, 0, 0, 0, 0, 2, 1, 1, 2, 2, 2, 0, 2, 2, 1, 1, 1, 1, 2, 0, 2, 2, 2, 2, 0, 0, 2, 1, 2, 2, 1, 1, 0, 2, 2, 1, 1, 2, 2, 0, 0, 2, 0, 1, 0, 0, 0, 0, 0, 2, 2, 2, 2, 1, 1, 1, 1, 1, 0, 1, 0, 1, 2, 2, 2, 1, 2, 2, 2, 2, 0, 1, 1, 0, 2, 2, 0, 2, 2, 2, 1, 0, 0, 0, 2, 2, 2, 2, 1, 0, 0, 2, 2, 1, 1, 2, 0, 2, 0, 1, 0, 2, 2, 0, 0, 2, 1, 2, 2, 0, 0, 2, 2, 2, 2, 1, 0, 1, 1, 0, 0, 0, 1, 1, 0, 0, 1, 2, 0, 0, 1, 0, 0, 0, 0, 2, 2, 0, 2, 1, 2, 1, 1, 1, 2, 2, 0, 1, 2, 1, 2, 0, 0, 0, 2, 1, 0, 1, 1, 2, 2, 0, 2, 0, 1, 0, 1, 2, 1, 0, 1, 2, 0]
    
    for i in range(100):
        print "Evening"
        morning = StagedScenario(MorningRushScenario(7000,10))
        print "d:" + str(evaluate_chromosome(d, morning, None))
        print "p:" + str(evaluate_paternoster(morning))
        
        print "Evening"
        evening = StagedScenario(EveningRushScenario(7000,10))
        print "d:" + str(evaluate_chromosome(d, evening, None))
        print "p:" + str(evaluate_paternoster(evening))
        
        print "Standard"
        standard = StagedScenario(StandardScenario(7000,10))
        print "d:" + str(evaluate_chromosome(d, standard, None))
        print "p:" + str(evaluate_paternoster(standard))
        
        print "-------------------------------------"
    
    
        
def test_best():
    cafter999gens = [2, 2, 1, 2, 1, 1, 2, 2, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 0, 2, 2, 1, 2, 2, 2, 0, 1, 0, 1, 1, 0, 2, 0, 1, 1, 2, 1, 1, 0, 0, 0, 1, 0, 0, 1, 1, 1, 0, 2, 0, 0, 0, 0, 0, 0, 0, 1, 2, 1, 0, 1, 2, 0, 2, 0, 2, 0, 1, 0, 0, 2, 2, 1, 2, 1, 0, 1, 0, 1, 0, 1, 2, 0, 1, 1, 0, 1, 1, 2, 2, 0, 1, 2, 2, 2, 0, 1, 1, 1, 2, 0, 1, 2, 2, 2, 1, 2, 0, 0, 0, 0, 0, 2, 2, 1, 1, 1, 0, 1, 1, 0, 2, 0, 0, 0, 0, 0, 2, 0, 2, 2, 2, 2, 0, 1, 1, 0, 2, 2, 1, 2, 2, 2, 1, 0, 1, 1, 0, 2, 0, 1, 1, 2, 0, 0, 1, 1, 0, 1, 0, 2, 0, 0, 2, 1, 2, 1, 1, 1, 2, 2, 2, 1, 2, 1, 2, 0, 2, 1, 0, 1, 1, 0, 0, 0, 2, 0, 0, 0, 1, 0, 0, 1, 1, 0, 0, 0, 1, 0, 2, 0, 0, 0, 0, 1, 0, 2, 0, 0, 2, 1, 2, 2, 0, 2, 1, 1, 0, 1, 0, 2, 0, 1, 1, 1, 2, 1, 1, 1, 2, 1, 0, 0, 1, 2, 1, 0, 1, 1, 1, 2, 2, 0, 0, 1, 0, 0, 0, 2, 2, 0, 0, 0, 0, 0, 0, 0, 1, 0, 2, 0, 0, 0, 1, 0, 1, 0, 0, 1, 2, 0, 1, 0, 2, 2, 0, 2, 2, 0, 2, 2, 0, 1, 1, 0, 2]
    bafter999gens = [2, 2, 1, 0, 2, 2, 0, 2, 1, 2, 2, 1, 2, 0, 1, 1, 1, 1, 2, 2, 1, 1, 2, 0, 2, 0, 0, 0, 2, 1, 2, 0, 0, 1, 0, 1, 2, 1, 0, 2, 1, 2, 1, 1, 1, 0, 1, 2, 0, 0, 2, 0, 0, 0, 0, 2, 1, 1, 1, 2, 1, 1, 2, 2, 2, 2, 0, 0, 1, 2, 1, 0, 2, 2, 0, 2, 1, 1, 2, 2, 1, 2, 1, 0, 0, 0, 0, 1, 1, 2, 1, 2, 2, 1, 2, 1, 2, 1, 1, 1, 0, 2, 2, 2, 1, 0, 2, 2, 0, 1, 2, 0, 0, 2, 2, 2, 2, 1, 1, 2, 1, 0, 1, 0, 0, 0, 0, 1, 2, 0, 1, 1, 2, 0, 2, 1, 0, 0, 1, 2, 2, 0, 2, 0, 2, 2, 1, 0, 2, 1, 0, 0, 1, 1, 1, 1, 1, 0, 0, 0, 1, 0, 0, 1, 2, 2, 1, 2, 2, 2, 2, 1, 0, 0, 0, 0, 0, 1, 1, 2, 0, 1, 1, 1, 0, 0, 0, 2, 1, 0, 0, 2, 1, 2, 0, 1, 0, 0, 0, 2, 1, 2, 2, 0, 0, 2, 1, 1, 0, 1, 0, 1, 0, 1, 2, 2, 0, 2, 2, 1, 1, 0, 0, 2, 2, 0, 1, 1, 1, 1, 2, 1, 1, 0, 2, 1, 0, 2, 0, 2, 2, 2, 0, 1, 1, 2, 1, 1, 1, 2, 1, 0, 2, 1, 0, 2, 0, 0, 2, 1, 2, 1, 1, 1, 1, 1, 0, 1, 0, 2, 1, 1, 0, 2, 0, 0, 2, 0, 2, 0, 2, 1, 1, 0, 0, 1, 1, 0]
    dafter999gens = [2, 2, 2, 1, 1, 0, 1, 2, 1, 0, 1, 2, 1, 2, 1, 1, 0, 1, 0, 2, 0, 1, 0, 1, 2, 2, 2, 1, 1, 0, 0, 2, 2, 0, 1, 1, 0, 0, 0, 0, 1, 0, 1, 1, 1, 1, 0, 0, 2, 1, 2, 0, 2, 2, 1, 2, 0, 0, 1, 0, 0, 0, 1, 0, 2, 1, 2, 0, 0, 1, 1, 1, 2, 2, 2, 2, 2, 1, 1, 2, 0, 0, 2, 2, 0, 2, 0, 2, 1, 0, 1, 2, 1, 0, 1, 2, 0, 1, 1, 2, 1, 1, 2, 2, 2, 2, 0, 0, 0, 0, 0, 1, 1, 1, 2, 2, 0, 2, 0, 2, 1, 2, 0, 1, 1, 2, 0, 1, 1, 2, 1, 2, 0, 2, 2, 2, 1, 0, 0, 2, 0, 1, 1, 0, 2, 0, 0, 1, 2, 2, 0, 1, 1, 1, 1, 1, 0, 1, 1, 0, 1, 1, 0, 0, 2, 2, 2, 2, 0, 2, 1, 2, 1, 0, 0, 1, 1, 1, 2, 1, 2, 1, 0, 2, 1, 0, 1, 2, 2, 2, 1, 2, 1, 1, 2, 2, 1, 0, 0, 1, 2, 2, 1, 0, 2, 2, 0, 0, 0, 0, 2, 2, 0, 0, 1, 2, 2, 0, 0, 0, 2, 0, 2, 0, 1, 2, 0, 2, 2, 1, 1, 0, 1, 2, 0, 2, 0, 2, 2, 1, 0, 0, 0, 0, 1, 2, 1, 1, 2, 2, 0, 1, 1, 2, 2, 2, 1, 2, 1, 0, 0, 0, 2, 2, 2, 2, 2, 0, 1, 0, 1, 2, 1, 2, 0, 0, 2, 1, 1, 0, 1, 0, 0, 0, 0, 0, 2, 0]
    #after999gens =  [1, 2, 0, 2, 1, 1, 2, 0, 2, 2, 2, 1, 0, 1, 1, 1, 0, 1, 1, 2, 2, 2, 2, 2, 2, 2, 1, 2, 2, 0, 1, 0, 0, 1, 1, 1, 0, 1, 2, 0, 1, 0, 2, 2, 2, 0, 2, 0, 1, 0, 2, 1, 2, 0, 2, 2, 0, 2, 1, 2, 1, 0, 1, 2, 0, 2, 0, 0, 0, 1, 0, 2, 2, 1, 0, 0, 0, 1, 1, 2, 0, 2, 1, 1, 1, 1, 0, 1, 2, 1, 2, 2, 1, 0, 2, 0, 0, 0, 2, 0, 0, 2, 0, 2, 1, 1, 2, 0, 0, 1, 1, 1, 0, 0, 0, 1, 2, 0, 2, 0, 2, 0, 1, 2, 2, 0, 2, 1, 0, 1, 0, 2, 0, 1, 0, 0, 0, 2, 1, 2, 2, 2, 1, 2, 0, 1, 1, 2, 0, 0, 2, 2, 1, 2, 2, 0, 1, 1, 1, 0, 2, 1, 0, 1, 1, 1, 2, 2, 2, 0, 0, 0, 0, 2, 1, 2, 1, 1, 1, 2, 2, 1, 2, 2, 1, 0, 0, 2, 0, 0, 2, 2, 1, 2, 2, 0, 1, 0, 1, 2, 1, 1, 1, 2, 0, 1, 0, 1, 1, 1, 1, 2, 0, 0, 1, 2, 0, 1, 1, 2, 1, 0, 0, 1, 2, 0, 0, 0, 1, 1, 1, 2, 2, 2, 0, 2, 0, 1, 2, 0, 1, 2, 0, 1, 0, 2, 0, 0, 0, 1, 2, 0, 0, 1, 0, 2, 0, 0, 0, 2, 1, 1, 1, 0, 1, 2, 1, 2, 0, 0, 1, 0, 1, 2, 0, 1, 1, 2, 0, 2, 0, 2, 0, 2, 0, 1, 0, 2]
    #after999gens = [2, 2, 2, 2, 1, 1, 0, 0, 2, 1, 0, 1, 2, 1, 2, 1, 0, 1, 0, 2, 2, 0, 2, 2, 0, 2, 1, 0, 1, 2, 1, 0, 0, 0, 0, 0, 1, 0, 2, 0, 2, 0, 2, 1, 2, 0, 1, 0, 1, 2, 2, 0, 2, 0, 2, 2, 2, 2, 2, 2, 1, 2, 0, 1, 1, 2, 2, 0, 1, 0, 0, 2, 2, 1, 1, 0, 0, 1, 1, 1, 0, 2, 1, 1, 2, 1, 0, 1, 0, 1, 0, 2, 1, 1, 2, 2, 0, 2, 0, 1, 2, 0, 0, 2, 2, 2, 2, 2, 0, 1, 2, 1, 2, 0, 2, 2, 2, 2, 0, 0, 2, 0, 1, 2, 0, 1, 2, 1, 2, 0, 1, 2, 1, 2, 1, 1, 2, 2, 1, 2, 1, 1, 1, 0, 0, 2, 1, 2, 1, 0, 2, 2, 0, 2, 2, 0, 0, 1, 1, 0, 2, 1, 0, 1, 1, 1, 2, 2, 2, 1, 0, 2, 0, 1, 1, 2, 1, 0, 0, 2, 0, 0, 1, 1, 0, 0, 2, 1, 2, 1, 1, 0, 2, 1, 2, 0, 1, 0, 1, 2, 2, 1, 1, 1, 0, 1, 2, 2, 0, 1, 1, 2, 2, 2, 0, 0, 1, 0, 1, 0, 1, 0, 2, 0, 1, 1, 2, 2, 2, 0, 1, 2, 0, 1, 0, 2, 0, 1, 2, 0, 1, 2, 0, 1, 0, 0, 0, 0, 0, 1, 2, 0, 0, 1, 1, 2, 0, 2, 0, 2, 1, 1, 0, 0, 1, 1, 0, 2, 2, 0, 1, 0, 0, 1, 1, 0, 1, 0, 1, 2, 0, 1, 0, 2, 0, 1, 0, 2]
    after999gens =  [2, 2, 1, 2, 2, 1, 2, 2, 2, 2, 1, 0, 1, 2, 1, 1, 1, 1, 2, 2, 1, 1, 2, 2, 2, 2, 0, 1, 0, 0, 1, 1, 2, 0, 1, 0, 2, 0, 0, 2, 1, 0, 2, 0, 1, 1, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 2, 0, 0, 1, 0, 0, 0, 1, 2, 0, 2, 0, 1, 2, 0, 2, 2, 2, 2, 0, 1, 1, 1, 1, 0, 1, 1, 2, 2, 2, 2, 1, 1, 2, 0, 2, 2, 2, 1, 2, 0, 1, 1, 2, 1, 2, 0, 0, 2, 2, 0, 1, 1, 2, 0, 0, 0, 0, 2, 1, 0, 2, 0, 0, 0, 2, 1, 0, 0, 0, 2, 2, 1, 2, 1, 2, 0, 1, 0, 0, 0, 0, 2, 1, 2, 2, 2, 2, 0, 0, 1, 2, 2, 1, 1, 0, 2, 0, 1, 2, 2, 0, 0, 0, 1, 0, 0, 2, 1, 1, 0, 2, 2, 2, 1, 0, 0, 1, 1, 0, 1, 2, 1, 2, 1, 1, 1, 2, 0, 0, 1, 1, 0, 0, 1, 0, 0, 2, 1, 1, 1, 0, 2, 0, 1, 0, 1, 1, 1, 2, 0, 0, 0, 1, 0, 1, 1, 0, 0, 1, 2, 0, 2, 2, 2, 2, 2, 1, 0, 2, 2, 0, 2, 0, 0, 1, 0, 1, 0, 0, 2, 1, 0, 0, 0, 0, 2, 2, 1, 2, 0, 1, 0, 2, 0, 0, 1, 2, 0, 0, 1, 1, 1, 2, 0, 2, 1, 2, 2, 1, 1, 0, 0, 1, 2, 0, 0, 1, 1, 1, 1, 2, 2, 0, 2, 2, 2, 0, 1, 2, 0, 1]
    point43 = [0, 2, 1, 2, 1, 1, 2, 2, 0, 1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 2, 0, 1, 2, 1, 2, 2, 2, 0, 2, 0, 2, 1, 2, 2, 0, 0, 0, 2, 1, 0, 2, 0, 1, 2, 2, 0, 0, 0, 2, 2, 2, 0, 0, 0, 0, 2, 1, 1, 2, 1, 2, 0, 0, 1, 2, 1, 0, 0, 1, 1, 2, 1, 0, 2, 1, 2, 1, 1, 2, 2, 0, 2, 0, 0, 0, 2, 1, 1, 0, 1, 1, 2, 0, 1, 0, 2, 1, 2, 2, 2, 0, 2, 0, 0, 1, 2, 2, 2, 2, 0, 2, 0, 0, 0, 1, 2, 1, 0, 0, 0, 2, 2, 0, 2, 0, 0, 0, 2, 2, 1, 2, 0, 0, 1, 0, 1, 1, 0, 0, 0, 0, 1, 0, 1, 1, 1, 2, 1, 2, 1, 0, 0, 2, 2, 0, 0, 1, 1, 2, 1, 1, 1, 0, 2, 2, 1, 0, 1, 2, 0, 2, 1, 2, 0, 0, 0, 1, 0, 2, 2, 0, 0, 0, 2, 2, 0, 0, 0, 2, 1, 2, 2, 0, 1, 1, 0, 1, 0, 2, 1, 0, 2, 2, 1, 1, 0, 1, 0, 2, 0, 1, 1, 2, 1, 1, 1, 2, 0, 0, 1, 1, 0, 1, 1, 1, 0, 1, 2, 2, 2, 1, 0, 1, 1, 1, 2, 0, 1, 1, 2, 0, 0, 2, 1, 2, 0, 2, 1, 0, 2, 1, 2, 2, 1, 0, 2, 0, 2, 1, 2, 2, 0, 1, 0, 0, 1, 2, 1, 1, 0, 1, 0, 0, 1, 0, 1, 1, 1, 0, 2, 1, 2, 0, 1, 2, 0, 1, 1]
    #best = [0, 2, 2, 2, 0, 1, 0, 2, 0, 1, 1, 1, 1, 2, 2, 1, 0, 1, 0, 2, 2, 2, 0, 1, 0, 2, 1, 0, 0, 2, 1, 2, 2, 1, 1, 2, 2, 0, 2, 2, 2, 0, 2, 2, 2, 2, 0, 2, 0, 0, 2, 0, 1, 0, 1, 1, 2, 2, 0, 2, 0, 1, 2, 1, 1, 1, 2, 2, 1, 1, 1, 0, 0, 2, 0, 2, 1, 1, 1, 2, 0, 2, 2, 0, 0, 0, 2, 0, 2, 1, 1, 0, 2, 1, 1, 0, 1, 0, 1, 1, 1, 1, 1, 1, 2, 2, 0, 2, 0, 1, 1, 1, 0, 0, 0, 2, 1, 1, 0, 2, 1, 1, 2, 2, 2, 0, 1, 0, 2, 0, 1, 0, 1, 2, 0, 2, 0, 1, 2, 1, 2, 1, 2, 1, 1, 2, 1, 2, 2, 2, 0, 0, 0, 1, 2, 0, 2, 1, 1, 0, 2, 0, 2, 2, 2, 1, 0, 1, 2, 0, 2, 2, 1, 1, 2, 1, 1, 0, 0, 2, 0, 0, 2, 2, 1, 0, 0, 2, 2, 0, 2, 2, 2, 2, 1, 0, 2, 0, 2, 2, 0, 2, 1, 2, 2, 0, 0, 0, 1, 2, 0, 2, 1, 1, 1, 2, 2, 0, 0, 2, 0, 0, 0, 0, 2, 0, 0, 1, 1, 2, 1, 0, 1, 1, 2, 0, 0, 0, 2, 2, 2, 2, 2, 1, 1, 0, 0, 2, 1, 1, 1, 0, 0, 2, 1, 1, 0, 1, 0, 2, 1, 0, 1, 1, 2, 0, 1, 1, 1, 0, 0, 1, 2, 1, 1, 0, 1, 1, 0, 1, 1, 2, 1, 0, 1, 0, 2, 1]
    best2= [1, 2, 1, 2, 2, 1, 0, 0, 0, 1, 2, 1, 0, 2, 0, 1, 0, 1, 2, 2, 1, 2, 0, 0, 0, 2, 0, 0, 2, 2, 2, 2, 1, 2, 2, 0, 2, 2, 2, 2, 1, 0, 1, 1, 0, 1, 0, 0, 2, 0, 2, 2, 1, 0, 1, 1, 0, 0, 1, 2, 1, 1, 1, 1, 1, 1, 2, 2, 1, 1, 0, 0, 2, 2, 0, 2, 1, 1, 1, 2, 2, 2, 0, 1, 1, 0, 1, 2, 2, 1, 2, 2, 2, 2, 1, 0, 1, 1, 2, 2, 2, 0, 1, 1, 0, 0, 1, 2, 1, 1, 0, 1, 0, 0, 1, 1, 1, 2, 0, 2, 0, 2, 2, 1, 2, 0, 2, 2, 1, 0, 0, 0, 2, 0, 1, 1, 1, 1, 1, 2, 1, 2, 2, 2, 1, 2, 1, 2, 0, 2, 1, 0, 0, 1, 2, 1, 2, 1, 2, 0, 1, 0, 1, 1, 2, 2, 0, 1, 2, 2, 2, 2, 1, 2, 0, 0, 1, 2, 2, 0, 1, 1, 2, 2, 0, 0, 1, 0, 0, 1, 1, 2, 2, 1, 2, 0, 2, 0, 0, 1, 0, 2, 0, 0, 2, 1, 0, 0, 2, 0, 1, 2, 0, 0, 1, 1, 1, 2, 2, 2, 2, 0, 1, 0, 2, 2, 0, 0, 1, 0, 0, 1, 1, 1, 2, 1, 1, 1, 2, 1, 1, 2, 2, 1, 1, 2, 1, 2, 1, 0, 1, 1, 2, 2, 1, 0, 2, 0, 2, 2, 1, 1, 1, 0, 2, 2, 2, 0, 0, 0, 0, 1, 1, 0, 0, 2, 1, 2, 2, 2, 1, 2, 1, 0, 2, 2, 2, 1]
    best3= [1, 2, 1, 2, 2, 1, 0, 0, 0, 2, 0, 1, 0, 1, 1, 1, 1, 1, 0, 2, 1, 2, 0, 0, 0, 2, 2, 2, 1, 2, 1, 2, 1, 1, 2, 2, 1, 2, 0, 2, 1, 0, 0, 2, 2, 1, 2, 0, 2, 1, 2, 2, 2, 0, 1, 2, 2, 2, 2, 0, 2, 0, 1, 1, 1, 0, 2, 1, 1, 1, 2, 2, 0, 2, 0, 2, 2, 1, 0, 2, 2, 2, 1, 2, 1, 0, 1, 2, 2, 1, 2, 2, 2, 2, 1, 2, 0, 1, 2, 2, 1, 0, 1, 1, 0, 0, 1, 2, 1, 0, 0, 1, 0, 0, 1, 1, 1, 1, 0, 2, 0, 2, 2, 1, 2, 0, 2, 2, 0, 0, 0, 0, 2, 0, 1, 1, 1, 2, 1, 2, 1, 0, 2, 1, 1, 2, 1, 2, 2, 1, 1, 0, 0, 1, 2, 1, 1, 1, 2, 0, 1, 2, 1, 1, 0, 0, 2, 0, 2, 1, 0, 1, 0, 1, 0, 2, 2, 1, 0, 0, 0, 2, 2, 2, 1, 0, 1, 0, 2, 2, 2, 2, 2, 1, 2, 0, 2, 0, 0, 1, 0, 2, 1, 1, 2, 1, 0, 0, 2, 0, 1, 2, 0, 0, 1, 2, 0, 2, 2, 2, 2, 0, 1, 0, 2, 0, 0, 0, 1, 1, 2, 1, 0, 1, 2, 1, 0, 1, 2, 1, 1, 1, 2, 1, 1, 2, 0, 0, 1, 2, 1, 1, 2, 2, 1, 0, 2, 1, 2, 2, 2, 0, 1, 0, 0, 0, 2, 0, 2, 0, 0, 1, 1, 1, 0, 2, 1, 2, 2, 2, 1, 2, 1, 0, 2, 2, 2, 1]
    best4= [1, 2, 2, 2, 2, 1, 0, 0, 2, 0, 0, 1, 0, 0, 1, 1, 1, 1, 0, 2, 1, 2, 0, 2, 0, 2, 2, 2, 1, 2, 1, 2, 1, 1, 2, 2, 1, 2, 0, 1, 2, 0, 1, 0, 2, 0, 2, 0, 0, 0, 2, 2, 0, 0, 0, 1, 2, 2, 2, 0, 2, 0, 1, 2, 1, 0, 2, 1, 1, 1, 2, 2, 0, 2, 0, 2, 2, 1, 1, 2, 1, 2, 1, 2, 1, 0, 1, 2, 2, 1, 0, 2, 2, 2, 1, 0, 0, 1, 0, 2, 1, 1, 1, 1, 0, 0, 0, 0, 1, 2, 1, 0, 0, 0, 1, 1, 1, 1, 0, 2, 0, 2, 1, 1, 2, 0, 1, 2, 0, 0, 0, 0, 2, 0, 1, 2, 1, 2, 1, 0, 1, 0, 2, 1, 2, 2, 2, 2, 2, 2, 1, 0, 0, 1, 1, 2, 2, 1, 2, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 2, 2, 0, 1, 2, 0, 2, 0, 0, 2, 1, 0, 2, 2, 0, 0, 1, 0, 0, 2, 1, 2, 2, 1, 0, 0, 2, 0, 2, 1, 2, 2, 0, 0, 0, 1, 0, 1, 1, 2, 2, 0, 0, 0, 2, 1, 0, 2, 1, 0, 1, 2, 1, 1, 0, 0, 2, 0, 1, 1, 2, 1, 1, 0, 2, 1, 0, 2, 2, 0, 1, 2, 2, 1, 1, 0, 1, 0, 0, 0, 1, 1, 0, 2, 2, 0, 2, 1, 2, 2, 1, 0, 2, 0, 2, 2, 2, 0, 0, 0, 1, 1, 2, 2, 1, 2, 0, 2, 2, 1, 2, 1, 1, 2, 2, 0, 2, 1]
    best_evening = [2, 2, 0, 0, 2, 2, 1, 0, 1, 1, 0, 2, 2, 1, 1, 1, 1, 1, 0, 1, 1, 0, 1, 2, 1, 2, 1, 1, 0, 2, 2, 1, 2, 1, 0, 2, 1, 0, 1, 2, 1, 0, 1, 0, 0, 1, 0, 1, 0, 0, 1, 0, 1, 2, 2, 0, 2, 1, 2, 0, 2, 1, 2, 0, 1, 0, 1, 1, 0, 0, 0, 1, 2, 2, 1, 2, 2, 2, 2, 2, 1, 2, 2, 0, 0, 1, 0, 2, 1, 0, 2, 0, 2, 1, 1, 1, 0, 0, 0, 1, 2, 1, 2, 0, 0, 0, 1, 2, 1, 2, 1, 2, 0, 0, 1, 2, 1, 0, 1, 1, 0, 0, 0, 1, 0, 2, 1, 2, 0, 0, 0, 2, 1, 1, 0, 1, 0, 0, 0, 2, 1, 1, 2, 0, 0, 0, 2, 2, 1, 1, 0, 1, 2, 2, 1, 1, 2, 1, 2, 0, 1, 0, 1, 2, 0, 1, 2, 1, 0, 1, 0, 2, 1, 0, 2, 1, 1, 1, 1, 2, 2, 2, 0, 0, 1, 0, 2, 1, 1, 0, 1, 2, 0, 2, 2, 2, 0, 1, 0, 0, 1, 0, 2, 1, 1, 1, 2, 0, 0, 2, 0, 2, 1, 2, 1, 1, 2, 1, 0, 0, 1, 1, 2, 0, 1, 0, 1, 1, 2, 0, 2, 1, 1, 2, 2, 0, 0, 1, 0, 0, 2, 0, 1, 1, 1, 1, 2, 0, 2, 2, 2, 1, 2, 1, 2, 0, 1, 1, 2, 2, 0, 1, 0, 0, 2, 2, 2, 0, 1, 2, 1, 0, 0, 1, 2, 1, 1, 0, 2, 2, 0, 0, 1, 0, 1, 0, 2, 0]
    #best= [2, 2, 1, 2, 0, 1, 2, 0, 2, 0, 1, 1, 1, 2, 2, 1, 2, 1, 0, 0, 0, 1, 2, 1, 0, 2, 0, 0, 0, 2, 0, 2, 0, 2, 1, 0, 0, 0, 0, 0, 0, 0, 1, 2, 2, 0, 2, 0, 0, 1, 0, 0, 2, 0, 2, 1, 0, 0, 0, 2, 0, 0, 1, 2, 0, 1, 1, 2, 1, 2, 1, 2, 1, 0, 2, 1, 1, 2, 2, 1, 0, 1, 0, 2, 1, 0, 1, 1, 0, 2, 0, 2, 1, 2, 2, 0, 0, 2, 2, 0, 1, 1, 2, 1, 1, 1, 1, 2, 2, 1, 2, 1, 1, 0, 2, 2, 2, 0, 0, 0, 0, 1, 0, 1, 1, 1, 2, 2, 0, 0, 2, 1, 0, 2, 2, 1, 0, 1, 1, 0, 0, 2, 0, 2, 2, 0, 0, 0, 1, 1, 2, 2, 1, 0, 1, 0, 1, 0, 1, 1, 2, 0, 2, 1, 0, 0, 1, 1, 2, 2, 2, 0, 2, 1, 0, 0, 1, 1, 1, 0, 0, 1, 0, 1, 1, 0, 2, 0, 2, 2, 1, 0, 0, 1, 1, 2, 2, 0, 2, 2, 0, 2, 2, 2, 0, 1, 1, 2, 0, 2, 0, 1, 0, 2, 1, 0, 2, 0, 0, 2, 2, 2, 0, 0, 2, 2, 2, 1, 0, 0, 1, 1, 1, 0, 0, 0, 2, 1, 1, 1, 1, 2, 0, 0, 0, 1, 0, 0, 1, 2, 2, 1, 2, 2, 2, 1, 1, 0, 2, 2, 1, 2, 1, 2, 0, 1, 0, 0, 1, 0, 0, 0, 2, 0, 1, 0, 0, 0, 1, 1, 1, 0, 2, 0, 0, 1, 2, 0]
    best = [2, 2, 1, 2, 2, 1, 2, 0, 2, 1, 2, 1, 2, 2, 1, 1, 1, 1, 2, 2, 0, 1, 1, 2, 2, 2, 0, 1, 2, 2, 0, 0, 1, 1, 2, 1, 0, 2, 1, 0, 2, 0, 1, 0, 2, 1, 2, 0, 2, 1, 0, 0, 0, 0, 2, 2, 0, 1, 0, 1, 2, 1, 2, 1, 1, 2, 0, 1, 1, 1, 2, 2, 0, 2, 0, 0, 0, 1, 1, 1, 2, 0, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 1, 1, 2, 0, 2, 1, 1, 0, 2, 1, 2, 1, 1, 0, 2, 2, 0, 2, 1, 0, 0, 2, 0, 1, 0, 0, 1, 1, 1, 1, 0, 2, 2, 0, 2, 0, 0, 1, 2, 0, 2, 1, 0, 2, 1, 2, 2, 0, 2, 1, 0, 1, 0, 1, 0, 0, 0, 1, 1, 2, 2, 2, 1, 2, 0, 1, 0, 1, 0, 0, 2, 2, 0, 1, 1, 0, 2, 1, 0, 0, 2, 0, 1, 2, 0, 2, 1, 1, 2, 1, 0, 2, 0, 0, 0, 0, 0, 2, 0, 2, 0, 2, 0, 0, 1, 1, 2, 2, 2, 2, 0, 0, 1, 2, 1, 2, 2, 0, 1, 2, 1, 0, 1, 2, 0, 1, 2, 2, 1, 0, 2, 0, 0, 2, 0, 2, 2, 1, 2, 2, 1, 2, 2, 0, 0, 2, 1, 1, 0, 2, 1, 1, 2, 2, 0, 2, 0, 0, 2, 0, 1, 1, 0, 0, 0, 2, 0, 2, 1, 2, 0, 1, 0, 1, 1, 1, 0, 0, 1, 2, 2, 0, 2, 2, 2, 2, 0, 2, 2, 0, 1, 2, 0, 0, 1]
 

    """after999gens[287] = 1
    after999gens[176] = 1
    after999gens[129] = 1
    after999gens[213] = 1
    after999gens[211] = 1
    after999gens[131] = 1"""
    for i in range(100):
        scenario = StagedScenario(EveningRushScenario(13000, 10))
        ours = evaluate_chromosome(best, scenario, None)#, graphics=True, print_results=True)
        pater = evaluate_paternoster(scenario)#, graphics=True, print_results=True)
        #if ours > pater:
        #    print "Won with " + str(ours-pater)
        #else:
        #    print "Lost with " + str(pater-ours)
        print "ours: " + str(ours)
        print "pater: " + str(pater)
        print ""
        #if ours - pater > 0.0:
        #    evaluate_chromosome(best_evening, scenario, None, graphics=True, print_results=True)
        #    evaluate_paternoster(scenario, graphics=True, print_results=True)
        
    
def main_evolution():
    log_file = get_log_file()
    log_file.write("Average fitness;" + 
                    "Best fitness;" + 
                    "Paternoster\n")
    log_file.flush()
    population = []
    for i in range(32):
        population.append([])
        for j in range(NUMBER_OF_SITUATIONS):
            population[len(population) - 1].append(random.randint(0, NUMBER_OF_COMMANDS - 1))
            
        population[-1][16] = 1  # I'm full and stuff's happening over there
        population[-1][18] = 0  # I'm full and stuff's happening behind me
        
    
    scenarios = []
    for i in range(6):
        scenarios += [StagedScenario(EveningRushScenario(13000, 10))]
    
    for i in range(1000):
        print "GENERATION " + str(i) + ":"
            
        if i == 5:
            population = population[len(population)-32:]
           
        if i == 10:
            population = population[len(population)-32:]
        if i == 5:
            MUTATION_RATE = 1/float(100)
        
        if i == 50:
            population = population[len(population)-24:]
            MUTATION_RATE = 0
        elif i > 30:
            MUTATION_RATE = 1/float(60*i)    
        elif i > 10:
            MUTATION_RATE = 1/float(25*i)
        population = next_generation(population, scenarios, i, display_winner=False , log_file=log_file)
    
    log_file = get_log_file()
    log_file.write("==== INFORMATION ====\r\n\r\n")
    log_file.write("-- Situation counter (total)\r\n"+str(situation_counter))
    log_file.close()
    print("Chromosome with best fitness (" + str(highest_fitness) + ") : ")
    print(best_chromosome)

def get_log_file():
    return open("logs/" + "logfile" + '.txt', 'a')
  
if __name__ == '__main__':
    #test_daniels()
    #main_evolution()
    #test_best()
    test_paternoster()
