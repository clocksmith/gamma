class Solution:
    def checkPossibility(self, nums: list[int]) -> bool:
        if len(nums) < 2:
            return True

        changes = 0
        previous = nums[0]
        for index in range(1, len(nums)):
            current = nums[index]
            if current >= previous:
                previous = current
                continue
            changes += 1
            if changes > 1:
                return False
            if index == 1 or nums[index - 2] <= current:
                previous = current
        return True
