"""1356. Sort Integers by The Number of 1 Bits (Easy).

Specification: https://leetcode.com/problems/sort-integers-by-the-number-of-1-bits/description/
"""


def solve(arr: list[int]) -> list[int]:
    """O(n * b + n log n) time, O(n) space; b <= 14 in the declared domain."""
    ranked = []
    for value in arr:
        remaining = value
        bits = 0
        while remaining > 0:
            remaining &= remaining - 1
            bits += 1
        ranked.append((bits, value))
    ranked.sort()
    return [value for bits, value in ranked]


class Solution:
    def sortByBits(self, arr: list[int]) -> list[int]:
        return solve(arr)
