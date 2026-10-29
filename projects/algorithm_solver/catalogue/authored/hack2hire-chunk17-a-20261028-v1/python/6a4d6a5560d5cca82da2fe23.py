"""Hack2Hire 6a4d6a5560d5cca82da2fe23 (Typed Task Lock) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown."""

from collections import deque


class MutexTaskLock:
    def __init__(self):
        self.running = 0
        self.kind = None
        self.waiting = deque()  # (jobId, jobType) in arrival order

    def acquire(self, jobId, jobType):
        if not self.waiting and (self.running == 0 or self.kind == jobType):
            self.running += 1
            self.kind = jobType
            return True
        self.waiting.append((jobId, jobType))
        return False

    def release(self, jobId):
        self.running -= 1
        admitted = []
        if self.running == 0 and self.waiting:
            self.kind = self.waiting[0][1]
            while self.waiting and self.waiting[0][1] == self.kind:
                admitted.append(self.waiting.popleft()[0])
            self.running = len(admitted)
        return admitted


def solve(operation_names, argument_lists):
    if operation_names[0] != 'MutexTaskLock' or len(argument_lists[0]) != 0:
        raise ValueError('exact initial constructor required')
    instance = MutexTaskLock(*argument_lists[0])
    allowed = {'acquire', 'release'}
    voids = set()
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in allowed:
            raise ValueError('unknown method')
        value = getattr(instance, name)(*arguments)
        result.append(None if name in voids else value)
    return result
