"""2344. Minimum Deletions to Make Array Divisible (Medium).

Specification: https://leetcode.com/problems/minimum-deletions-to-make-array-divisible/description/
"""


def solve(nums: list[int], numsDivide: list[int]) -> int:
    import math
    g = numsDivide[0]
    for v in numsDivide:
        g = math.gcd(g, v)
    for i, v in enumerate(sorted(nums)):
        if g % v == 0:
            return i
    return -1


class Solution:
    def minOperations(self, nums, numsDivide) -> object:
        return solve(nums, numsDivide)
