"""Hack2Hire 69fa55d2661bab75bbca3b9d (Maximize Hole in Prison Gate); INFERRED spec; qualification unknown."""


def _longest_gap(removed):
    best = run = 0
    previous = None
    for bar in sorted(removed):
        run = run + 1 if previous is not None and bar == previous + 1 else 1
        best = max(best, run); previous = bar
    return best + 1


def solve(n, m, h, v):
    return _longest_gap(h) * _longest_gap(v)


class Solution:
    def maximizeHole(self, n, m, h, v):
        return solve(n, m, h, v)
