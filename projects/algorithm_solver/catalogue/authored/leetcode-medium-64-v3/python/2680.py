"""2680. Maximum OR: combine prefix and suffix ORs with all shifts on one element."""


def solve(nums: list[int], k: int) -> int:
    """O(n) time and O(n) auxiliary space on the bounded integer domain; inputs are read-only."""
    suffix = [0] * (len(nums) + 1)
    for index in range(len(nums) - 1, -1, -1):
        suffix[index] = suffix[index + 1] | nums[index]
    prefix = best = 0
    for index, value in enumerate(nums):
        best = max(best, prefix | (value << k) | suffix[index + 1])
        prefix |= value
    return best


class Solution:
    def maximumOr(self, nums: list[int], k: int) -> int:
        return solve(nums, k)
