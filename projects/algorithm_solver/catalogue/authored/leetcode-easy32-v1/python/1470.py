"""1470. Shuffle the Array (Easy).

Specification: https://leetcode.com/problems/shuffle-the-array/description/
"""


def solve(nums: list[int], n: int) -> list[int]:
    """O(n) time, O(1) auxiliary space excluding output; preserve nums."""
    result = []
    for index in range(n):
        result.append(nums[index])
        result.append(nums[index + n])
    return result


class Solution:
    def shuffle(self, nums: list[int], n: int) -> list[int]:
        return solve(nums, n)
