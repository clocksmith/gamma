"""Hack2Hire 68e9554c149617c9114ecdd1 (Racing Points and Winner, variant 2) over an INFERRED spec; qualification unknown."""

_POINTS = (15, 10, 5)


def solve(races):
    stats = {}  # rider -> [points, firsts, seconds, thirds]
    for race in races:
        for pos, rider in enumerate(race):
            row = stats.get(rider)
            if row is None:
                row = stats[rider] = [0, 0, 0, 0]
            if pos < 3:
                row[0] += _POINTS[pos]
                row[pos + 1] += 1
    return sorted(stats, key=lambda r: (-stats[r][0], -stats[r][1], -stats[r][2], -stats[r][3], r))


class Solution:
    def seasonStandings(self, races):
        return solve(races)
