"""Hack2Hire 67730b5ddd9437f8aa275b04 (Write Disk Block With Cycle) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown."""

import heapq


class DiskBlockManager:
    def __init__(self, n, maximumCycles):
        # min-heap of (remaining writes, block id) over blocks that can still be written
        self.heap = [(maximumCycles, i) for i in range(n)]
        heapq.heapify(self.heap)

    def write(self):
        if not self.heap:
            return -1
        left, block = self.heap[0]
        if left == 1:
            heapq.heappop(self.heap)
        else:
            heapq.heapreplace(self.heap, (left - 1, block))
        return block


def solve(operation_names, argument_lists):
    if operation_names[0] != 'DiskBlockManager' or len(argument_lists[0]) != 2:
        raise ValueError('exact initial constructor required')
    instance = DiskBlockManager(*argument_lists[0])
    allowed = {'write'}
    voids = set()
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in allowed:
            raise ValueError('unknown method')
        value = getattr(instance, name)(*arguments)
        result.append(None if name in voids else value)
    return result
