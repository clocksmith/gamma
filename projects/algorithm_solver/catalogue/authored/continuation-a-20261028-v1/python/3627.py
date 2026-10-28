def solve(nums):
    ordered = sorted(nums)
    groups = len(nums) // 3
    return sum(ordered[len(nums) - 2 - 2 * i] for i in range(groups))


class Solution:
    def maximumMedianSum(self, nums):
        return solve(nums)
