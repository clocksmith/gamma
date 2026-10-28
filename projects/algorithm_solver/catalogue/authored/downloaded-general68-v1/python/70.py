"""70. Climbing Stairs (Easy).

Specification: https://leetcode.com/problems/climbing-stairs/description/
"""


def solve(n: int) -> int:
    if n <= 2:
        return n
    a, b = 1, 2
    for _i in range(3, n + 1):
        a, b = b, a + b
    return b


class Solution:
    def climbStairs(self, n: int) -> int:
        return solve(n)
