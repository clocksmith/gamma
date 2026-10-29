"""Original Hack2Hire 69dd8c3595e80ae213e5b9c7 native class variant over an INFERRED specification, with a separately declared trace adapter; qualification unknown."""


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

    def addDependency(self, taskId, dependsOnId):
        if taskId not in self.tasks or dependsOnId not in self.tasks or taskId == dependsOnId or (taskId, dependsOnId) in self.edges:
            return False
        self.edges.add((taskId, dependsOnId))
        self.requires[taskId].append(dependsOnId)
        return True

    def getDependencies(self, taskId):
        return list(self.requires.get(taskId, ()))


METHODS = ('add', 'get', 'updateStatus', 'addDependency', 'getDependencies')


def solve(operation_names, argument_lists):
    if operation_names[0] != 'ToDoList' or argument_lists[0] != []:
        raise ValueError('exact initial constructor required')
    instance, result = ToDoList(), [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in METHODS:
            raise ValueError('unknown method')
        result.append(getattr(instance, name)(*arguments))
    return result
