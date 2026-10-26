"""1664. Ways to Make a Fair Array: compare prefix totals with parity-flipped suffix totals after each deletion."""


def solve(nums: list[int]) -> int:
    """O(n) time and O(1) auxiliary space; inputs are read-only."""
    right_even = right_odd = 0
    for index, value in enumerate(nums):
        if index % 2 == 0:
            right_even += value
        else:
            right_odd += value
    left_even = left_odd = answer = 0
    for index, value in enumerate(nums):
        if index % 2 == 0:
            right_even -= value
        else:
            right_odd -= value
        if left_even + right_odd == left_odd + right_even:
            answer += 1
        if index % 2 == 0:
            left_even += value
        else:
            left_odd += value
    return answer


class Solution:
    def waysToMakeFair(self, nums: list[int]) -> int:
        return solve(nums)
