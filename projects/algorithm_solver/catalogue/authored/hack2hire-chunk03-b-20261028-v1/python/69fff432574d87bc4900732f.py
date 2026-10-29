"""Hack2Hire 69fff432574d87bc4900732f (Minimum Steps to Reorder Layers) over an INFERRED spec; qualification unknown."""


def solve(current, desired):
    position = {v: i for i, v in enumerate(desired)}
    kept = 1
    while kept < len(current) and position[current[kept]] > position[current[kept - 1]]:
        kept += 1
    return len(current) - kept


class Solution:
    def minOperations(self, current, desired):
        return solve(current, desired)
