"""Hack2Hire 6a4fae98665efda9311f5607 (Array Frequency Sort, variant 1) over an INFERRED spec; qualification unknown."""

def solve(items):
    counts = {}
    for value in items:
        counts[value] = counts.get(value, 0) + 1
    result = []
    for value in sorted(counts, key=lambda v: (counts[v], v)):
        result.extend([value] * counts[value])
    return result


class Solution:
    def frequencySort(self, items):
        return solve(items)
