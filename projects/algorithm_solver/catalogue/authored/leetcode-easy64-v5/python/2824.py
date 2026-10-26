"""2824. Count Pairs Whose Sum is Less than Target (Easy).

Specification: https://leetcode.com/problems/count-pairs-whose-sum-is-less-than-target/description/
"""


def solve(nums: list[int], target: int) -> int:
    """O(n log n) time, O(n) space; sort a copy and preserve nums."""
    ordered = sorted(nums)
    left = 0
    right = len(ordered) - 1
    pairs = 0
    while left < right:
        if ordered[left] + ordered[right] < target:
            pairs += right - left
            left += 1
        else:
            right -= 1
    return pairs


class Solution:
    def countPairs(self, nums: list[int], target: int) -> int:
        return solve(nums, target)
