class Solution:
    def findMin(self, nums: list[int]) -> int:
        left = 0
        right = len(nums) - 1
        # The minimum remains in the closed interval [left, right].
        while left < right:
            middle = left + (right - left) // 2
            if nums[middle] > nums[right]:
                left = middle + 1
            else:
                right = middle
        return nums[left]
