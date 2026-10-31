"""Original frontend 3247 variant; qualification unknown."""

MOD = 10**9 + 7


def solve(nums) -> int:
    if any(x & 1 for x in nums):
        return pow(2, len(nums) - 1, MOD)
    return 0


subsequenceCount = solve


class Solution:
    def subsequenceCount(self, nums) -> int:
        return solve(nums)
