"""3194. Minimum Average of Smallest and Largest Elements (Easy).

Specification: https://leetcode.com/problems/minimum-average-of-smallest-and-largest-elements/description/
"""


def solve(nums: list[int]) -> float:
    """O(n log n) time, O(n) space; preserve nums; half-integer results are exactly representable."""
    ordered = sorted(nums)
    minimum_sum = ordered[0] + ordered[-1]
    for left in range(1, len(ordered) // 2):
        minimum_sum = min(minimum_sum, ordered[left] + ordered[len(ordered) - 1 - left])
    return minimum_sum / 2


class Solution:
    def minimumAverage(self, nums: list[int]) -> float:
        return solve(nums)
