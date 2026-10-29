"""Hack2Hire 68e8779c80f69c7a01706899 (Racing Points and Winner, variant 1) over an INFERRED spec; qualification unknown."""

_POINTS = (15, 10, 5)


def solve(races):
    total = {}
    for race in races:
        for pos, rider in enumerate(race):
            total[rider] = total.get(rider, 0) + (_POINTS[pos] if pos < 3 else 0)
    best_name, best_points = None, -1
    for rider, points in total.items():
        if points > best_points or (points == best_points and rider < best_name):
            best_name, best_points = rider, points
    return best_name


class Solution:
    def seasonWinner(self, races):
        return solve(races)
