"""This module provides a framework for the creation of behavior trees"""

from random import shuffle
from time import time

class Node():
    """Base class for all nodes in a behavior tree"""

    def __init__(self):
        """Nodes have one of three statuses once is active: running, failure or 
        success. When it's just created the status is inactive"""
        self._status = 'inactive'

    def get_status(self):
        return self._status

    def setup(self):
        """Called when an inactive node starts for the first time"""
        pass

    def run(self):
        """Main process to be executed with each tick of the tree"""
        pass

    def deactivate(self):
        self._status = 'inactive'

class Root(Node):
    """A Root node is the first node in a behavior tree, they only serve as a 
    nexus and starting point for the tree. All nodes contain a reference to the 
    root. The root keeps the blackboard where all nodes share data. The root 
    Maintains a reference to the currently running node. 
    Roots only have one child node"""

    def __init__(self):
        super().__init__()
        self.blackboard = {'checks':{}, 'delete':[]}
        self._active = None
        self._child = None
    
    def setup(self):
        self._status = 'running'
        self._child.setup(self)
    
    def run(self):
        """Before the normal behavior for run, before the tick, we check if any
        of the triggers set in the checks dictionary returns true, if not
        everything works as normal, if it does then the node that set the check
        is ran and the check is deleted"""
        for node, check in self.blackboard['checks'].items():
            if check():
                node.run()
                self.push_stack('delete', node) #Revisar en el futuro si dos timers
                                                #darian un problema
        
        """Since the size of a dictionary can't be change mid iteration, when a 
        check is used it can't be deleted immediatly, we push it to the delete 
        stack and if there are elements in the delete stack this next loop will
        make sure they are deleted"""
        if self.blackboard['delete']:
            for node in self.blackboard['delete']:
                del self.blackboard['checks'][node]
            self.blackboard['delete'] = []


        """If the child node is still running then we check wheter the active
        node is also still running, if it is we tick it again if not we run the
        child, because then the whole tree gets ticked and a new active will be
        set. If the child node has finished then the node sets its new status"""
        if self._child.get_status() == 'running':
            if self._active != 'running':
                self._child.run()
            else:
                self.active.run()
        else:
            self._status = self._child.get_status()        

    def add_child(self, node:Node):
        self._child = node

    def add_check(self, node:Node, check):
        self.blackboard['checks'][node] = check

    def del_check(self, node:Node):
        del self.blackboard['checks'][node]

    def set_active(self, node:Node):
        self._active = node

    def set_value(self, name, value):
        self.blackboard[name] = value

    def get_value(self, name):
        return self.blackboard[name]

    def push_stack(self, name, value):
        if not self.blackboard[name]:
            self.blackboard[name] = [value]
        elif isinstance(self.blackboard[name], list):
            self.blackboard[name].append(value)
        else:
            raise Exception("New stack name alraedy in use in the blackboard")

    def pop_stack(self, name):
        if not self.blackboard[name] or len(self.blackboard[name]) == 0:
            return None
        else:
            return self.blackboard[name].pop()
    
    def flush_stack(self, name):
        if not self.blackboard[name] or len(self.blackboard[name]) == 0:
            None
        else:
            del self.blackboard[name]
            return True

class Composite(Node):
    """Composites define the flow of the behavior tree, they have many child 
    nodes. The type of composite will determine how they are run and what status
    is returned back up"""

    def __init__(self):
        super().__init__()
        self._childs = []
        self._root = None

    def setup(self, root:Root):
        if not self._childs: #Design problem if a composite has no child nodes
            raise Exception("Childless composite node")
        self._status = 'running'
        self._root = root
        self._root.set_active(self._childs[0])                    
        self._childs[0].setup(self._root)

    def add_child(self, node:Node):
        self._childs.append(node)

    def clean_up(self):
        for node in self._childs:
            node.deactivate()

class Sequence(Composite):

    def __init__(self):
        super().__init__()

    def run(self):
        """When a sequence runs through its childs it will fail whenever any 
        node fails, and will only succeed when the last node succeeds. The for
        breaks at every case because if any of the conditions are true we don't 
        need to go for the next child. the for only moves forward when any child
        (but not the last) has a success status"""
        for node in self._childs:
            #If a child is inactive it means it's its first time running so it 
            #needs to be setup and set as the new active for the root to run
            if node.get_status() == 'inactive':  
                self._root.set_active(node)
                node.setup(self._root)
                node.run()
                break
            elif node.get_status() == 'running':
                node.run()
                break
            elif node.get_status() == 'failure':
                self._status = 'failure'
                self.clean_up()
                break
            elif node.get_status() == 'success' and node == self._childs[-1]:
                self._status = 'success'
                self.clean_up()
                break
            else:
                next #This is completely unnecessary, but better have it to
            #understand what is really going on, if none of the conditionals run
            #then we just move on to the next node.

class RandomSequence(Sequence):
    def __init__(self):
        super().__init__()

    def setup(self, root:Root):#Everytime the composite is setup the child order
        shuffle(self._childs) #gets shuffled, that way it's no longer in order
        super().setup(root)

class Selector(Composite):

    def __init__(self):
        super().__init__()

    def run(self):
        """Extremely similar to a sequence, but a selector works inversly, 
        as soon as a node succeeds the selector succeeds, if one fails it moves
        to the next"""
        for node in self._childs:
            #If a child is inactive it means it's its first time running so it 
            #needs to be setup and set as the new active for the root to run
            if node.get_status() == 'inactive':  
                self._root.set_active(node)
                node.setup(self._root)
                node.run()
                break
            elif node.get_status() == 'running':
                node.run()
                break
            elif node.get_status() == 'success':
                self._status = 'success'
                self.clean_up()
                break
            elif node.get_status() == 'failure' and node == self._childs[-1]:
                self._status = 'failure'
                self.clean_up()
                break
            else:
                next #This is completely unnecessary, but better have it to
            #understand what is really going on, if none of the conditionals run
            #then we just move on to the next node.

class RandomSelector(Selector):
    def __init__(self):
        super().__init__()

    def setup(self, root:Root):#Everytime the composite is setup the child order
        shuffle(self._childs) #gets shuffled, that way it's no longer in order
        super().setup(root)

class Decorator(Node):
    """Decorators only have one child, the status they return will depend on the
    child node status"""

    def __init__(self):
        super().__init__()
        self._child = None
        self._root = None

    def setup(self, root:Root):
        if not self._child: #Design problem if a decorator has no child nodes
            raise Exception("Childless decorator node") 
        self._status = 'running'
        self._root = root

        """After linking the root and setting the running status, we set the 
        child as active and call setup, if this will end up being the active
        then it'll be the active, if not setup will find the active down 
        the line"""
        self._root.set_active(self._child)                    
        self._child.setup(self._root)

    def add_child(self, node:Node):
        self._child = node

class Inverter(Decorator):
    def __init__(self):
        super().__init__()

    def run(self): #Simple, inverts the result of the child
        if self._child.get_status() == 'running':
            self._child.run()
        elif self._child.get_status() == 'success':
            self._child.deactivate()
            self._status = 'failure'
        else:
            self._child.deactivate()
            self._status = 'success'

class Succeeder(Decorator):
    def __init__(self):
        super().__init__()

    def run(self): #No matter what the child returns, this succeeds
        if self._child.get_status() == 'running':
            self._child.run()
        else:
            self._child.deactivate()
            self._status = 'success'

class UntilFail(Decorator):
    def __init__(self):
        super().__init__()
    
    def run(self): #Will continue repeating the child until it fails
        if self._child.get_status() == 'running':
            self._child.run()
        elif self._child.get_status() == 'success':
            self._child.setup(self._root)
            self._child.run()
        else:
            self._child.deactivate()
            self._status = 'success'

class ManualRepeater(Decorator):
    def __init__(self, times:int):
        super().__init__()
        self.times = times
        self._current = times

    def setup(self):
        self._current = self.times
        super().__init__()

    def run(self):
        if self._child.get_status() == 'running':
            self._child.run()
        else:
            self._current -= 1
            if self._current > 0:
                self._child.setup()
                self._child.run()
            else:
                self._child.deactivate()
                self._status = 'success'

class ManualTimer(Decorator):
    """The timer node runs the child node until the time runs out, if it runs
    out of time it fails, if not then whatever status the child has will be the
    new status of the node. This Manual Timer has the time in seconds set when
    the tree is created, unlike the other which could be set at runtime"""
    def __init__(self, seconds):
        super().__init__()
        self.seconds = seconds #time limit
        self.initial_time = 0

    def setup(self, root):
        super().setup(root)
        self.initial_time = time() #When the node is setup it will record that
                                   #moment as the starting time for the timer
        self._root.add_check(self, self.check_time)
        """The root node itself will check before each tick if the time has run
        out and when this happens the whole tree is ran, so that the timer does
        its job. This function adds a function to check the time to the board"""

    def check_time(self):#returns true if the time has run out
        return (time() - self.initial_time) >= self.seconds

    def run(self):
        if self.check_time():
            self._status = 'failure'
            self._child.deactivate()
        elif self._child.get_status() == 'running':
            self._child.run()
        else:
            self._status = self._child.get_status()
            self._child.deactivate()

class Leaf(Node):
    """Leaves contain the main behavior nodes, which realize actions and 
    evaluate variables"""

    def __init__(self):
        super().__init__()
        self._root = None

    def setup(self, root:Root):
        self._status = 'running'
        self._root = root
        self._root.set_active(self) #Since leaves are at the end of the tree
                           #it's safe to set them as active when they get setup                   