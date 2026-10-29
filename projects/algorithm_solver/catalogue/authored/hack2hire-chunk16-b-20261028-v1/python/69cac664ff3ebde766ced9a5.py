"""Hack2Hire 69cac664ff3ebde766ced9a5 (Minimum Absolute Difference Pairs) over an INFERRED spec; qualification unknown."""


def solve(latencies):
    values = sorted(latencies)
    best = None
    for i in range(1, len(values)):
        gap = values[i] - values[i - 1]
        if best is None or gap < best:
            best = gap
    return [[values[i - 1], values[i]] for i in range(1, len(values)) if values[i] - values[i - 1] == best]


class Solution:
    def minimumAbsDifference(self, latencies):
        return solve(latencies)
