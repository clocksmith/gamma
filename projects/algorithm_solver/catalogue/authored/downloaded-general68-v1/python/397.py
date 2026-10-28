"""397. Integer Replacement (Medium).

Specification: https://leetcode.com/problems/integer-replacement/description/
"""


def solve(n: int) -> int:
    steps = 0
    value = n
    while value != 1:
        if value % 2 == 0:
            value //= 2
        elif value == 3 or value % 4 == 1:
            value -= 1
        else:
            value += 1
        steps += 1
    return steps


class Solution:
    def integerReplacement(self, n: int) -> int:
        return solve(n)
