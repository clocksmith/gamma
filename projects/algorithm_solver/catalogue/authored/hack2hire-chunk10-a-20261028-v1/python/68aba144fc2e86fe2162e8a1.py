"""Hack2Hire 68aba144fc2e86fe2162e8a1 (Design Cache with Eviction, variant 2 of 2) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown."""

import heapq


class RankedCache:
    def __init__(self, capacity, source):
        self.capacity = capacity
        self.entries = {}  # key -> (value, rank, write sequence)
        self.heap = []  # (rank, write sequence, key); stale when the sequence no longer matches
        self.seq = 0
        self.source = {row[0]: (row[1], row[2]) for row in source}  # private copy of the data source
        self.loads = 0

    def _write(self, key, value, rank):
        self.seq += 1
        if key not in self.entries and len(self.entries) == self.capacity:
            while True:
                _, seq, victim = heapq.heappop(self.heap)
                entry = self.entries.get(victim)
                if entry is not None and entry[2] == seq:
                    del self.entries[victim]
                    break
        self.entries[key] = (value, rank, self.seq)
        heapq.heappush(self.heap, (rank, self.seq, key))

    def put(self, key, value, rank):
        self._write(key, value, rank)
        self.source[key] = (value, rank)  # write-through

    def get(self, key):
        entry = self.entries.get(key)
        if entry is not None:
            return entry[0]
        stored = self.source.get(key)
        if stored is not None:
            self.loads += 1
            self._write(key, stored[0], stored[1])
            return stored[0]
        return ''

    def getLoadCount(self):
        return self.loads


def solve(operation_names, argument_lists):
    if operation_names[0] != 'RankedCache' or len(argument_lists[0]) != 2:
        raise ValueError('exact initial constructor required')
    instance = RankedCache(*argument_lists[0])
    allowed = {'put', 'get', 'getLoadCount'}
    voids = {'put'}
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in allowed:
            raise ValueError('unknown method')
        value = getattr(instance, name)(*arguments)
        result.append(None if name in voids else value)
    return result
