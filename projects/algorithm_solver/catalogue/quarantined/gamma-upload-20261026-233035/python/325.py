"""325. Maximum Size Subarray Sum Equals k."""
def solve(nums: list[int], k: int) -> int:
    first = {0: -1}
    total = best = 0
    for index, value in enumerate(nums):
        total += value
        if total - k in first:
            best = max(best, index - first[total - k])
        first.setdefault(total, index)
    return best

class Solution:
    def maxSubArrayLen(self, nums: list[int], k: int) -> int:
        return solve(nums, k)
