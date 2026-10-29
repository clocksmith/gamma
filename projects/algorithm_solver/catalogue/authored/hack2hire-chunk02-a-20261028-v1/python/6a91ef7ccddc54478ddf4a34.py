"""Hack2Hire 6a91ef7ccddc54478ddf4a34 (Highest Average Score); INFERRED spec; qualification unknown."""


def solve(scores):
    totals = {}
    for name, score in scores:
        entry = totals.setdefault(name, [0, 0])
        entry[0] += int(score); entry[1] += 1
    best = None
    for total, count in totals.values():
        if best is None or total * best[1] > best[0] * count: best = (total, count)
    return 0 if best is None else best[0] // best[1]


class Solution:
    def highestAverageScore(self, scores):
        return solve(scores)
