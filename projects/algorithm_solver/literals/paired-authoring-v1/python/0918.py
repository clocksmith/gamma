class Solution:
    def maxSubarraySumCircular(self, nums: list[int]) -> int:
        total = nums[0]
        maximum_end = nums[0]
        minimum_end = nums[0]
        maximum = nums[0]
        minimum = nums[0]
        for index in range(1, len(nums)):
            value = nums[index]
            maximum_end = max(value, maximum_end + value)
            minimum_end = min(value, minimum_end + value)
            maximum = max(maximum, maximum_end)
            minimum = min(minimum, minimum_end)
            total += value
        if maximum < 0:
            return maximum
        return max(maximum, total - minimum)
