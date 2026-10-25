"""2587. Rearrange Array to Maximize Prefix Score: put larger values first to maximize every prefix."""


def solve(nums: list[int]) -> int:
    """O(n log n) time and O(n) auxiliary space; inputs are read-only."""
    values = sorted(nums, reverse=True)
    prefix = score = 0
    for value in values:
        prefix += value
        if prefix <= 0:
            break
        score += 1
    return score


class Solution:
    def maxScore(self, nums: list[int]) -> int:
        return solve(nums)
