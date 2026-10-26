"""3684. Maximize Sum of At Most K Distinct Elements (Easy).

Specification: https://leetcode.com/problems/maximize-sum-of-at-most-k-distinct-elements/description/
"""


def solve(nums: list[int], k: int) -> list[int]:
    """O(n + u * log(u + 1)) expected time, O(u) space; preserve nums; output descending values."""
    values = sorted(set(nums), reverse=True)
    return values[:k]


class Solution:
    def maxKDistinct(self, nums: list[int], k: int) -> list[int]:
        return solve(nums, k)
