"""Original frontend 3788 development variant; qualification unknown."""

def solve(nums):
    suffix = [0] * len(nums)
    suffix[-1] = nums[-1]
    for i in range(len(nums) - 2, -1, -1):
        suffix[i] = min(nums[i], suffix[i + 1])
    total = 0
    answer = -10**30
    for i in range(len(nums) - 1):
        total += nums[i]
        answer = max(answer, total - suffix[i + 1])
    return answer


class Solution:
    def maximumScore(self, nums):
        return solve(nums)
