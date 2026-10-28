"""740. Delete and Earn (Medium).

Specification: https://leetcode.com/problems/delete-and-earn/description/
"""


def solve(nums: list[int]) -> int:
    if not nums:
        return 0
    max_value = max(nums)
    points = [0] * (max_value + 1)
    for value in nums:
        points[value] += value
    previous = 0
    current = points[0]
    for value in range(1, max_value + 1):
        previous, current = current, max(current, previous + points[value])
    return current


class Solution:
    def deleteAndEarn(self, nums: list[int]) -> int:
        return solve(nums)
