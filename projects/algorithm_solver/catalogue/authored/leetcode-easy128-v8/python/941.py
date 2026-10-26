"""941. Valid Mountain Array (Easy).

Specification: https://leetcode.com/problems/valid-mountain-array/description/
"""


def solve(arr: list[int]) -> bool:
    """O(n) time, O(1) space; require a nonempty strictly increasing and decreasing segment."""
    if len(arr) < 3:
        return False
    index = 1
    while index < len(arr) and arr[index] > arr[index - 1]:
        index += 1
    if index == 1 or index == len(arr):
        return False
    while index < len(arr) and arr[index] < arr[index - 1]:
        index += 1
    return index == len(arr)


class Solution:
    def validMountainArray(self, arr: list[int]) -> bool:
        return solve(arr)
