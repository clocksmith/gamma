"""Hack2Hire 697d94b4b8c468a441586147 (Design Card Game II, variant 1) over an INFERRED spec; qualification unknown."""

SUITS = ('CLUBS', 'DIAMONDS', 'HEARTS', 'SPADES')
RANKS = ('A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K')
SUIT_INDEX = {s: i for i, s in enumerate(SUITS)}
RANK_INDEX = {r: i for i, r in enumerate(RANKS)}


def solve(shuffledDeck):
    players = 4
    held = [[False] * 52 for _ in range(players)]
    for i, (suit, rank) in enumerate(shuffledDeck):
        held[i % players][SUIT_INDEX[suit] * 13 + RANK_INDEX[rank]] = True
    return [[[SUITS[k // 13], RANKS[k % 13]] for k in range(52) if marks[k]] for marks in held]


class Solution:
    def dealAndSortHands(self, shuffledDeck):
        return solve(shuffledDeck)
