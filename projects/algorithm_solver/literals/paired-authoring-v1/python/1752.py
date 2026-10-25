class Solution:
    def check(self, nums: list[int]) -> bool:
        descents = 0
        for index in range(len(nums)):
            if nums[index] > nums[(index + 1) % len(nums)]:
                descents += 1
                if descents > 1:
                    return False
        return True
