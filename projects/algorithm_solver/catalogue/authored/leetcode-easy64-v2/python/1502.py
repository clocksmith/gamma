"""1502. Can Make Arithmetic Progression From Sequence (Easy).

Specification: https://leetcode.com/problems/can-make-arithmetic-progression-from-sequence/description/
"""


def solve(arr: list[int]) -> bool:
    """O(n log n) time, O(n) space; sort a copy and preserve arr."""
    ordered = sorted(arr)
    difference = ordered[1] - ordered[0]
    for index in range(2, len(ordered)):
        if ordered[index] - ordered[index - 1] != difference:
            return False
    return True


class Solution:
    def canMakeArithmeticProgression(self, arr: list[int]) -> bool:
        return solve(arr)
