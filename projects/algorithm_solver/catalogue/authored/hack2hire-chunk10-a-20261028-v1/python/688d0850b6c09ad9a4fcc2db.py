"""Hack2Hire 688d0850b6c09ad9a4fcc2db (Design Cache with Eviction, variant 1 of 2) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown."""

import heapq


class RankedCache:
    def __init__(self, capacity):
        self.capacity = capacity
        self.entries = {}  # key -> (value, rank, write sequence)
        self.heap = []  # (rank, write sequence, key); stale when the sequence no longer matches
        self.seq = 0

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

    def get(self, key):
        entry = self.entries.get(key)
        if entry is not None:
            return entry[0]
        return ''


def solve(operation_names, argument_lists):
    if operation_names[0] != 'RankedCache' or len(argument_lists[0]) != 1:
        raise ValueError('exact initial constructor required')
    instance = RankedCache(*argument_lists[0])
    allowed = {'put', 'get'}
    voids = {'put'}
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in allowed:
            raise ValueError('unknown method')
        value = getattr(instance, name)(*arguments)
        result.append(None if name in voids else value)
    return result
