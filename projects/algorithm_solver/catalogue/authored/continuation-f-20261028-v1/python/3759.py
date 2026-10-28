"""Original frontend 3759 development candidate; qualification unknown."""

def solve(nums, k):
    if k == 0:
        return len(nums)
    cutoff = sorted(nums)[len(nums) - k]
    return sum(value < cutoff for value in nums)


class Solution:
    def countElements(self, nums, k):
        return solve(nums, k)
