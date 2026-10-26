"""3010. Divide an Array Into Subarrays With Minimum Cost I (Easy).

Specification: https://leetcode.com/problems/divide-an-array-into-subarrays-with-minimum-cost-i/description/
"""


def solve(nums: list[int]) -> int:
    """O(n) time, O(1) auxiliary space; choose two smallest starts after index zero."""
    smallest = min(nums[1], nums[2])
    second_smallest = max(nums[1], nums[2])
    for index in range(3, len(nums)):
        value = nums[index]
        if value < smallest:
            second_smallest = smallest
            smallest = value
        elif value < second_smallest:
            second_smallest = value
    return nums[0] + smallest + second_smallest


class Solution:
    def minimumCost(self, nums: list[int]) -> int:
        return solve(nums)
