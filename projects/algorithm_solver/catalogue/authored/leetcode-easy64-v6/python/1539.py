"""1539. Kth Missing Positive Number (Easy).

Specification: https://leetcode.com/problems/kth-missing-positive-number/description/
"""


def solve(arr: list[int], k: int) -> int:
    """O(log n) time, O(1) space; binary-search the missing-count boundary; preserve arr."""
    low, high = 0, len(arr)
    while low < high:
        middle = (low + high) // 2
        if arr[middle] - middle - 1 < k:
            low = middle + 1
        else:
            high = middle
    return low + k


class Solution:
    def findKthPositive(self, arr: list[int], k: int) -> int:
        return solve(arr, k)
