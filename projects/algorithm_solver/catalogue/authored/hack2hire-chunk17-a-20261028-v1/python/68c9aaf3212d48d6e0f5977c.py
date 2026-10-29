"""Hack2Hire 68c9aaf3212d48d6e0f5977c (Thrilling Teleporters, variant 1 of 2) over an INFERRED spec; qualification unknown."""


def solve(teleporters, dieSides, currentSquare, lastSquare):
    jump = {}
    for entry in teleporters:
        a, b = entry.split(',')
        jump[int(a)] = int(b)
    ends = set()
    for roll in range(1, dieSides + 1):
        land = currentSquare + roll
        ends.add(lastSquare if land >= lastSquare else jump.get(land, land))
    return sorted(ends)


class Solution:
    def possibleDestinations(self, teleporters, dieSides, currentSquare, lastSquare):
        return solve(teleporters, dieSides, currentSquare, lastSquare)
