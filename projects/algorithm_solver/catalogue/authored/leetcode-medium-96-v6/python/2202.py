"""2202. Maximize the Topmost Element After K Moves: compare recoverable removed elements with the untouched kth element."""


def solve(nums: list[int], k: int) -> int:
    """O(min(n, k) + 1) time and O(1) auxiliary space; inputs are read-only."""
    if k == 0:
        return nums[0]
    if len(nums) == 1:
        return nums[0] if k % 2 == 0 else -1
    best = -1
    for index in range(min(len(nums), k - 1)):
        best = max(best, nums[index])
    if k < len(nums):
        best = max(best, nums[k])
    return best


class Solution:
    def maximumTop(self, nums: list[int], k: int) -> int:
        return solve(nums, k)
