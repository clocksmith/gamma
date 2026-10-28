def solve(nums):
    i = len(nums) - 1
    while i > 0 and nums[i - 1] < nums[i]:
        i -= 1
    return i


class Solution:
    def minimumPrefixLength(self, nums):
        return solve(nums)
