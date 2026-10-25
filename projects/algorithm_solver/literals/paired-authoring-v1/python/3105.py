class Solution:
    def longestMonotonicSubarray(self, nums: list[int]) -> int:
        if not nums:
            return 0
        increasing = 1
        decreasing = 1
        best = 1
        for index in range(1, len(nums)):
            if nums[index] > nums[index - 1]:
                increasing += 1
            else:
                increasing = 1
            if nums[index] < nums[index - 1]:
                decreasing += 1
            else:
                decreasing = 1
            best = max(best, increasing, decreasing)
        return best
