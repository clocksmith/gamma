"""1200. Minimum Absolute Difference (Easy).

Specification: https://leetcode.com/problems/minimum-absolute-difference/description/
"""


def solve(arr: list[int]) -> list[list[int]]:
    """O(n log n) time, O(n) space; sort a copy and return fresh pairs."""
    values = sorted(arr)
    smallest = values[1] - values[0]
    result = []
    for index in range(1, len(values)):
        difference = values[index] - values[index - 1]
        if difference < smallest:
            smallest = difference
            result = []
        if difference == smallest:
            result.append([values[index - 1], values[index]])
    return result


class Solution:
    def minimumAbsDifference(self, arr: list[int]) -> list[list[int]]:
        return solve(arr)
