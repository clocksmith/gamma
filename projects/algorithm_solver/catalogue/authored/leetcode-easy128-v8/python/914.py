"""914. X of a Kind in a Deck of Cards (Easy).

Specification: https://leetcode.com/problems/x-of-a-kind-in-a-deck-of-cards/description/
"""


def solve(deck: list[int]) -> bool:
    """O(n + u * log n) time, O(u) space; all frequencies must share a divisor of at least two."""
    counts = {}
    for card in deck:
        counts[card] = counts.get(card, 0) + 1
    divisor = 0
    for count in counts.values():
        while count:
            divisor, count = count, divisor % count
        if divisor == 1:
            return False
    return divisor >= 2


class Solution:
    def hasGroupsSizeX(self, deck: list[int]) -> bool:
        return solve(deck)
