"""Hack2Hire 686833a90ed1b6fe83428ac3 (Minimize Cost with Vouchers) over an INFERRED spec; qualification unknown."""

import heapq


def solve(price, vouchersCount):
    heap = [-p for p in price]
    heapq.heapify(heap)
    total = sum(price)
    for _ in range(vouchersCount):
        if not heap or heap[0] == 0:
            break
        top = -heap[0]
        total -= top - top // 2
        heapq.heapreplace(heap, -(top // 2))
    return total


class Solution:
    def minimizeCost(self, price, vouchersCount):
        return solve(price, vouchersCount)
