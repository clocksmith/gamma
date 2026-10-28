"""1512. Number of Good Pairs (Easy).

Specification: https://leetcode.com/problems/number-of-good-pairs/description/
"""


def solve(nums: list[int]) -> int:
    counts = {}
    for value in nums:
        counts[value] = counts.get(value, 0) + 1
    total = 0
    for count in counts.values():
        total += count * (count - 1) // 2
    return total


class Solution:
    def numIdenticalPairs(self, nums: list[int]) -> int:
        return solve(nums)
