"""Hack2Hire 688102fcf96758aa78e1d67a (Find Minimal Shoppers). Spec inferred by claude-opus-5-5 subagent 2026-10-28; qualification unknown."""
import heapq


def solve(orders, maxAverageWait):
    n = len(orders)
    sequence = sorted(range(n), key=lambda i: (orders[i][1], i))

    def total_wait(shoppers):
        free, total = [0] * shoppers, 0
        for i in sequence:
            duration, arrival = orders[i]
            finish = max(free[0], arrival) + duration
            heapq.heapreplace(free, finish)
            total += finish - arrival
        return total

    limit = maxAverageWait * n
    if total_wait(n) > limit:
        return -1
    low, high = 1, n
    while low < high:
        middle = (low + high) // 2
        if total_wait(middle) <= limit:
            high = middle
        else:
            low = middle + 1
    return low


class Solution:
    def minShoppers(self, orders, maxAverageWait):
        return solve(orders, maxAverageWait)
