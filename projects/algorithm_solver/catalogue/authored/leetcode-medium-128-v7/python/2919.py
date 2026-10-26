"""2919. Minimum Increment Operations to Make Array Beautiful: ensure every length-three window contains a raised element using three rolling costs."""


def solve(nums: list[int], k: int) -> int:
    """O(n) time and O(1) auxiliary space; inputs are read-only."""
    first = second = third = 0
    for value in nums:
        current = min(first, second, third) + max(0, k - value)
        first, second, third = second, third, current
    return min(first, second, third)


class Solution:
    def minIncrementOperations(self, nums: list[int], k: int) -> int:
        return solve(nums, k)
