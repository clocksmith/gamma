"""1846. Maximum Element After Decreasing and Rearranging (Medium).

Specification: https://leetcode.com/problems/maximum-element-after-decreasing-and-rearranging/description/
"""


def solve(arr: list[int]) -> int:
    ordered = sorted(arr)
    ordered[0] = 1
    for i in range(1, len(ordered)):
        if ordered[i] > ordered[i - 1] + 1:
            ordered[i] = ordered[i - 1] + 1
    return ordered[-1]


class Solution:
    def maximumElementAfterDecrementingAndRearranging(self, arr: list[int]) -> int:
        return solve(arr)
