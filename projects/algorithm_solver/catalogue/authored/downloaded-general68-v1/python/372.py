"""372. Super Pow (Medium).

Specification: https://leetcode.com/problems/super-pow/description/
"""


def solve(a: int, b: list[int]) -> int:
    result = 1
    for digit in b:
        result = (pow(result, 10, 1337) * pow(a, digit, 1337)) % 1337
    return result


class Solution:
    def superPow(self, a: int, b: list[int]) -> int:
        return solve(a, b)
