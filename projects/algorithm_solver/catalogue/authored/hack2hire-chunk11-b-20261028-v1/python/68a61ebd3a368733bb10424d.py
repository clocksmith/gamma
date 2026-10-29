"""Hack2Hire 68a61ebd3a368733bb10424d (Incremental Task Scheduler) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown."""

import heapq


class TaskScheduler:
    def __init__(self):
        self.prerequisites = {}  # added id -> its prerequisite list
        self.dependents = {}     # id (added or not) -> added tasks listing it

    def addTask(self, id, dependencies):
        if id in self.prerequisites:
            return False
        wanted = set(dependencies)
        if id in wanted:
            return False
        # a cycle appears exactly when a prerequisite already depends on id transitively
        seen = {id}
        stack = [id]
        while stack:
            v = stack.pop()
            for w in self.dependents.get(v, ()):
                if w in wanted:
                    return False
                if w not in seen:
                    seen.add(w)
                    stack.append(w)
        self.prerequisites[id] = list(dependencies)
        for d in dependencies:
            self.dependents.setdefault(d, []).append(id)
        return True

    def getExecutionOrder(self):
        remaining = {t: len(p) for t, p in self.prerequisites.items()}  # missing prerequisites never reach zero
        heap = [t for t, c in remaining.items() if c == 0]
        heapq.heapify(heap)
        order = []
        while heap:
            t = heapq.heappop(heap)
            order.append(t)
            for w in self.dependents.get(t, ()):
                remaining[w] -= 1
                if remaining[w] == 0:
                    heapq.heappush(heap, w)
        return order


def solve(operation_names, argument_lists):
    if operation_names[0] != 'TaskScheduler' or len(argument_lists[0]) != 0:
        raise ValueError('exact initial constructor required')
    instance = TaskScheduler(*argument_lists[0])
    allowed = {'addTask', 'getExecutionOrder'}
    voids = set()
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in allowed:
            raise ValueError('unknown method')
        value = getattr(instance, name)(*arguments)
        result.append(None if name in voids else value)
    return result
