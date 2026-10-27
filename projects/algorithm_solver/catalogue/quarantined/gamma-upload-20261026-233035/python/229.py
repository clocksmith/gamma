"""229. Majority Element II."""
def solve(nums: list[int]) -> list[int]:
    first = second = None
    first_count = second_count = 0
    for value in nums:
        if value == first:
            first_count += 1
        elif value == second:
            second_count += 1
        elif first_count == 0:
            first, first_count = value, 1
        elif second_count == 0:
            second, second_count = value, 1
        else:
            first_count -= 1
            second_count -= 1
    return [value for value in (first, second) if value is not None and nums.count(value) > len(nums) // 3]

class Solution:
    def majorityElement(self, nums: list[int]) -> list[int]:
        return solve(nums)
