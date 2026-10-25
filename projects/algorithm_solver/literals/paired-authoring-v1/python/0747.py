class Solution:
    def dominantIndex(self, nums: list[int]) -> int:
        if not nums:
            return -1

        largest = 0
        for index in range(1, len(nums)):
            if nums[index] > nums[largest]:
                largest = index
        for index, value in enumerate(nums):
            if index != largest and 2 * value > nums[largest]:
                return -1
        return largest
