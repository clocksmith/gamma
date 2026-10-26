"""2260. Minimum Consecutive Cards to Pick Up: compare each repeated card with its nearest previous occurrence."""


def solve(cards: list[int]) -> int:
    """O(n) expected time and O(n) auxiliary space; inputs are read-only."""
    previous = {}
    best = len(cards) + 1
    for index, value in enumerate(cards):
        if value in previous:
            best = min(best, index - previous[value] + 1)
        previous[value] = index
    return best if best <= len(cards) else -1


class Solution:
    def minimumCardPickup(self, cards: list[int]) -> int:
        return solve(cards)
