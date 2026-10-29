"""Hack2Hire 68eabd503a3bb8f8354249a7 (Black Cell Covering Block List) over an INFERRED spec; qualification unknown."""


def solve(m, n, coordinates):
    counts = {}
    for x, y in coordinates:
        for a in (x - 1, x):
            if 0 <= a < m - 1:
                for b in (y - 1, y):
                    if 0 <= b < n - 1:
                        key = a * n + b
                        counts[key] = counts.get(key, 0) + 1
    lists = [[], [], [], []]
    for key in sorted(counts):
        lists[counts[key] - 1].append([key // n, key % n])
    return lists


class Solution:
    def blackBlockLists(self, m, n, coordinates):
        return solve(m, n, coordinates)
