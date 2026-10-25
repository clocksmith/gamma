class Solution:
    def isMonotonic(self, nums: list[int]) -> bool:
        increasing = True
        decreasing = True
        for index in range(1, len(nums)):
            if nums[index] < nums[index - 1]:
                increasing = False
            if nums[index] > nums[index - 1]:
                decreasing = False
            if not increasing and not decreasing:
                return False
        return True
