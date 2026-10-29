"""Hack2Hire 678d6982fa7ce9616e190fb3 (Interleave Iterator with Cycle) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown."""
from collections import deque


class InterleaveIterator:
    def __init__(self, arrays, cycle):
        self.arrays = [list(a) for a in arrays if a]
        self.cycle = cycle
        self.queue = deque((i, 0) for i in range(len(self.arrays)))

    def hasNext(self):
        return bool(self.queue) or (self.cycle and bool(self.arrays))

    def next(self):
        if not self.queue:
            if not (self.cycle and self.arrays):
                return None
            self.queue = deque((i, 0) for i in range(len(self.arrays)))
        i, position = self.queue.popleft()
        values = self.arrays[i]
        if position + 1 < len(values):
            self.queue.append((i, position + 1))
        return values[position]


def solve(operation_names, argument_lists):
    if operation_names[0] != 'InterleaveIterator' or len(argument_lists[0]) != 2:
        raise ValueError('exact initial constructor required')
    instance = InterleaveIterator(*argument_lists[0])
    allowed = ['hasNext', 'next']
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in allowed:
            raise ValueError('unknown method')
        result.append(getattr(instance, name)(*arguments))
    return result
