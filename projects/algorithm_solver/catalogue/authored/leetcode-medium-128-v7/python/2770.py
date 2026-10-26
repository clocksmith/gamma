"""2770. Maximum Number of Jumps to Reach the Last Index: compute the longest reachable path through increasing array indices."""


def solve(nums: list[int], target: int) -> int:
    """O(n * n) time and O(n) auxiliary space; inputs are read-only."""
    jumps = [-1] * len(nums)
    jumps[0] = 0
    for right in range(1, len(nums)):
        for left in range(right):
            if jumps[left] != -1 and abs(nums[right] - nums[left]) <= target:
                jumps[right] = max(jumps[right], jumps[left] + 1)
    return jumps[-1]


class Solution:
    def maximumJumps(self, nums: list[int], target: int) -> int:
        return solve(nums, target)
