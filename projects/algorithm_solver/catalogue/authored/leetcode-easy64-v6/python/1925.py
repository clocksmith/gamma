"""1925. Count Square Sum Triples (Easy).

Specification: https://leetcode.com/problems/count-square-sum-triples/description/
"""


def solve(n: int) -> int:
    """O(n^2) expected time, O(n) space; exact square membership counts both orders of the legs."""
    squares = {value * value for value in range(1, n + 1)}
    result = 0
    for first in range(1, n + 1):
        for second in range(1, n + 1):
            if first * first + second * second in squares:
                result += 1
    return result


class Solution:
    def countTriples(self, n: int) -> int:
        return solve(n)
