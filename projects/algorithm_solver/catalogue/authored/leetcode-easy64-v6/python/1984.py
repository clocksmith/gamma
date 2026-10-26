"""1984. Minimum Difference Between Highest and Lowest of K Scores (Easy).

Specification: https://leetcode.com/problems/minimum-difference-between-highest-and-lowest-of-k-scores/description/
"""


def solve(nums: list[int], k: int) -> int:
    """O(n log n) time, O(n) space; compare sorted length-k windows without mutating nums."""
    values = sorted(nums)
    smallest = values[k - 1] - values[0]
    for right in range(k, len(values)):
        smallest = min(smallest, values[right] - values[right - k + 1])
    return smallest


class Solution:
    def minimumDifference(self, nums: list[int], k: int) -> int:
        return solve(nums, k)
