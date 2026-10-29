"""Hack2Hire 67eb34914c9bb801bfd0ef7d (Stock Trades Matching, variant 1 of 2) over an INFERRED spec; qualification unknown."""


def solve(house, street):
    counts = {}
    for trade in street:
        counts[trade] = counts.get(trade, 0) + 1
    left = []
    for trade in house:
        if counts.get(trade, 0) > 0:
            counts[trade] -= 1
        else:
            left.append(trade)
    for trade, count in counts.items():
        for _ in range(count):
            left.append(trade)
    left.sort()
    return left


class Solution:
    def unmatchedTrades(self, house, street):
        return solve(house, street)
