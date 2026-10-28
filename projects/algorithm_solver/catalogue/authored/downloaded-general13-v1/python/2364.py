"""2364. Count Number of Bad Pairs (Medium).

Specification: https://leetcode.com/problems/count-number-of-bad-pairs/description/
"""


def solve(nums):
    seen = {}
    good = 0
    for i, v in enumerate(nums):
        key = v - i
        good += seen.get(key, 0)
        seen[key] = seen.get(key, 0) + 1
    n = len(nums)
    return n * (n - 1) // 2 - good


class Solution:
    def countBadPairs(self, nums):
        return solve(nums)
