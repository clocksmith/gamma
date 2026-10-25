class Solution:
    def minimumOperations(self, nums):
        if not nums:
            return 0
        left = 0
        right = len(nums) - 1
        left_sum = nums[left]
        right_sum = nums[right]
        merges = 0
        while left < right:
            if left_sum == right_sum:
                left += 1
                right -= 1
                if left < right:
                    left_sum = nums[left]
                    right_sum = nums[right]
            elif left_sum < right_sum:
                left += 1
                left_sum += nums[left]
                merges += 1
            else:
                right -= 1
                right_sum += nums[right]
                merges += 1
        return merges
