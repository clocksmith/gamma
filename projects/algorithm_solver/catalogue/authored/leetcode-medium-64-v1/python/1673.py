"""1673. Find the Most Competitive Subsequence: spend the deletion budget on larger preceding values."""


def solve(nums: list[int], k: int) -> list[int]:
    """O(n) time and O(n) auxiliary space; inputs are read-only."""
    remaining = len(nums) - k
    stack = []
    for value in nums:
        while remaining and stack and stack[-1] > value:
            stack.pop()
            remaining -= 1
        stack.append(value)
    return stack[:k]


class Solution:
    def mostCompetitive(self, nums: list[int], k: int) -> list[int]:
        return solve(nums, k)
