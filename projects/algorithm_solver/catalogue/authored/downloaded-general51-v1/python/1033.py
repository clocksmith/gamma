"""1033. Moving Stones Until Consecutive (Medium).

Specification: https://leetcode.com/problems/moving-stones-until-consecutive/description/
"""


def solve(a: int, b: int, c: int) -> list[int]:
    x, y, z = sorted([a, b, c])
    if z - x == 2:
        return [0, 0]
    minimum = 1 if (y - x <= 2 or z - y <= 2) else 2
    return [minimum, z - x - 2]


class Solution:
    def numMovesStones(self, a: int, b: int, c: int) -> list[int]:
        return solve(a, b, c)
