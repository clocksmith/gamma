class Solution:
    def getSumAbsoluteDifferences(self, nums: list[int]) -> list[int]:
        total = sum(nums)
        left_sum = 0
        output = []
        for index, value in enumerate(nums):
            left = value * index - left_sum
            right = total - left_sum - value - value * (len(nums) - index - 1)
            output.append(left + right)
            left_sum += value
        return output
