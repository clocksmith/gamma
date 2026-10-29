"""Hack2Hire 6a973a3a0ca9cc4e1c789e48 (Product of Maximum and Minimum) over an INFERRED spec; qualification unknown."""
import heapq


def solve(operations, x):
    count, low, high, result = {}, [], [], []
    for op, v in zip(operations, x):
        if op == 'push':
            count[v] = count.get(v, 0) + 1
            heapq.heappush(low, v)
            heapq.heappush(high, -v)
        else:
            count[v] -= 1
        while not count.get(low[0]): heapq.heappop(low)
        while not count.get(-high[0]): heapq.heappop(high)
        result.append(low[0] * -high[0])
    return result


class Solution:
    def maxMinProducts(self, operations, x):
        return solve(operations, x)
