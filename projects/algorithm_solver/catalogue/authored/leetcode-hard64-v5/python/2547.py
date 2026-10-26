"""2547. Minimum Cost to Split an Array. Prefix DP with incremental duplicate penalties for each final segment."""


def solve(nums: list[int], k: int) -> int:
    """O(n^2) time and O(n) space. Inputs are preserved."""
    size = len(nums)
    best = [0] + [float("inf")] * size
    for end in range(1, size + 1):
        counts = {}
        penalty = 0
        for start in range(end - 1, -1, -1):
            value = nums[start]
            counts[value] = counts.get(value, 0) + 1
            if counts[value] == 2:
                penalty += 2
            elif counts[value] > 2:
                penalty += 1
            best[end] = min(best[end], best[start] + k + penalty)
    return best[size]


class Solution:
    def minCost(self, nums: list[int], k: int) -> int:
        return solve(nums, k)
