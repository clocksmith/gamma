"""2044. Count Number of Maximum Bitwise-OR Subsets: enumerate inclusion choices while carrying their accumulated bitwise OR."""


def solve(nums: list[int]) -> int:
    """O(2^n) time and O(n) auxiliary stack space; inputs are read-only."""
    target = 0
    for value in nums:
        target |= value

    def count(index: int, value: int) -> int:
        if index == len(nums):
            return int(value == target)
        return count(index + 1, value) + count(index + 1, value | nums[index])

    return count(0, 0) - int(target == 0)


class Solution:
    def countMaxOrSubsets(self, nums: list[int]) -> int:
        return solve(nums)
