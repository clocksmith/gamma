"""Hack2Hire 68d30311d490dee995152f5b (Weighted Cache) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown."""

import heapq


class WeightedCache:
    def __init__(self, maxTotalWeight):
        self.limit = maxTotalWeight
        self.items = {}
        self.heap = []
        self.total = 0
        self.clock = 0

    def put(self, key, value, weight):
        self.clock += 1
        old = self.items.get(key)
        if old is not None:
            self.total -= old[1]
        self.items[key] = (value, weight, self.clock)
        self.total += weight
        heapq.heappush(self.heap, (-weight, self.clock, key))
        while self.total > self.limit:
            negative, stamp, victim = heapq.heappop(self.heap)
            item = self.items.get(victim)
            if item is not None and item[2] == stamp:
                del self.items[victim]
                self.total += negative

    def get(self, key):
        item = self.items.get(key)
        return -1 if item is None else item[0]


def solve(operation_names, argument_lists):
    if operation_names[0] != 'WeightedCache' or len(argument_lists[0]) != 1:
        raise ValueError('exact initial constructor required')
    instance = WeightedCache(*argument_lists[0])
    allowed = {'put', 'get'}
    voids = {'put'}
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in allowed:
            raise ValueError('unknown method')
        value = getattr(instance, name)(*arguments)
        result.append(None if name in voids else value)
    return result
