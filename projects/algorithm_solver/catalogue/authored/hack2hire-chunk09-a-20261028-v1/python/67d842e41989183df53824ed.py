"""Hack2Hire 67d842e41989183df53824ed (Build the Longest Spike) over an INFERRED spec; qualification unknown."""


def solve(arr):
    if not arr:
        return 0
    count = {}
    for v in arr:
        count[v] = count.get(v, 0) + 1
    peak = max(count)
    return 1 + sum(2 if c >= 2 else 1 for v, c in count.items() if v != peak)


class Solution:
    def longestSpike(self, arr):
        return solve(arr)
