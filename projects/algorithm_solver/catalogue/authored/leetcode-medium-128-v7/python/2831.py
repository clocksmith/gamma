"""2831. Find the Longest Equal Subarray: slide over positions of each value while limiting intervening deletions."""


def solve(nums: list[int], k: int) -> int:
    """O(n) expected time and O(n) auxiliary space; inputs are read-only."""
    positions = {}
    for index, value in enumerate(nums):
        positions.setdefault(value, []).append(index)
    best = 0
    for indices in positions.values():
        left = 0
        for right, index in enumerate(indices):
            while index - indices[left] - (right - left) > k:
                left += 1
            best = max(best, right - left + 1)
    return best


class Solution:
    def longestEqualSubarray(self, nums: list[int], k: int) -> int:
        return solve(nums, k)
