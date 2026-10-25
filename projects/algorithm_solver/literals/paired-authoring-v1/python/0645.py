class Solution:
    def findErrorNums(self, nums: list[int]) -> list[int]:
        counts = [0] * (len(nums) + 1)
        for value in nums:
            counts[value] += 1
        duplicate = 0
        missing = 0
        for value in range(1, len(counts)):
            if counts[value] == 2:
                duplicate = value
            elif counts[value] == 0:
                missing = value
        return [duplicate, missing]
