"""2568. Minimum Impossible OR: find the first missing power of two since smaller powers generate every smaller value."""


def solve(nums: list[int]) -> int:
    """O(n + log(M + 1)) expected time and O(n) auxiliary space; inputs are read-only."""
    present = set(nums)
    value = 1
    while value in present:
        value *= 2
    return value


class Solution:
    def minImpossibleOR(self, nums: list[int]) -> int:
        return solve(nums)
