"""Hack2Hire 68f6f36986f7cb4953d40fbc (Game Machine) over an INFERRED spec; qualification unknown."""

def solve(energyCosts, points, initialEnergy):
    n = len(energyCosts)
    end, cost, score, best = 0, 0, 0, None
    for start in range(n):
        if end < start:
            end, cost, score = start, 0, 0
        while end < n and cost + energyCosts[end] <= initialEnergy:
            cost += energyCosts[end]
            score += points[end]
            end += 1
        best = score if best is None or score > best else best
        if end > start:
            cost -= energyCosts[start]
            score -= points[start]
    return best


class Solution:
    def maxGamePoints(self, energyCosts, points, initialEnergy):
        return solve(energyCosts, points, initialEnergy)
