"""Hack2Hire 679f09b9e818521cacd22471 (Job Scheduler) over an INFERRED spec; qualification unknown."""

from heapq import heappop, heappush


def solve(jobs):
    busy, free, machines, out = [], [], 0, []
    for job_id, hhmm, duration in jobs:
        start = int(hhmm[:2]) * 60 + int(hhmm[2:])
        while busy and busy[0][0] <= start:
            heappush(free, heappop(busy)[1])
        if free:
            machine = heappop(free)
        else:
            machines += 1
            machine = machines
        heappush(busy, (start + int(duration), machine))
        out.append([job_id, 'M' + str(machine)])
    return out


class Solution:
    def assignMachines(self, jobs):
        return solve(jobs)
