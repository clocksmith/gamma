"""Original frontend 808 variant; qualification not qualified."""

def solve(n):
    units = (n + 24) // 25
    if units >= 200:
        return 1.0
    table = [[0.0] * (units + 1) for _ in range(units + 1)]

    def value(a, b):
        if a <= 0 and b <= 0:
            return 0.5
        if a <= 0:
            return 1.0
        if b <= 0:
            return 0.0
        return table[a][b]

    for a in range(1, units + 1):
        for b in range(1, units + 1):
            table[a][b] = 0.25 * (value(a - 4, b) + value(a - 3, b - 1) + value(a - 2, b - 2) + value(a - 1, b - 3))
    return value(units, units)


class Solution:
    def soupServings(self, n):
        return solve(n)
