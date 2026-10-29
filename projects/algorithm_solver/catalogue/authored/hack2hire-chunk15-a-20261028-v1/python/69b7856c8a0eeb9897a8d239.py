"""Hack2Hire 69b7856c8a0eeb9897a8d239 (Car Fleet Scheduler, variant 1 of 2) over an INFERRED spec; qualification unknown."""

import heapq


def solve(leases):
    order = sorted(range(len(leases)), key=lambda i: (leases[i][0], i))
    busy, free, result, cars = [], [], [0] * len(leases), 0
    for i in order:
        start, end = leases[i]
        while busy and busy[0][0] <= start:
            heapq.heappush(free, heapq.heappop(busy)[1])
        if free:
            car = heapq.heappop(free)
        else:
            cars += 1
            car = cars
        heapq.heappush(busy, (end, car))
        result[i] = car
    return result


class Solution:
    def assignCars(self, leases):
        return solve(leases)
