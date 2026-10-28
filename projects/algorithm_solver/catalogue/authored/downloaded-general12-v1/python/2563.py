"""2563. Count the Number of Fair Pairs (Medium).

Specification: https://leetcode.com/problems/count-the-number-of-fair-pairs/description/
"""


def solve(nums, lower, upper):
    a = sorted(nums)

    def count_less(target):
        l, r = 0, len(a) - 1
        cnt = 0
        while l < r:
            if a[l] + a[r] < target:
                cnt += r - l
                l += 1
            else:
                r -= 1
        return cnt

    return count_less(upper + 1) - count_less(lower)


class Solution:
    def countFairPairs(self, nums, lower, upper):
        return solve(nums, lower, upper)
