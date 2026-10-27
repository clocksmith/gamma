"""487. Max Consecutive Ones II."""

def solve(nums: list[int]) -> int:
    left = zeros = answer = 0
    for right, value in enumerate(nums):
        zeros += value == 0
        while zeros > 1:
            zeros -= nums[left] == 0
            left += 1
        answer = max(answer, right - left + 1)
    return answer


class Solution:
    def findMaxConsecutiveOnes(self, nums: list[int]) -> int:
        return solve(nums)
