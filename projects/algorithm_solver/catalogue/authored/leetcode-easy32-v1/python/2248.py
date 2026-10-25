"""2248. Intersection of Multiple Arrays (Easy).

Specification: https://leetcode.com/problems/intersection-of-multiple-arrays/description/
"""


def solve(nums: list[list[int]]) -> list[int]:
    """O(S + U) time, O(U) space; U = 1000; preserve every input row."""
    maximum_value = 1000
    counts = [0] * (maximum_value + 1)
    for row in nums:
        for value in row:
            counts[value] += 1
    result = []
    for value in range(1, maximum_value + 1):
        if counts[value] == len(nums):
            result.append(value)
    return result


class Solution:
    def intersection(self, nums: list[list[int]]) -> list[int]:
        return solve(nums)
