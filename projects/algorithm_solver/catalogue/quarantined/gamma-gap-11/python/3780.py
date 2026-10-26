"""3780. Maximum Sum of Three Numbers Divisible by Three."""
from __future__ import annotations


def solve(nums: list[int]) -> int:
    """O(n) time and O(1) auxiliary space; descending cardinalities prevent reusing an index."""
    state = [[float('-inf')] * 3 for _ in range(4)]
    state[0][0] = 0
    for value in nums:
        for count in range(3, 0, -1):
            for remainder in range(3):
                total = state[count - 1][remainder] + value
                following = (remainder + value) % 3
                state[count][following] = max(state[count][following], total)
    return max(0, state[3][0])


class Solution:
    def maximumSum(self, nums: list[int]) -> int:
        return solve(nums)
