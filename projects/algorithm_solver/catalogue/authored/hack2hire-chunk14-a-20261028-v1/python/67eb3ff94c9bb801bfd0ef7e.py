"""Hack2Hire 67eb3ff94c9bb801bfd0ef7e (Stock Trades Matching, variant 2 of 2) over an INFERRED spec; qualification unknown."""


def solve(house, street):
    counts = {}
    for trade in street:
        counts[trade] = counts.get(trade, 0) + 1
    house_left = []
    for trade in house:
        if counts.get(trade, 0) > 0:
            counts[trade] -= 1
        else:
            house_left.append(trade)
    groups = {}
    for trade in house_left:
        groups.setdefault(trade[:11], ([], []))[0].append(trade)
    for trade, count in counts.items():
        for _ in range(count):
            groups.setdefault(trade[:11], ([], []))[1].append(trade)
    left = []
    for side_house, side_street in groups.values():
        side_house.sort()
        side_street.sort()
        paired = min(len(side_house), len(side_street))
        left.extend(side_house[paired:])
        left.extend(side_street[paired:])
    left.sort()
    return left


class Solution:
    def unmatchedTradesWithAttributes(self, house, street):
        return solve(house, street)
