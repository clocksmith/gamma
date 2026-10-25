class Solution:
    def subsets(self, nums: list[int]) -> list[list[int]]:
        result = [[]]
        for value in nums:
            count = len(result)
            for index in range(count):
                result.append(result[index] + [value])
        return result
