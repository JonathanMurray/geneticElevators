import pygame
from pygame import Surface
from model import Direction

SCREEN_WIDTH = 400
SCREEN_HEIGHT = 700
PIXELS_PER_METER = 10








def init_visualization(_elevator, floors, _controller, _chromosome_controller=False, _event_callback=None):
    global screen, elevatorDrawable, floorDrawables, runs, controller, elevator, event_callback, chromosome_controller
    chromosome_controller = _chromosome_controller
    runs = 0
    controller = _controller
    elevator = _elevator
    elevatorDrawable = ElevatorDrawable(_elevator)
    floorDrawables = []
    for floor in floors:
        floorDrawable = FloorDrawable(floor)
        floorDrawables.append(floorDrawable)
    event_callback = _event_callback
    pygame.init()
    
    
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

  

def draw():
    """ Returns False if user tries to exit """  
    global runs, controller, elevator
    runs += 1
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return False
        if event_callback != None:
            event_callback(event)
            
    screen.fill((0, 0, 0))
    elevatorDrawable.draw()   
    for i, floorDrawable in enumerate(floorDrawables):
        floorDrawable.draw()
        if controller._elevator_buttons[i]:
            # Draw line between target floor and elevator
            pygame.draw.line(screen, (055,155,55), (elevatorDrawable.x, elevatorDrawable.y), (64,floorDrawable.y))
    blit_text()
    pygame.display.flip()   
    return True
        
        
def blit_text():
    if chromosome_controller:
        myfont = pygame.font.SysFont("Monospace", 13)
        for i,line in enumerate(controller.situation_string):
            label = myfont.render(line, 1, (255, 255, 255))
            screen.blit(label, (150, 30+i*10))    
           
        myfont = pygame.font.SysFont("Consolas", 13) 
        label = myfont.render("State: " + elevator._state, 1, (255,255,255))
        screen.blit(label, (220,10))
        
        label = myfont.render("Action: " + controller.command_string, 1, (255,255,255))
        screen.blit(label, (220,25))
        
        label = myfont.render("Direction: " + str(elevator.direction), 1, (255,255,255))
        screen.blit(label, (220,40))
        
        label = myfont.render("Situation index:: " + str(controller.situation_index), 1, (255,255,255))
        screen.blit(label, (220,55))  
    myfont = pygame.font.SysFont("Consolas", 13) 
    label = myfont.render("Runs: " + str(runs), 1, (255, 255, 255))
    screen.blit(label, (10, 10))









""" -----------      ELEVATOR DRAWABLE       -----------------"""

class ElevatorDrawable:
    def __init__(self, elevator):
        self.elevator = elevator
        self.x = 30
        self.y = 0
          
    def draw(self):
        w = 25
        h = 30
        self.y = SCREEN_HEIGHT - self.elevator.height_above_ground * PIXELS_PER_METER - h
        rect = pygame.Rect(self.x, self.y, w, h)
        pygame.draw.rect(screen, (0, 128, 255), rect)
        myfont = pygame.font.SysFont("Consolas", 13)
        label = myfont.render(str(len(self.elevator._passengers)), 1, (255, 255, 255))
        screen.blit(label, (self.x, self.y))
  
        
      
  
""" -----------      FLOOR DRAWABLE       -----------------"""  
        
class FloorDrawable:
    def __init__(self, start_floor):
        self.floor = start_floor
        self.y = SCREEN_HEIGHT - self.floor.height_above_ground * PIXELS_PER_METER
        
    def draw(self):
        w = 9
        h = 9
        start = (64, self.y)
        end = (SCREEN_WIDTH, self.y)
        color = {
                 Direction.UP:(0, 255, 0),
                 Direction.DOWN:(255, 0, 0),
                 }
        
        pygame.draw.line(screen, (0, 128, 255), start, end)
        people = self.floor._people_waiting
        i = 0
        for dir, people in people.iteritems():
            for person in people:
                rect = pygame.Rect(68 + i * (h + 5), self.y-h, w, h)
                pygame.draw.rect(screen, color[dir], rect)
                i += 1



""" ---------------------------------------------------------"""


