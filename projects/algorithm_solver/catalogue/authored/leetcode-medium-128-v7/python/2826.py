"""2826. Sorting Three Groups: maintain minimal corrections for prefixes ending in each of the three ordered groups."""


def solve(nums: list[int]) -> int:
    """O(n) time and O(1) auxiliary space; inputs are read-only."""
    first = second = third = 0
    for value in nums:
        first, second, third = (first + int(value != 1),
                                min(first, second) + int(value != 2),
                                min(first, second, third) + int(value != 3))
    return min(first, second, third)


class Solution:
    def minimumOperations(self, nums: list[int]) -> int:
        return solve(nums)
