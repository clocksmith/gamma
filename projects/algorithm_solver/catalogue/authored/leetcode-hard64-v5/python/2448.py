"""2448. Minimum Cost to Make Array Equal. Choose a weighted median and sum its absolute deviations."""


def solve(nums: list[int], cost: list[int]) -> int:
    """O(n log n) time and O(n) space. Inputs are preserved."""
    ordered = sorted(zip(nums, cost))
    total_weight = sum(cost)
    prefix_weight = 0
    median = ordered[0][0]
    for value, weight in ordered:
        prefix_weight += weight
        if 2 * prefix_weight >= total_weight:
            median = value
            break
    return sum(abs(value - median) * weight for value, weight in ordered)


class Solution:
    def minCost(self, nums: list[int], cost: list[int]) -> int:
        return solve(nums, cost)
