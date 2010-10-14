import sys
from SimPy.Simulation import *
from SimPy.SimPlot import *
import random

# Import our modules
from Scheduler import *
from SchedulingAlgos import *
from TaskGenerator import *
from Task import *
from AbstractResource import *

class GridMachine(AbstractResource):
    def __init__(self, number, queue_max_size=10, factor=1):
        AbstractResource.__init__(self, capacity=1, name="M"+str(number)+':'+str(factor),
                            queue_max=queue_max_size)
        self.factor = factor
    
currentMachine=0

#CONSTANTS
SCHEDULER_MAX_QUEUE_SIZE=5000000
MACHINE_MAX_QUEUE_SIZE=100000
GRID_SIZE=10
SCHEDULER_HOLD_TIME=0.000001

#TASK CONSTANTS
SIMPLE_TASK_TIME=1.0
NORMAL_TASK_TIME=50.0
COMPLEX_TASK_TIME=150.0

SIMPLE_TASK_PROB=0.33
NORMAL_TASK_PROB=0.33
COMPLEX_TASK_PROB=0.34

DEFAULT_SCHEDULING_ALG = weighted_random_schedule

DEFAULT_SIMULATION_TIME = 10000

class GridSimScenario:
    def __init__(self):
        
        # Parameters
        self.grid_description = [(GRID_SIZE, 1)] # All machines have the same performance
        self.schedule_algorithm = DEFAULT_SCHEDULING_ALG
        self.task_distribution = [("simple", SIMPLE_TASK_PROB, SIMPLE_TASK_TIME),
                                     ("normal", NORMAL_TASK_PROB, NORMAL_TASK_TIME),
                                     ("complex", COMPLEX_TASK_PROB, COMPLEX_TASK_TIME)]
        self.task_distribution = [("simple", SIMPLE_TASK_PROB, SIMPLE_TASK_TIME)]
        self.scheduler_queue_size = SCHEDULER_MAX_QUEUE_SIZE
        self.machine_queue_size = MACHINE_MAX_QUEUE_SIZE
        self.task_class_selector_seed = random.randint(11, 9999)
        self.task_duration_seed = random.randint(11, 9999)
        self.task_arrival_seed = random.randint(11, 9999)
        self.task_arrival_mean = 10.0
        self.scheduler_hold_time = SCHEDULER_HOLD_TIME
        self.sim_time = DEFAULT_SIMULATION_TIME
        
        self.total_tasks = 0
        self.total_arriving_tasks = 0
        self.total_leaving_tasks = 0
        self.total_task_drops = 0
        
        self.initiated = False
        self.monitors = {}
        
    def init_objects(self):
        if self.initiated:
            raise Exception("Objects already initiated")
        else:
            self.initiated = True
        #objects
        self.scheduler = Scheduler(queue_max_size=self.scheduler_queue_size)
        self.machineList = []
        count = 0
        for m in self.grid_description:
            for n in range(m[0]):
                self.machineList.append(GridMachine(count, self.machine_queue_size, m[1]))
                count += 1
        
        # Monitors
        self.monitors['N'] = Monitor("N") # Number of clients
        self.monitors['T'] = Monitor("T") # Service time
        
arguments = [
             ('--grid-size', 'number of machines in the grid', 'integer', ),
             ('--scheduling-algorithm', 'scheduling algorithm', 'one of random, least_full, round_robin, fill_queue', ),
             ('--scheduler-qs', 'scheduler queue size', 'integer', ),
             ('--machine-qs', 'machine queue size', 'integer',  ),
             ('--scheduler-ht', 'scheduler hold time', 'float', ),
             ('--task-class-seed', 'seed used to do task class selection', 'integer'),
             ('--task-duration-seed', 'seed used to generate task duration', 'integer'),
             ('--task-arrival-seed', 'seed used to generate task arrivals', 'integer'),
             ('--task-arrival-mean', 'Mean task arrival rate', 'float'),
             ('--task-class', 'defines a task class, 4 values are needed: name probability time', 'string float int')
             ]

algorithms_map = {'random':random_schedule,
                  'least_full':least_full,
                  'round_robin':round_robin,
                  'fill_queue':fill_queue}

def usage():
    string = 'USAGE:\n'
    global arguments
    for arg in arguments:
        string = string + ('Argument: %s (%s) - type: %s\n' % arg)
        
    string += '\nArguments are passed as follow: simgrid.py --argument-name value'
    return string

def parse_args(scenario):
    import sys
    if len(sys.argv) == 1:
        #we have only one argument, return (we use default values)
        return
    
    args = sys.argv[1:]
    if len(args) == 1 and 'help' in args[0]:
        print usage()
        sys.exit()
    
    task_classes = []
    index = 0
    while index < len(args):
        if args[index] == '--grid-size':
            value = int(args[index+1])
            if value <= 0:
                raise Exception, '--grid-size must be positive'
            scenario.grid_description = [(value,1)]
            index += 2
        
        elif args[index] == '--scheduling-algorithm':
            scenario.schedule_algorithm = algorithms_map[args[index+1]]
            index += 2
            
        elif args[index] == '--scheduler-qs':
            value = int(args[index+1])
            if value <= 0:
                raise Exception, '--scheduler-qs must be positive'
            scenario.scheduler_queue_size = value
            index += 2
            
        elif args[index] == '--machine-qs':
            value = int(args[index+1])
            if value <= 0:
                raise Exception, '--machine-qs must be positive'
            scenario.machine_queue_size = value
            index += 2
        
        elif args[index] == '--scheduler-ht':
            value = float(args[index+1])
            if value <= 0:
                raise Exception, '--scheduler-ht must be positive'
            scenario.scheduler_hold_time = value
            index += 2

        elif args[index] == '--task-class-seed':
            value = int(args[index+1])
            if value <= 0:
                raise Exception, '--task-class-seed must be positive'
            scenario.task_class_selector_seed = value
            index += 2
            
        elif args[index] == '--task-duration-seed':
            value = int(args[index+1])
            if value <= 0:
                raise Exception, '--task-duration-seed must be positive'
            scenario.task_duration_seed = value
            index += 2
            
        elif args[index] == '--task-arrival-seed':
            value = int(args[index+1])
            if value <= 0:
                raise Exception, '--task-arrival-seed must be positive'
            scenario.task_arrival_seed = value
            index += 2
            
        elif args[index] == '--task-arrival-mean':
            value = float(args[index+1])
            if value <= 0:
                raise Exception, '--task-arrival-mean must be positive'
            scenario.task_arrival_mean = value
            index += 2
            
        elif args[index] == '--task-class':
            name = args[index+1]
            prob = float(args[index+2])
            mintime = int(args[index+3])
            maxtime = int(args[index+4])
            task_classes.append((name, prob, mintime, maxtime))
            index+=5

        else:
            raise Exception, 'Unknown option:' + str(args[index])
        
        if len(task_classes) > 0:
            scenario.task_distribution = task_classes

def makeGraphs(scenario):
    plt=SimPlot()
#    plt.plotHistogram(scenario.monitors['N'].histogram(low=0.0, high=100, nbins=30), xlab="tempo", ylab="tasks no sistema")
#
#    plt.root.title("Tasks arrived and tasks finished")
#    lineA=plt.makeLine(scenario.monitors['A'],color='blue')
#    lineC=plt.makeLine(scenario.monitors['C'],color='red')
    #lineN=plt.makeLine(scenario.monitors['N'],color='green')
#    obj=plt.makeGraphObjects([lineA, lineC])
#    frame=Frame(plt.root)
#    graph=plt.makeGraphBase(frame,1024,768,title="Chegadas[azul], Saidas[vermelho], Fregueses no sistema[verde]")
#    graph.pack()
#    graph.draw(obj)
#    frame.pack()
    
    plt.root.title("Tasks in the system")
    lineN=plt.makeLine(scenario.machineList[0].monitors['N'],color='red')
    obj=plt.makeGraphObjects([lineN])
    frame=Frame(plt.root)
    graph=plt.makeGraphBase(frame,1024,768,title="Tasks in the system")
    graph.pack()
    graph.draw(obj)
    frame.pack()
    
    #graph.postscr() 

    plt.mainloop()
    
def operationalValidation(scenario, verbose):
    T=now()
    global total_leaving_tasks
    
    if verbose:
        print "***Operational Validation***"
        for mac in scenario.machineList:
            print '***', mac.name, '***'
            print 'current tasks =', len(mac.waitQ) + len(mac.activeQ)
            print 'Ai =', mac.A
            print 'Bi =', mac.monitors['B'].total()
            print 'Ci =', mac.C
            print 'Ui =', mac.monitors['B'].total()/float(T)
            print 'Xi =', mac.C/float(T)
            print 'Si =', mac.monitors['B'].total()/mac.C
            print 'lambda-i =', mac.A/float(T)
            print 'Vi =', mac.C/scenario.total_leaving_tasks
            print 'N =', mac.monitors['N'].timeAverage()
            print 'T =', mac.monitors['T'].mean()
        
        print '***System as a whole***'
        print 't =', T
        print 'Ao = ', scenario.scheduler.A
        print 'lambda = ', float(scenario.scheduler.A)/T
        print 'Co = ', scenario.total_leaving_tasks
        print 'Xo = ', float(scenario.total_leaving_tasks)/T
        print 'N =', scenario.monitors['N'].timeAverage()
        print 'T =', scenario.monitors['T'].mean()
    
    #TODO calcular o num. tasks no sistema

def run(scenario, verbose=True):
    scenario.init_objects()
    initialize()
    
    taskGenerator = TaskGenerator(scenario)
    activate(taskGenerator, taskGenerator.run(scenario.sim_time))
       
    simulate(until=scenario.sim_time)
    
    if verbose:
        print "Total tasks:", scenario.total_arriving_tasks
        print "task arrival seed: ", scenario.task_arrival_seed
        print "task class seed: ", scenario.task_class_selector_seed
        print "task duration seed: ", scenario.task_duration_seed
    
    #makeGraphs(scenario)
    operationalValidation(scenario, verbose)
    return scenario, now()

def main():
    scenario = GridSimScenario()
    parse_args(scenario)
    return run(scenario)
    
if __name__ == '__main__':
    main()

