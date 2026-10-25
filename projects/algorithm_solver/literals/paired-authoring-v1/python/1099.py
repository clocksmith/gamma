class Solution:
    def twoSumLessThanK(self, nums, k):
        nums.sort()
        left = 0
        right = len(nums) - 1
        best = -1
        while left < right:
            total = nums[left] + nums[right]
            if total < k:
                best = max(best, total)
                left += 1
            else:
                right -= 1
        return best
