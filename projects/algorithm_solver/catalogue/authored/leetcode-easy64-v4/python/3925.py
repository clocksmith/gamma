"""3925. Concatenate Array With Reverse (Easy).

Specification: https://leetcode.com/problems/concatenate-array-with-reverse/description/
"""


def solve(nums: list[int]) -> list[int]:
    """O(n) time and output space; do not mutate or return the input array."""
    result = nums.copy()
    for index in range(len(nums) - 1, -1, -1):
        result.append(nums[index])
    return result


class Solution:
    def concatWithReverse(self, nums: list[int]) -> list[int]:
        return solve(nums)
