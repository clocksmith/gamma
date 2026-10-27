"""442. Find All Duplicates in an Array. Temporary sign marks use O(1) auxiliary space; restore all input values before returning."""

def solve(nums: list[int]) -> list[int]:
    answer = []
    for i in range(len(nums)):
        value = abs(nums[i])
        if nums[value - 1] < 0:
            answer.append(value)
        else:
            nums[value - 1] = -nums[value - 1]
    for i in range(len(nums)):
        nums[i] = abs(nums[i])
    return answer


class Solution:
    def findDuplicates(self, nums: list[int]) -> list[int]:
        return solve(nums)
