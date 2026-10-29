"""Hack2Hire 6a04d7ad3141bbc31efdd5c2 (Minimum Machines for Task Scheduling) over an INFERRED spec; qualification unknown."""


def solve(tasks):
    starts = sorted(t[0] for t in tasks)
    ends = sorted(t[1] for t in tasks)
    best = j = 0
    for i, s in enumerate(starts):
        while ends[j] <= s:
            j += 1
        best = max(best, i + 1 - j)
    return best


class Solution:
    def minMachines(self, tasks):
        return solve(tasks)
