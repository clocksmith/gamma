"""Hack2Hire 69646297b481f959f9e384ee (Minimum Coin Combination Counts) over an INFERRED spec; qualification unknown."""


def solve(coins, target):
    order = sorted(range(len(coins)), key=lambda i: -coins[i])
    m = len(order)
    inf = target + 1
    tables = [None] * (m + 1)
    tables[m] = [0] + [inf] * target
    for pos in range(m - 1, -1, -1):
        c = coins[order[pos]]
        row = tables[pos + 1][:]
        for a in range(c, target + 1):
            if row[a - c] + 1 < row[a]:
                row[a] = row[a - c] + 1
        tables[pos] = row
    if tables[0][target] >= inf:
        return []
    counts = [0] * len(coins)
    left = target
    for pos in range(m):
        c = coins[order[pos]]
        need = tables[pos][left]
        t = left // c
        while tables[pos + 1][left - t * c] != need - t:
            t -= 1
        counts[order[pos]] = t
        left -= t * c
    return counts


class Solution:
    def minCoinCombination(self, coins, target):
        return solve(coins, target)
