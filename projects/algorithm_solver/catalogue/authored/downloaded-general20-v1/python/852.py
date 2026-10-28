"""852. Peak Index in a Mountain Array (Medium).

Specification: https://leetcode.com/problems/peak-index-in-a-mountain-array/description/
"""


def solve(arr: list[int]) -> int:
    left = 0
    right = len(arr) - 1
    while left < right:
        middle = (left + right) // 2
        if arr[middle] < arr[middle + 1]:
            left = middle + 1
        else:
            right = middle
    return left


class Solution:
    def peakIndexInMountainArray(self, arr: list[int]) -> int:
        return solve(arr)
