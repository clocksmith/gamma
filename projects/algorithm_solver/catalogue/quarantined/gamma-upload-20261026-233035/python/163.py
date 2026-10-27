"""163. Missing Ranges."""
def solve(nums: list[int], lower: int, upper: int) -> list[list[int]]:
    result = []
    previous = lower - 1
    for value in nums + [upper + 1]:
        if value - previous >= 2:
            result.append([previous + 1, value - 1])
        previous = value
    return result

class Solution:
    def findMissingRanges(self, nums: list[int], lower: int, upper: int) -> list[list[int]]:
        return solve(nums, lower, upper)
