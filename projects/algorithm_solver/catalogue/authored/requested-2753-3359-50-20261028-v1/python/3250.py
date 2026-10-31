"""Original frontend 3250 variant; qualification unknown."""

import math

MOD = 10**9 + 7


def solve(nums) -> int:
    n = len(nums)
    diff_sum = sum(max(0, nums[i] - nums[i - 1]) for i in range(1, n))
    rem = nums[-1] - diff_sum
    if rem < 0:
        return 0
    return math.comb(rem + n, n) % MOD


countOfPairs = solve


class Solution:
    def countOfPairs(self, nums) -> int:
        return solve(nums)
