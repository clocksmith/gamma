"""Hack2Hire 6a8615b8701a76fc6843aed0 (Maximum Balanced Task Assignment) over an INFERRED spec; qualification unknown."""


def solve(m, task):
    counts = {}
    for t in task:
        counts[t] = counts.get(t, 0) + 1
    usable = 0
    for c in counts.values():
        usable += c if c < m else m
    return m * (usable // m)


class Solution:
    def maxBalancedTasks(self, m, task):
        return solve(m, task)
