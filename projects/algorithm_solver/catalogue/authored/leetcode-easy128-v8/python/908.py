"""908. Smallest Range I (Easy).

Specification: https://leetcode.com/problems/smallest-range-i/description/
"""


def solve(nums: list[int], k: int) -> int:
    """O(n) time, O(1) space; both extremes can move inward by at most k."""
    smallest = largest = nums[0]
    for value in nums:
        smallest = min(smallest, value)
        largest = max(largest, value)
    return max(0, largest - smallest - 2 * k)


class Solution:
    def smallestRangeI(self, nums: list[int], k: int) -> int:
        return solve(nums, k)
