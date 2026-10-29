"""Hack2Hire 68fd5b9d47bea664c0bba367 (Poker Straight Sequence Check) over an INFERRED spec; qualification unknown."""

_RANK = {'A': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, '10': 10, 'J': 11, 'Q': 12, 'K': 13}


def solve(cards):
    low = [_RANK[c] for c in cards]
    if max(low) - min(low) == 4:  # five distinct values spanning 4 are consecutive
        return True
    high = [14 if r == 1 else r for r in low]
    return max(high) - min(high) == 4


class Solution:
    def isStraight(self, cards):
        return solve(cards)
