"""386. Lexicographical Numbers (Medium).

Specification: https://leetcode.com/problems/lexicographical-numbers/description/
"""


def solve(n: int) -> list[int]:
    return sorted(range(1, n + 1), key=str)


class Solution:
    def lexicalOrder(self, n: int) -> list[int]:
        return solve(n)
