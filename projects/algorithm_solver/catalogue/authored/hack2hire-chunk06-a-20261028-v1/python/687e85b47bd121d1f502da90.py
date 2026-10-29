"""Hack2Hire 687e85b47bd121d1f502da90 (Find Smallest Hub) over an INFERRED spec; qualification unknown."""


def solve(capacities, intervals, requiredCapacity, taskInterval):
    colon = taskInterval.index(':')
    start, end = int(taskInterval[:colon]), int(taskInterval[colon + 1:])
    best = -1
    for i, capacity in enumerate(capacities):
        if capacity < requiredCapacity or (best >= 0 and capacity >= capacities[best]):
            continue
        free = True
        for booking in intervals[i]:
            colon = booking.index(':')
            if int(booking[:colon]) <= end and start <= int(booking[colon + 1:]):
                free = False
                break
        if free:
            best = i
    return best


class Solution:
    def findSmallestHub(self, capacities, intervals, requiredCapacity, taskInterval):
        return solve(capacities, intervals, requiredCapacity, taskInterval)
