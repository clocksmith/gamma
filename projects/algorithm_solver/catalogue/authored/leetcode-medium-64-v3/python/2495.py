"""2495. Number of Subarrays Having Even Product: subtract all-odd endings from all endings at each position."""


def solve(nums: list[int]) -> int:
    """O(n) time and O(1) auxiliary space; inputs are read-only."""
    odd_run = answer = 0
    for index, value in enumerate(nums):
        odd_run = odd_run + 1 if value % 2 else 0
        answer += index + 1 - odd_run
    return answer


class Solution:
    def evenProduct(self, nums: list[int]) -> int:
        return solve(nums)
