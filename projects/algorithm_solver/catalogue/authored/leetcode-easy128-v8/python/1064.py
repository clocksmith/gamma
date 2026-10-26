"""1064. Fixed Point (Easy).

Specification: https://leetcode.com/problems/fixed-point/description/
"""


def solve(arr: list[int]) -> int:
    """O(log n) time, O(1) space; lower-bound search for the first arr[index] >= index in a strictly increasing array."""
    left, right = 0, len(arr)
    while left < right:
        middle = left + (right - left) // 2
        if arr[middle] < middle:
            left = middle + 1
        else:
            right = middle
    return left if left < len(arr) and arr[left] == left else -1


class Solution:
    def fixedPoint(self, arr: list[int]) -> int:
        return solve(arr)
