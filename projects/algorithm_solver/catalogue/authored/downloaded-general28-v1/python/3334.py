"""3334. Find the Maximum Factor Score of Array (Medium).

Specification: https://leetcode.com/problems/find-the-maximum-factor-score-of-array/description/
"""


def solve(nums: list[int]) -> int:
    import math

    def score(arr):
        if not arr:
            return 0
        g = arr[0]
        l = arr[0]
        for x in arr[1:]:
            g = math.gcd(g, x)
            l = l // math.gcd(l, x) * x
        return g * l

    best = score(nums)
    for i in range(len(nums)):
        best = max(best, score(nums[:i] + nums[i + 1:]))
    return best


class Solution:
    def maxScore(self, nums: list[int]) -> int:
        return solve(nums)
