"""Hack2Hire 6ab32819e74ebb7457a3f0f5 (Fault-Tolerant Work Queue, level 1) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown."""
from collections import deque
import heapq


class WorkQueue:
    def __init__(self, taskIds, leaseDuration, maxAttempts):
        self.lease = leaseDuration
        self.cap = maxAttempts
        self.position = {t: i for i, t in enumerate(taskIds)}
        self.attempts = dict.fromkeys(taskIds, 0)
        self.holder = {}
        self.heap = []
        self.seq = 0
        self.dead = []
        self.dead_set = set()
        self.ready = deque(taskIds)

    def _release(self, task):
        if self.attempts[task] < self.cap:
            self.ready.append(task)
        else:
            self._kill(task)

    def _kill(self, task):
        self.dead_set.add(task)
        self.dead.append(task)


    def _expire(self, time):
        heap = self.heap
        while heap and heap[0][0] <= time:
            _, seq, task = heapq.heappop(heap)
            if self.holder.get(task) == seq:
                del self.holder[task]
                self._release(task)

    def reserve(self, time):
        self._expire(time)
        if not self.ready:
            return -1
        task = self.ready.popleft()
        self.attempts[task] += 1
        self.seq += 1
        self.holder[task] = self.seq
        heapq.heappush(self.heap, (time + self.lease, self.seq, task))
        return task

    def complete(self, time, taskId):
        self._expire(time)
        if taskId not in self.holder:
            return False
        del self.holder[taskId]

        return True

    def fail(self, time, taskId):
        self._expire(time)
        if taskId not in self.holder:
            return False
        del self.holder[taskId]
        self._release(taskId)
        return True

    def getDeadLetters(self, time):
        self._expire(time)
        return list(self.dead)


def solve(operation_names, argument_lists):
    if operation_names[0] != 'WorkQueue' or len(argument_lists[0]) != 3:
        raise ValueError('exact initial constructor required')
    instance = WorkQueue(*argument_lists[0])
    allowed = ['reserve', 'complete', 'fail', 'getDeadLetters']
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in allowed:
            raise ValueError('unknown method')
        result.append(getattr(instance, name)(*arguments))
    return result
