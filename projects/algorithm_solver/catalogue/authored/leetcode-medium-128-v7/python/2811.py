"""2811. Check if it is Possible to Split Array: use an adjacent qualifying pair as the final nonsingleton piece."""


def solve(nums: list[int], m: int) -> bool:
    """O(n) time and O(1) auxiliary space for positive inputs; inputs are read-only."""
    if len(nums) <= 2:
        return True
    return any(nums[index - 1] + nums[index] >= m for index in range(1, len(nums)))


class Solution:
    def canSplitArray(self, nums: list[int], m: int) -> bool:
        return solve(nums, m)
