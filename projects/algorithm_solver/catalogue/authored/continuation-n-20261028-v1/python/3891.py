"""Original frontend 3891 variant; qualification unknown."""

def solve(nums):
    def better(a, b):
        return a if a[0] > b[0] or a[0] == b[0] and a[1] <= b[1] else b
    skipped, selected = (0, 0), (-1, 0)
    for i in range(1, len(nums) - 1):
        cost = max(0, max(nums[i - 1], nums[i + 1]) + 1 - nums[i])
        skipped, selected = better(skipped, selected), (skipped[0] + 1, skipped[1] + cost)
    return better(skipped, selected)[1]


class Solution:
    def minIncrease(self, nums):
        return solve(nums)
