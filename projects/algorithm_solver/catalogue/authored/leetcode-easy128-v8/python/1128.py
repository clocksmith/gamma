"""1128. Number of Equivalent Domino Pairs (Easy).

Specification: https://leetcode.com/problems/number-of-equivalent-domino-pairs/description/
"""


def solve(dominoes: list[list[int]]) -> int:
    """O(n) time, O(1) space for digits 1 through 9; count prior unordered matches."""
    counts = [0] * 100
    pairs = 0
    for first, second in dominoes:
        key = min(first, second) * 10 + max(first, second)
        pairs += counts[key]
        counts[key] += 1
    return pairs


class Solution:
    def numEquivDominoPairs(self, dominoes: list[list[int]]) -> int:
        return solve(dominoes)
