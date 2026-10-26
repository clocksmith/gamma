"""2560. House Robber IV: binary search the smallest capability allowing a greedy nonadjacent selection."""


def solve(nums: list[int], k: int) -> int:
    """O(n log(M + 1)) time and O(1) auxiliary space, where M is the largest value; inputs are read-only."""
    low, high = min(nums), max(nums)
    while low < high:
        capability = (low + high) // 2
        count = index = 0
        while index < len(nums):
            if nums[index] <= capability:
                count += 1
                index += 2
            else:
                index += 1
        if count >= k:
            high = capability
        else:
            low = capability + 1
    return low


class Solution:
    def minCapability(self, nums: list[int], k: int) -> int:
        return solve(nums, k)
