"""Hack2Hire 68ae7b5ec8631a6568126dbe (Find Minimum Score Threshold) over an INFERRED spec; qualification unknown."""


def solve(games, threshold):
    total, lose = {}, {}
    for score, result in games:
        v = int(score)
        total[v] = total.get(v, 0) + 1
        if result == 'lose':
            lose[v] = lose.get(v, 0) + 1
    best, seen, lost = -1, 0, 0
    for v in sorted(total, reverse=True):
        seen += total[v]
        lost += lose.get(v, 0)
        if lost / seen >= threshold:  # IEEE double quotient, identical in both languages
            best = v
    return best


class Solution:
    def findMinimumScoreThreshold(self, games, threshold):
        return solve(games, threshold)
