"""Original frontend 3828 variant; qualification unknown."""

def solve(nums):
    return max(nums[0], nums[-1])


class Solution:
    def finalElement(self, nums):
        return solve(nums)
