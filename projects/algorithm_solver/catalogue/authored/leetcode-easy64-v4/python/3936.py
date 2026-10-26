"""3936. Minimum Swaps to Move Zeros to End (Easy).

Specification: https://leetcode.com/problems/minimum-swaps-to-move-zeros-to-end/description/
"""


def solve(nums: list[int]) -> int:
    """O(n) time, O(1) space; arbitrary index swaps are allowed; preserve nums."""
    nonzeroCount = 0
    for value in nums:
        if value != 0:
            nonzeroCount += 1
    swaps = 0
    for index in range(nonzeroCount):
        if nums[index] == 0:
            swaps += 1
    return swaps


class Solution:
    def minimumSwaps(self, nums: list[int]) -> int:
        return solve(nums)
