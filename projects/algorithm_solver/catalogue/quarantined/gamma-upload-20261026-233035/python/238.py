"""238. Product of Array Except Self."""
def solve(nums: list[int]) -> list[int]:
    result = [1] * len(nums)
    prefix = 1
    for index, value in enumerate(nums):
        result[index] = prefix
        prefix *= value
    suffix = 1
    for index in range(len(nums) - 1, -1, -1):
        result[index] *= suffix
        suffix *= nums[index]
    return result

class Solution:
    def productExceptSelf(self, nums: list[int]) -> list[int]:
        return solve(nums)
