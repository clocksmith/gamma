"""3637. Trionic Array I (Easy).

Specification: https://leetcode.com/problems/trionic-array-i/description/
"""


def solve(nums: list[int]) -> bool:
    """O(n) time, O(1) space; each of the three strict runs needs at least one edge."""
    length = len(nums)
    index = 1
    while index < length and nums[index] > nums[index - 1]:
        index += 1
    if index == 1 or index == length:
        return False
    firstTurn = index
    while index < length and nums[index] < nums[index - 1]:
        index += 1
    if index == firstTurn or index == length:
        return False
    secondTurn = index
    while index < length and nums[index] > nums[index - 1]:
        index += 1
    return index == length and index > secondTurn


class Solution:
    def isTrionic(self, nums: list[int]) -> bool:
        return solve(nums)
