"""3192. Minimum Operations to Make Binary Array Elements Equal to One II (Medium).

Specification: https://leetcode.com/problems/minimum-operations-to-make-binary-array-elements-equal-to-one-ii/description/
"""


def solve(nums: list[int]) -> int:
    flips = 0
    ans = 0
    for v in nums:
        if (v ^ flips) == 0:
            flips ^= 1
            ans += 1
    return ans


class Solution:
    def minOperations(self, nums):
        return solve(nums)
