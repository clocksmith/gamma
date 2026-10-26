"""1588. Sum of All Odd Length Subarrays (Easy).

Specification: https://leetcode.com/problems/sum-of-all-odd-length-subarrays/description/
"""


def solve(arr: list[int]) -> int:
    """O(n) time, O(1) space; count odd-length windows containing each index; preserve arr."""
    result = 0
    for index, value in enumerate(arr):
        containing_windows = (index + 1) * (len(arr) - index)
        odd_windows = (containing_windows + 1) // 2
        result += value * odd_windows
    return result


class Solution:
    def sumOddLengthSubarrays(self, arr: list[int]) -> int:
        return solve(arr)
