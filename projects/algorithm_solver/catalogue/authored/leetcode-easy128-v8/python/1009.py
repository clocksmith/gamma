"""1009. Complement of Base 10 Integer (Easy).

Specification: https://leetcode.com/problems/complement-of-base-10-integer/description/
"""


def solve(n: int) -> int:
    """O(log(n + 1)) time, O(1) space; subtract from a mask with the same binary width."""
    if n == 0:
        return 1
    power = 1
    while power <= n:
        power *= 2
    return power - 1 - n


class Solution:
    def bitwiseComplement(self, n: int) -> int:
        return solve(n)
