"""Hack2Hire 6ab30396e74ebb7457a3ef46 (Design Card Game III, variant 1 of 3) over an INFERRED spec; qualification unknown."""


RANK = {r: i for i, r in enumerate(['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A'])}


def hand_key(hand):
    """Flat strength key: category, then tie-break ranks in significance order."""
    ranks = sorted((RANK[c[:-1]] for c in hand), reverse=True)
    counts = {}
    for r in ranks:
        counts[r] = counts.get(r, 0) + 1
    if len(counts) == 1:
        return [3, ranks[0]]
    if len(counts) == 2:
        pair = ranks[1]  # the middle of three sorted ranks always belongs to the pair
        kicker = ranks[0] if ranks[0] != pair else ranks[2]
        return [2, pair, kicker]
    return [1] + ranks


def solve(deck):
    first = [deck[0], deck[2], deck[4]]
    second = [deck[1], deck[3], deck[5]]
    a, b = hand_key(first), hand_key(second)
    return [first, second, 1 if a > b else 2 if b > a else 0]


class Solution:
    def playRound(self, deck):
        return solve(deck)
