"""Hack2Hire 6a8664a4701a76fc6843b36e (Maximum Testing Efficiency) over an INFERRED spec; qualification unknown."""

def solve(arrivalTime):
    times = sorted(arrivalTime)
    best, run, prev, i = None, 0, None, 0
    while i < len(times):
        t, count = times[i], 0
        while i < len(times) and times[i] == t:
            count += 1
            i += 1
        run = count if prev is None else count + max(0, run - (t - prev))
        prev = t
        if best is None or run > best:
            best = run
    return best


class Solution:
    def maxTestingEfficiency(self, arrivalTime):
        return solve(arrivalTime)
