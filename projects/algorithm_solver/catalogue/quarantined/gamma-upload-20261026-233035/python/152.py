"""152. Maximum Product Subarray."""
def solve(nums: list[int]) -> int:
    current_minimum = current_maximum = answer = nums[0]
    for value in nums[1:]:
        if value < 0:
            current_minimum, current_maximum = current_maximum, current_minimum
        current_maximum = max(value, current_maximum * value)
        current_minimum = min(value, current_minimum * value)
        answer = max(answer, current_maximum)
    return answer

class Solution:
    def maxProduct(self, nums: list[int]) -> int:
        return solve(nums)
