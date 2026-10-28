"""1574. Shortest Subarray to be Removed to Make Array Sorted (Medium).

Specification: https://leetcode.com/problems/shortest-subarray-to-be-removed-to-make-array-sorted/description/
"""


def solve(arr: list[int]) -> int:
    n = len(arr)
    left = 0
    while left + 1 < n and arr[left] <= arr[left + 1]:
        left += 1
    if left == n - 1:
        return 0
    right = n - 1
    while right > 0 and arr[right - 1] <= arr[right]:
        right -= 1
    best = min(n - left - 1, right)
    i, j = 0, right
    while i <= left and j < n:
        if arr[i] <= arr[j]:
            best = min(best, j - i - 1)
            i += 1
        else:
            j += 1
    return best


class Solution:
    def findLengthOfShortestSubarray(self, arr: list[int]) -> int:
        return solve(arr)
