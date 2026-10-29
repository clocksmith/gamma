"""Hack2Hire 69b78e4e8a0eeb9897a8d2a5 (Garage Occupancy per Timestamp) over an INFERRED spec; qualification unknown."""


def solve(n, tickets):
    change = [0] * (n + 1)
    for entry, leave in tickets:
        change[entry] += 1
        change[leave + 1] -= 1
    result = []
    current = 0
    for t in range(n):
        current += change[t]
        result.append(current)
    return result


class Solution:
    def getOccupancy(self, n, tickets):
        return solve(n, tickets)
