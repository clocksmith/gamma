"""845. Longest Mountain in Array (Medium).

Specification: https://leetcode.com/problems/longest-mountain-in-array/description/
"""


def solve(arr: list[int]) -> int:
    best = 0
    i = 1
    while i < len(arr) - 1:
        if arr[i] > arr[i - 1] and arr[i] > arr[i + 1]:
            left = i - 1
            while left > 0 and arr[left] > arr[left - 1]:
                left -= 1
            right = i + 1
            while right < len(arr) - 1 and arr[right] > arr[right + 1]:
                right += 1
            best = max(best, right - left + 1)
            i = right
        else:
            i += 1
    return best


class Solution:
    def longestMountain(self, arr: list[int]) -> int:
        return solve(arr)
