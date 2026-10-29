"""Original frontend 249 variant; qualification unknown."""

from collections import defaultdict


def solve(strings):
    groups = defaultdict(list)
    for s in strings:
        base = ord(s[0])
        key = tuple((ord(c) - base) % 26 for c in s)
        groups[key].append(s)
    return list(groups.values())


groupStrings = solve


class Solution:
    def groupStrings(self, strings):
        return solve(strings)
