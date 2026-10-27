# Original candidate; contract and evidence: ../batch1/manifest.json
import heapq


class TaskManager:
    def __init__(self, tasks):
        self.tasks = {}
        self.heap = []
        self.version = 0
        for user, task, priority in tasks:
            self.add(user, task, priority)

    def add(self, userId, taskId, priority):
        self.version += 1
        self.tasks[taskId] = (userId, priority, self.version)
        heapq.heappush(self.heap, (-priority, -taskId, self.version))

    def edit(self, taskId, newPriority):
        self.add(self.tasks[taskId][0], taskId, newPriority)

    def rmv(self, taskId):
        del self.tasks[taskId]

    def execTop(self):
        while self.heap:
            priority, neg_task, version = heapq.heappop(self.heap)
            task = -neg_task
            current = self.tasks.get(task)
            if current is not None and current[2] == version:
                del self.tasks[task]
                return current[0]
        return -1


def solve(operations, arguments):
    manager = None
    answers = []
    for operation, args in zip(operations, arguments):
        if operation == 'TaskManager':
            manager = TaskManager(*args)
            answers.append(None)
        else:
            answers.append(getattr(manager, operation)(*args))
    return answers
