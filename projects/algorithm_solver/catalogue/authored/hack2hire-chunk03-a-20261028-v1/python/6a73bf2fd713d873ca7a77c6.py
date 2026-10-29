"""Hack2Hire 6a73bf2fd713d873ca7a77c6 (Largest Consecutive Skill Team) over an INFERRED spec; qualification unknown."""
from collections import Counter


def solve(skills):
    count = Counter(skills)
    best = 0
    for level in count:
        if level - 1 in count:
            continue
        size, current = 0, level
        while current in count:
            size += count[current]
            current += 1
        best = max(best, size)
    return best


class Solution:
    def largestTeam(self, skills):
        return solve(skills)
