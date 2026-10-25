class Solution:
    def findUnsortedSubarray(self, nums: list[int]) -> int:
        if len(nums) < 2:
            return 0

        left = len(nums)
        right = -1
        largest = nums[0]
        for index in range(1, len(nums)):
            if nums[index] < largest:
                right = index
            else:
                largest = nums[index]
        smallest = nums[-1]
        for index in range(len(nums) - 2, -1, -1):
            if nums[index] > smallest:
                left = index
            else:
                smallest = nums[index]
        return 0 if right < left else right - left + 1
