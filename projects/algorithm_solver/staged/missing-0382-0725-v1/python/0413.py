"""413. Arithmetic Slices."""

def solve(nums: list[int]) -> int:
    answer = ending = 0
    for i in range(2, len(nums)):
        ending = ending + 1 if nums[i] - nums[i - 1] == nums[i - 1] - nums[i - 2] else 0
        answer += ending
    return answer


class Solution:
    def numberOfArithmeticSlices(self, nums: list[int]) -> int:
        return solve(nums)
