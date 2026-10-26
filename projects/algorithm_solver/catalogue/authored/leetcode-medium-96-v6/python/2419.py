"""2419. Longest Subarray With Maximum Bitwise AND: find the longest run of the global maximum value."""


def solve(nums: list[int]) -> int:
    """O(n) time and O(1) auxiliary space; inputs are read-only."""
    maximum = max(nums)
    current = best = 0
    for value in nums:
        current = current + 1 if value == maximum else 0
        best = max(best, current)
    return best


class Solution:
    def longestSubarray(self, nums: list[int]) -> int:
        return solve(nums)
