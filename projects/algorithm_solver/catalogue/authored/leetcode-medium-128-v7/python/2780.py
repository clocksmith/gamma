"""2780. Minimum Index of a Valid Split: find the dominant candidate and check both sides of each split."""


def solve(nums: list[int]) -> int:
    """O(n) time and O(1) auxiliary space; inputs are read-only."""
    candidate = balance = 0
    for value in nums:
        if balance == 0:
            candidate = value
        balance += 1 if value == candidate else -1
    total = nums.count(candidate)
    prefix = 0
    for index in range(len(nums) - 1):
        prefix += int(nums[index] == candidate)
        if 2 * prefix > index + 1 and 2 * (total - prefix) > len(nums) - index - 1:
            return index
    return -1


class Solution:
    def minimumIndex(self, nums: list[int]) -> int:
        return solve(nums)
