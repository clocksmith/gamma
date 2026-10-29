"""Hack2Hire 69efc8ea96981f58ae1f6d74 (Design a Task Assignment System, variant 1 of 4) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown."""


class TaskManager:
    def __init__(self):
        self.tasks = {}  # taskId -> [name, priority, creation number]
        self.count = 0

    def addTask(self, timestamp, name, priority):
        self.count += 1
        taskId = 'taskId%d' % self.count
        self.tasks[taskId] = [name, priority, self.count]
        return taskId

    def updateTask(self, timestamp, taskId, name, priority):
        task = self.tasks.get(taskId)
        if task is None:
            return False
        task[0], task[1] = name, priority
        return True

    def getTask(self, timestamp, taskId):
        task = self.tasks.get(taskId)
        return '' if task is None else '%s(%d)' % (task[0], task[1])


def solve(operation_names, argument_lists):
    if operation_names[0] != 'TaskManager' or len(argument_lists[0]) != 0:
        raise ValueError('exact initial constructor required')
    instance = TaskManager(*argument_lists[0])
    allowed = {'addTask', 'updateTask', 'getTask'}
    voids = set()
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in allowed:
            raise ValueError('unknown method')
        value = getattr(instance, name)(*arguments)
        result.append(None if name in voids else value)
    return result
