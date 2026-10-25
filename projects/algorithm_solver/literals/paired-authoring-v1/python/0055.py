class Solution:
    def canJump(self, nums: list[int]) -> bool:
        farthest = 0
        for index, distance in enumerate(nums):
            if index > farthest:
                return False
            farthest = max(farthest, index + distance)
            if farthest >= len(nums) - 1:
                return True
        return False
