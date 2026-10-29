"""Hack2Hire 6986df8bfedd959e9aa443d6 (Design Card Game II, variant 3) over an INFERRED spec; qualification unknown."""

SUITS = ('CLUBS', 'DIAMONDS', 'HEARTS', 'SPADES')
RANKS = ('A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K')
SUIT_INDEX = {s: i for i, s in enumerate(SUITS)}
RANK_INDEX = {r: i for i, r in enumerate(RANKS)}


def solve(shuffledDeck, players):
    size = 52 // players
    hands = [[] for _ in range(players)]
    for i in range(size * players):
        suit, rank = shuffledDeck[i]
        hands[i % players].append(RANK_INDEX[rank] * 4 + SUIT_INDEX[suit])  # strength: rank first, suit breaks ties
    for hand in hands:
        hand.sort(reverse=True)
    wins = [0] * players
    for round_index in range(size):
        best = max(range(players), key=lambda p: hands[p][round_index])
        wins[best] += 1
    return wins


class Solution:
    def playRounds(self, shuffledDeck, players):
        return solve(shuffledDeck, players)
