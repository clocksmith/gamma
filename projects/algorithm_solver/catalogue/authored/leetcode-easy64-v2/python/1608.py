"""1608. Special Array With X Elements Greater Than or Equal X (Easy).

Specification: https://leetcode.com/problems/special-array-with-x-elements-greater-than-or-equal-x/description/
"""


def solve(nums: list[int]) -> int:
    """O(n) time, O(n) space; nonnegative values are counted without mutating nums."""
    size = len(nums)
    counts = [0] * (size + 1)
    for value in nums:
        counts[min(size, value)] += 1
    at_least = 0
    for candidate in range(size, 0, -1):
        at_least += counts[candidate]
        if at_least == candidate:
            return candidate
    return -1


class Solution:
    def specialArray(self, nums: list[int]) -> int:
        return solve(nums)
