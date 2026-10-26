"""1330. Reverse Subarray To Maximize Array Value.

Separate boundary reversals from the best internal boundary exchange; O(n) time and O(1) space. Inputs are preserved.
"""

def solve(nums: list[int]) -> int:
    total = gain = 0
    largest_lower = float('-inf')
    smallest_upper = float('inf')
    for first, second in zip(nums, nums[1:]):
        difference = abs(first - second)
        total += difference
        gain = max(gain, abs(nums[0] - second) - difference, abs(nums[-1] - first) - difference)
        largest_lower = max(largest_lower, min(first, second))
        smallest_upper = min(smallest_upper, max(first, second))
    if len(nums) > 1:
        gain = max(gain, 2 * (largest_lower - smallest_upper))
    return total + gain


class Solution:
    def maxValueAfterReverse(self, nums: list[int]) -> int:
        return solve(nums)
