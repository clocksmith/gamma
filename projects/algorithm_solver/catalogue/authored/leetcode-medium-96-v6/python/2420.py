"""2420. Find All Good Indices: check monotone runs immediately before and after each excluded center."""


def solve(nums: list[int], k: int) -> list[int]:
    """O(n) time and O(n) auxiliary and result space; inputs are read-only."""
    size = len(nums)
    before = [1] * size
    after = [1] * size
    for index in range(1, size):
        if nums[index] <= nums[index - 1]:
            before[index] = before[index - 1] + 1
    for index in range(size - 2, -1, -1):
        if nums[index] <= nums[index + 1]:
            after[index] = after[index + 1] + 1
    return [index for index in range(k, size - k)
            if before[index - 1] >= k and after[index + 1] >= k]


class Solution:
    def goodIndices(self, nums: list[int], k: int) -> list[int]:
        return solve(nums, k)
