"""1015. Smallest Integer Divisible by K (Medium).

Specification: https://leetcode.com/problems/smallest-integer-divisible-by-k/description/
"""


def solve(k: int) -> int:
    if k % 2 == 0 or k % 5 == 0:
        return -1
    remainder = 0
    for length in range(1, k + 1):
        remainder = (remainder * 10 + 1) % k
        if remainder == 0:
            return length
    return -1


class Solution:
    def smallestRepunitDivByK(self, k: int) -> int:
        return solve(k)
