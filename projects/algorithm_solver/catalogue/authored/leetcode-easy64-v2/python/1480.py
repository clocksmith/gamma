"""1480. Running Sum of 1d Array (Easy).

Specification: https://leetcode.com/problems/running-sum-of-1d-array/description/
"""


def solve(nums: list[int]) -> list[int]:
    """O(n) time, O(n) output space; preserve nums."""
    result = []
    total = 0
    for value in nums:
        total += value
        result.append(total)
    return result


class Solution:
    def runningSum(self, nums: list[int]) -> list[int]:
        return solve(nums)
