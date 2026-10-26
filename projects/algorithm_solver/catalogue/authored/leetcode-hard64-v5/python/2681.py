"""2681. Power of Heroes. Accumulate contributions by maximum with a running sum of subset minima."""


def solve(nums: list[int]) -> int:
    """O(n log n) time and O(n) space. Inputs are preserved."""
    modulus = 1_000_000_007
    minima = 0
    answer = 0
    for value in sorted(nums):
        answer = (answer + value * value % modulus * (value + minima)) % modulus
        minima = (2 * minima + value) % modulus
    return answer


class Solution:
    def sumOfPower(self, nums: list[int]) -> int:
        return solve(nums)
