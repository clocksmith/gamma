"""Original frontend 2931 variant; qualification unknown."""


def solve(values) -> int:
    flat = sorted(x for row in values for x in row)
    return sum((i + 1) * v for i, v in enumerate(flat))


maxSpending = solve


class Solution:
    def maxSpending(self, values) -> int:
        return solve(values)
