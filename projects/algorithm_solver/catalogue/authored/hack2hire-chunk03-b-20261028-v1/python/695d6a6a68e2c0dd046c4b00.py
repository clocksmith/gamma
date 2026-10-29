"""Hack2Hire 695d6a6a68e2c0dd046c4b00 (Poker Hand Game Checker, level 1) over an INFERRED spec; qualification unknown."""

VALUE = {r: v for v, r in enumerate(['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A'], start=2)}


def strength(hand):
    values, suits = [], set()
    for card in hand:
        rank, suit = card.split(' of ')
        values.append(VALUE[rank])
        suits.add(suit)
    counts = {}
    for v in values: counts[v] = counts.get(v, 0) + 1
    groups = sorted(counts.items(), key=lambda kv: (-kv[1], -kv[0]))
    shape = [c for _, c in groups]
    order = [v for v, _ in groups]
    flush = len(suits) == 1
    high = 0
    if len(groups) == 5:
        if order[0] - order[4] == 4: high = order[0]
        elif order == [14, 5, 4, 3, 2]: high = 5
    if high and flush: category = 8
    elif shape == [4, 1]: category = 7
    elif shape == [3, 2]: category = 6
    elif flush: category = 5
    elif high: category = 4
    elif shape == [3, 1, 1]: category = 3
    elif shape == [2, 2, 1]: category = 2
    elif shape == [2, 1, 1, 1]: category = 1
    else: category = 0
    return [category, high] if category in (8, 4) else [category] + order


def solve(hand):
    return strength(hand)[0] > 0


class Solution:
    def isValidHand(self, hand):
        return solve(hand)
