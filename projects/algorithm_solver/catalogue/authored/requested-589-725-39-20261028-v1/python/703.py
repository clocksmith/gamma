"""Original LeetCode 703 candidate; qualification unknown."""

import heapq

class KthLargest:
    def __init__(self, k, nums):
        self.k, self.heap = k, list(nums)
        heapq.heapify(self.heap)
        while len(self.heap) > k: heapq.heappop(self.heap)
    def add(self, val):
        if len(self.heap) < self.k: heapq.heappush(self.heap, val)
        elif val > self.heap[0]: heapq.heapreplace(self.heap, val)
        return self.heap[0]


def solve(operations, arguments):
    instance = KthLargest(*arguments[0])
    result = [None]
    for operation, values in zip(operations[1:], arguments[1:]):
        result.append(getattr(instance, operation)(*values))
    return result
