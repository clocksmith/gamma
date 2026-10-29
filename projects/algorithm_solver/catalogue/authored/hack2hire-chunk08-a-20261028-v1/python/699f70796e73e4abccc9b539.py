"""Hack2Hire 699f70796e73e4abccc9b539 (Priority Expiry LRU Cache) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown."""

import heapq


class PriorityExpiryLRUCache:
    def __init__(self, capacity):
        self.capacity = capacity
        self.items = {}  # key -> [value, priority, expiryTime, access stamp]
        self.by_expiry = []
        self.by_priority = []
        self.clock = 0

    def _touch(self, key, item):
        self.clock += 1
        item[3] = self.clock
        heapq.heappush(self.by_expiry, (item[2], self.clock, key))
        heapq.heappush(self.by_priority, (item[1], self.clock, key))

    def _top(self, heap):
        while heap:
            entry = heap[0]
            item = self.items.get(entry[2])
            if item is not None and item[3] == entry[1]:
                return entry
            heapq.heappop(heap)
        return None

    def get(self, key, currentTime):
        item = self.items.get(key)
        if item is None:
            return -1
        if item[2] <= currentTime:
            del self.items[key]
            return -1
        self._touch(key, item)
        return item[0]

    def set(self, key, value, priority, expiryTime, currentTime):
        item = self.items.get(key)
        if item is None:
            if len(self.items) == self.capacity:
                top = self._top(self.by_expiry)
                victim = top[2] if top[0] <= currentTime else self._top(self.by_priority)[2]
                del self.items[victim]
            item = [value, priority, expiryTime, 0]
            self.items[key] = item
        else:
            item[0], item[1], item[2] = value, priority, expiryTime
        self._touch(key, item)


def solve(operation_names, argument_lists):
    if operation_names[0] != 'PriorityExpiryLRUCache' or len(argument_lists[0]) != 1:
        raise ValueError('exact initial constructor required')
    instance = PriorityExpiryLRUCache(*argument_lists[0])
    allowed = {'get', 'set'}
    voids = {'set'}
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in allowed:
            raise ValueError('unknown method')
        value = getattr(instance, name)(*arguments)
        result.append(None if name in voids else value)
    return result
