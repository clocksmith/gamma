"""201. Bitwise AND of Numbers Range (Medium).

Specification: https://leetcode.com/problems/bitwise-and-of-numbers-range/description/
"""


def solve(left: int, right: int) -> int:
    shift = 0
    while left < right:
        left //= 2
        right //= 2
        shift += 1
    return left * (2 ** shift)


class Solution:
    def rangeBitwiseAnd(self, left: int, right: int) -> int:
        return solve(left, right)
