"""485. Max Consecutive Ones (Easy).

Specification: https://leetcode.com/problems/max-consecutive-ones/description/
"""


def solve(nums: list[int]) -> int:
    """O(n) time, O(1) space; preserve nums."""
    current = 0
    longest = 0
    for value in nums:
        current = current + 1 if value == 1 else 0
        longest = max(longest, current)
    return longest


class Solution:
    def findMaxConsecutiveOnes(self, nums: list[int]) -> int:
        return solve(nums)
