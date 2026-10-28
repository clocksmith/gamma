"""1186. Maximum Subarray Sum with One Deletion (Medium).

Specification: https://leetcode.com/problems/maximum-subarray-sum-with-one-deletion/description/
"""


def solve(arr: list[int]) -> int:
    without = arr[0]
    with_one = float('-inf')
    best = arr[0]
    for i in range(1, len(arr)):
        with_one = max(with_one + arr[i], without)
        without = max(arr[i], without + arr[i])
        best = max(best, without, with_one)
    return best


class Solution:
    def maximumSum(self, arr: list[int]) -> int:
        return solve(arr)
