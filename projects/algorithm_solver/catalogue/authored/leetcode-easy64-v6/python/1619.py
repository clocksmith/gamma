"""1619. Mean of Array After Removing Some Elements (Easy).

Specification: https://leetcode.com/problems/mean-of-array-after-removing-some-elements/description/
"""


def solve(arr: list[int]) -> float:
    """O(n log n) time, O(n) space; sort a copy; n is a positive multiple of 20."""
    values = sorted(arr)
    trim = len(values) // 20
    total = 0
    for index in range(trim, len(values) - trim):
        total += values[index]
    return total / (len(values) - 2 * trim)


class Solution:
    def trimMean(self, arr: list[int]) -> float:
        return solve(arr)
