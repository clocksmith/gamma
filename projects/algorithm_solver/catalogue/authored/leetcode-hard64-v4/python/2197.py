"""2197. Replace Non-Coprime Numbers in Array."""

from math import gcd


def solve(nums: list[int]) -> list[int]:
    """Stack of merged adjacent values; O(n log M) time and O(n) space, M bounds intermediate values. Inputs are preserved."""
    stack = []
    for value in nums:
        while stack:
            common = gcd(stack[-1], value)
            if common == 1:
                break
            value = stack.pop() // common * value
        stack.append(value)
    return stack


class Solution:
    def replaceNonCoprimes(self, nums: list[int]) -> list[int]:
        return solve(nums)
