"""Original Hack2Hire 69dd8d2795e80ae213e5b9cf native class variant over an INFERRED specification, with a separately declared trace adapter; qualification unknown."""
import heapq


class ToDoList:
    def __init__(self):
        self.tasks = {}
        self.requires = {}
        self.edges = set()

    def add(self, taskId, description, status):
        if taskId not in self.tasks:
            self.tasks[taskId] = [taskId, description, status]
            self.requires[taskId] = []

    def get(self, taskId):
        return list(self.tasks.get(taskId, ()))

    def updateStatus(self, taskId, status):
        if taskId not in self.tasks:
            return False
        self.tasks[taskId][2] = status
        return True

    def _reaches(self, start, target):
        seen, stack = {start}, [start]
        while stack:
            node = stack.pop()
            if node == target:
                return True
            for nxt in self.requires[node]:
                if nxt not in seen:
                    seen.add(nxt)
                    stack.append(nxt)
        return False

    def addDependency(self, taskId, dependsOnId):
        if taskId not in self.tasks or dependsOnId not in self.tasks or taskId == dependsOnId or (taskId, dependsOnId) in self.edges:
            return False
        if self._reaches(dependsOnId, taskId):
            return False
        self.edges.add((taskId, dependsOnId))
        self.requires[taskId].append(dependsOnId)
        return True

    def getDependencies(self, taskId):
        return list(self.requires.get(taskId, ()))

    def getExecutionOrder(self):
        waiting, dependents = {}, {task: [] for task in self.tasks}
        for task, prerequisites in self.requires.items():
            waiting[task] = len(prerequisites)
            for prerequisite in prerequisites:
                dependents[prerequisite].append(task)
        ready = [task for task, count in waiting.items() if count == 0]
        heapq.heapify(ready)
        order = []
        while ready:
            task = heapq.heappop(ready)
            order.append(task)
            for dependent in dependents[task]:
                waiting[dependent] -= 1
                if waiting[dependent] == 0:
                    heapq.heappush(ready, dependent)
        return order


METHODS = ('add', 'get', 'updateStatus', 'addDependency', 'getDependencies', 'getExecutionOrder')


def solve(operation_names, argument_lists):
    if operation_names[0] != 'ToDoList' or argument_lists[0] != []:
        raise ValueError('exact initial constructor required')
    instance, result = ToDoList(), [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in METHODS:
            raise ValueError('unknown method')
        result.append(getattr(instance, name)(*arguments))
    return result
