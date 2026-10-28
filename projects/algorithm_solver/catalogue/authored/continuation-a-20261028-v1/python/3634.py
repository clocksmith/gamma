def solve(nums, k):
    ordered = sorted(nums)
    left = best = 0
    for right, value in enumerate(ordered):
        while value > ordered[left] * k:
            left += 1
        best = max(best, right - left + 1)
    return len(nums) - best


class Solution:
    def minRemoval(self, nums, k):
        return solve(nums, k)
