"""1287. Element Appearing More Than 25% In Sorted Array (Easy).

Specification: https://leetcode.com/problems/element-appearing-more-than-25-in-sorted-array/description/
"""


def solve(arr: list[int]) -> int:
    """O(n) time, O(1) space; preserve the sorted input."""
    offset = len(arr) // 4
    for index in range(len(arr) - offset):
        if arr[index] == arr[index + offset]:
            return arr[index]
    return arr[0]


class Solution:
    def findSpecialInteger(self, arr: list[int]) -> int:
        return solve(arr)
