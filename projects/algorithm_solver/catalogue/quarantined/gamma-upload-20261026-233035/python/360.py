"""360. Sort Transformed Array."""
def solve(nums: list[int], a: int, b: int, c: int) -> list[int]:
    transform = lambda value: a * value * value + b * value + c
    left, right = 0, len(nums) - 1
    result = [0] * len(nums)
    write = len(nums) - 1 if a >= 0 else 0
    step = -1 if a >= 0 else 1
    while left <= right:
        left_value, right_value = transform(nums[left]), transform(nums[right])
        if (left_value >= right_value) == (a >= 0):
            result[write] = left_value
            left += 1
        else:
            result[write] = right_value
            right -= 1
        write += step
    return result

class Solution:
    def sortTransformedArray(self, nums, a, b, c):
        return solve(nums, a, b, c)
