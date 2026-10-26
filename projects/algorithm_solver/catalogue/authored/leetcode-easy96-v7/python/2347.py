"""2347. Best Poker Hand (Easy).

Specification: https://leetcode.com/problems/best-poker-hand/description/
"""


def solve(ranks: list[int], suits: list[str]) -> str:
    """O(1) time and space for five cards; prioritize Flush, Three of a Kind, Pair, High Card."""
    if all(suit == suits[0] for suit in suits):
        return 'Flush'
    counts = {}
    largest = 0
    for rank in ranks:
        count = counts.get(rank, 0) + 1
        counts[rank] = count
        largest = max(largest, count)
    if largest >= 3:
        return 'Three of a Kind'
    if largest >= 2:
        return 'Pair'
    return 'High Card'


class Solution:
    def bestHand(self, ranks: list[int], suits: list[str]) -> str:
        return solve(ranks, suits)
