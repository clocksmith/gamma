"""2862. Maximum Element-Sum of a Complete Subset of Indices. Enumerate positive square-multiple index groups."""


def solve(nums: list[int]) -> int:
    """O(n) time and O(1) space; sum of floor(sqrt(n/base)) is at most 2*n. Inputs are preserved."""
    size = len(nums)
    answer = 0
    for base in range(1, size + 1):
        total = 0
        multiplier = 1
        while base * multiplier * multiplier <= size:
            total += nums[base * multiplier * multiplier - 1]
            multiplier += 1
        answer = max(answer, total)
    return answer


class Solution:
    def maximumSum(self, nums: list[int]) -> int:
        return solve(nums)
