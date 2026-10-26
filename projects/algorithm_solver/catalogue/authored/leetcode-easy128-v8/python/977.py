"""977. Squares of a Sorted Array (Easy).

Specification: https://leetcode.com/problems/squares-of-a-sorted-array/description/
"""


def solve(nums: list[int]) -> list[int]:
    """O(n) time and space; fill from the largest squared endpoint without sorting."""
    result = [0] * len(nums)
    left, right = 0, len(nums) - 1
    for index in range(len(nums) - 1, -1, -1):
        if abs(nums[left]) > abs(nums[right]):
            result[index] = nums[left] * nums[left]
            left += 1
        else:
            result[index] = nums[right] * nums[right]
            right -= 1
    return result


class Solution:
    def sortedSquares(self, nums: list[int]) -> list[int]:
        return solve(nums)
