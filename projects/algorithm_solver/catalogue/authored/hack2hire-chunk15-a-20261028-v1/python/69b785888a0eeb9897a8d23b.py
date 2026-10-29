"""Hack2Hire 69b785888a0eeb9897a8d23b (Car Fleet Scheduler, variant 2 of 2) over an INFERRED spec; qualification unknown."""

import heapq


def solve(leases, cars):
    order = sorted(range(len(leases)), key=lambda i: (leases[i][0], i))
    busy, free, result = [], list(range(1, cars + 1)), [0] * len(leases)
    for i in order:
        start, end = leases[i]
        while busy and busy[0][0] <= start:
            heapq.heappush(free, heapq.heappop(busy)[1])
        if free:
            car = heapq.heappop(free)
            heapq.heappush(busy, (end, car))
            result[i] = car
        else:
            result[i] = -1
    return result


class Solution:
    def assignCarsLimited(self, leases, cars):
        return solve(leases, cars)
