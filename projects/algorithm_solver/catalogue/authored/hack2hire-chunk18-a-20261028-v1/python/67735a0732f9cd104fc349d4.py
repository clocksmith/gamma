"""Hack2Hire 67735a0732f9cd104fc349d4 (Maximize Task Scheduling Within Time Limit) over an INFERRED spec; qualification unknown."""

import heapq


def solve(n, m, tasks):
    slots = [0] * min(n * m, len(tasks))
    started = 0
    for duration in sorted(tasks):
        free = slots[0]
        if free + duration > 60:
            break
        heapq.heapreplace(slots, free + duration)
        started += 1
    return started


class Solution:
    def maxTasksWithinLimit(self, n, m, tasks):
        return solve(n, m, tasks)
