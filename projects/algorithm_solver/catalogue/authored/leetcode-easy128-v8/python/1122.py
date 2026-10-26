"""1122. Relative Sort Array (Easy).

Specification: https://leetcode.com/problems/relative-sort-array/description/
"""


def solve(arr1: list[int], arr2: list[int]) -> list[int]:
    """O(n + m + u log u) time, O(n + u) space; ordered groups first, remaining values ascending."""
    counts = {}
    for value in arr1:
        counts[value] = counts.get(value, 0) + 1
    result = []
    for value in arr2:
        result.extend([value] * counts.pop(value, 0))
    for value in sorted(counts):
        result.extend([value] * counts[value])
    return result


class Solution:
    def relativeSortArray(self, arr1: list[int], arr2: list[int]) -> list[int]:
        return solve(arr1, arr2)
