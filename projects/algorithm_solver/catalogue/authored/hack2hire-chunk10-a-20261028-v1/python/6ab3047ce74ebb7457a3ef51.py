"""Hack2Hire 6ab3047ce74ebb7457a3ef51 (Design Card Game III, variant 3 of 3) over an INFERRED spec; qualification unknown."""


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


def solve(numPlayers, deck):
    hands = [[deck[p], deck[p + numPlayers], deck[p + 2 * numPlayers]] for p in range(numPlayers)]
    best, winners = None, []
    for p, hand in enumerate(hands):
        key = hand_key(hand)
        if best is None or key > best:
            best, winners = key, [p + 1]
        elif key == best:
            winners.append(p + 1)
    return [hands, winners]


class Solution:
    def playTable(self, numPlayers, deck):
        return solve(numPlayers, deck)
