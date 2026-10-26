"""2501. Longest Square Streak in an Array: process distinct values in increasing order and extend exact square chains."""
from math import isqrt


def solve(nums: list[int]) -> int:
    """O(n log n) time and O(n) auxiliary space; inputs are read-only."""
    lengths = {}
    best = 0
    for value in sorted(set(nums)):
        root = isqrt(value)
        length = lengths.get(root, 0) + 1 if root * root == value else 1
        lengths[value] = length
        best = max(best, length)
    return best if best >= 2 else -1


class Solution:
    def longestSquareStreak(self, nums: list[int]) -> int:
        return solve(nums)
