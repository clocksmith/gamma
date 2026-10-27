"""3700. Number of ZigZag Arrays II
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/number-of-zigzag-arrays-ii/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3700-3799/3700.Number%20of%20ZigZag%20Arrays%20II/README_EN.md
Complexity: O((r-l+1)^3 log n) time; O((r-l+1)^2) space.
Uses reflection to reduce the transition to m states. Split integer multiplication preserves exact modular arithmetic in JavaScript.
"""

from __future__ import annotations

def solve(n, l, r):
    modulus = 1_000_000_007
    width = r - l + 1
    # Reflection maps descending-ending counts to ascending-ending counts.
    matrix = [[int(column >= width - row) for column in range(width)] for row in range(width)]
    vector = [1] * width
    exponent = n - 1
    def square(matrix):
        columns = list(zip(*matrix))
        return [[sum(a * b for a, b in zip(row, column)) % modulus for column in columns] for row in matrix]
    while exponent:
        if exponent % 2:
            vector = [sum(value * entry for value, entry in zip(row, vector)) % modulus for row in matrix]
        exponent //= 2
        if exponent:
            matrix = square(matrix)
    return 2 * sum(vector) % modulus


class Solution:
    def zigZagArrays(self, n, l, r):
        return solve(n, l, r)
