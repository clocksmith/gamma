"""Hack2Hire 6a4fb090665efda9311f5615 (League Earnings) over an INFERRED spec; qualification unknown."""


def solve(leagues, stadiumCapacities, silverwareCounts, targetLeague):
    clubs = [i for i, name in enumerate(leagues) if name == targetLeague]
    c = len(clubs)
    trophies = sum(silverwareCounts[i] for i in clubs)
    total = 0
    for i in clubs:
        own = silverwareCounts[i]
        total += stadiumCapacities[i] * ((c - 1) * own + (trophies - own))
    matches = c * (c - 1)
    quotient, remainder = divmod(total, matches)
    cents = quotient * 100 + (remainder * 200 + matches) // (2 * matches)
    return [total, '%d.%02d' % (cents // 100, cents % 100)]


class Solution:
    def leagueEarnings(self, leagues, stadiumCapacities, silverwareCounts, targetLeague):
        return solve(leagues, stadiumCapacities, silverwareCounts, targetLeague)
