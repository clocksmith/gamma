"""970. Powerful Integers (Medium).

Specification: https://leetcode.com/problems/powerful-integers/description/
"""


def solve(x: int, y: int, bound: int) -> list[int]:
    x_powers = []
    value = 1
    while value <= bound:
        x_powers.append(value)
        if x == 1:
            break
        value *= x
    y_powers = []
    value = 1
    while value <= bound:
        y_powers.append(value)
        if y == 1:
            break
        value *= y
    result = set()
    for a in x_powers:
        for b in y_powers:
            if a + b <= bound:
                result.add(a + b)
    return sorted(result)


class Solution:
    def powerfulIntegers(self, x: int, y: int, bound: int) -> list[int]:
        return solve(x, y, bound)
