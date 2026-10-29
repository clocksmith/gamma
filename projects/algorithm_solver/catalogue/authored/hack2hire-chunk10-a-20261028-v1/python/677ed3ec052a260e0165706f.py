"""Hack2Hire 677ed3ec052a260e0165706f (Design Delayed Tasks Scheduler) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown."""

import heapq


class DelayedTaskScheduler:
    def __init__(self):
        self.heap = []  # (run time, sequence, task id)
        self.pending = {}  # task id -> sequence
        self.seq = 0

    def schedule(self, taskId, delayTime, currentTime):
        self.seq += 1
        run_at = currentTime + delayTime
        self.pending[taskId] = self.seq
        heapq.heappush(self.heap, (run_at, self.seq, taskId))
        return run_at

    def runDue(self, currentTime):
        done = []
        while self.heap and self.heap[0][0] <= currentTime:
            _, seq, task = heapq.heappop(self.heap)
            if self.pending.get(task) == seq:
                del self.pending[task]
                done.append(task)
        return done

    def cancel(self, taskId):
        if taskId in self.pending:
            del self.pending[taskId]  # its heap entry becomes stale
            return True
        return False


def solve(operation_names, argument_lists):
    if operation_names[0] != 'DelayedTaskScheduler' or len(argument_lists[0]) != 0:
        raise ValueError('exact initial constructor required')
    instance = DelayedTaskScheduler(*argument_lists[0])
    allowed = {'schedule', 'runDue', 'cancel'}
    voids = set()
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in allowed:
            raise ValueError('unknown method')
        value = getattr(instance, name)(*arguments)
        result.append(None if name in voids else value)
    return result
