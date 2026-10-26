"""3736. Minimum Moves to Equal Array Elements III (Easy).

Specification: https://leetcode.com/problems/minimum-moves-to-equal-array-elements-iii/description/
"""


def solve(nums: list[int]) -> int:
    """O(n) time, O(1) space; increasing every value to the existing maximum is optimal."""
    largest = nums[0]
    total = 0
    for value in nums:
        largest = max(largest, value)
        total += value
    return largest * len(nums) - total


class Solution:
    def minMoves(self, nums: list[int]) -> int:
        return solve(nums)
