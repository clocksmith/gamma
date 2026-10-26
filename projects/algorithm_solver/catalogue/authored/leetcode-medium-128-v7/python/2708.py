"""2708. Maximum Strength of a Group: track both extremal products of a nonempty subsequence."""


def solve(nums: list[int]) -> int:
    """O(n) time and O(1) auxiliary space on the bounded integer domain; inputs are read-only."""
    smallest = largest = nums[0]
    for index in range(1, len(nums)):
        value = nums[index]
        candidates = (value, smallest * value, largest * value)
        smallest = min(smallest, *candidates)
        largest = max(largest, *candidates)
    return largest


class Solution:
    def maxStrength(self, nums: list[int]) -> int:
        return solve(nums)
