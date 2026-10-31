"""Original frontend 3353 variant; qualification unknown."""


def solve(nums) -> int:
    return sum(1 for i in range(len(nums) - 1) if nums[i] != nums[i + 1])


minOperations = solve


class Solution:
    def minOperations(self, nums) -> int:
        return solve(nums)
