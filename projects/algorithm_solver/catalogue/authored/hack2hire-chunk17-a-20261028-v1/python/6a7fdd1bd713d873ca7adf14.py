"""Hack2Hire 6a7fdd1bd713d873ca7adf14 (Scooter Street Simulation) over an INFERRED spec; qualification unknown."""


def solve(finish, scooters):
    covered = 0
    reach = 0
    for s in sorted(p for p in scooters if p < finish):
        end = min(s + 10, finish)
        if end > reach:
            covered += end - max(s, reach)
            reach = end
    return finish - covered


class Solution:
    def minWalkingDistance(self, finish, scooters):
        return solve(finish, scooters)
