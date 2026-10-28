"""386. Lexicographical Numbers (Medium).

Specification: https://leetcode.com/problems/lexicographical-numbers/description/
"""


def solve(n: int) -> list[int]:
    result = []
    current = 1
    for _ in range(n):
        result.append(current)
        if current * 10 <= n:
            current *= 10
        else:
            while current % 10 == 9 or current + 1 > n:
                current //= 10
            current += 1
    return result


class Solution:
    def lexicalOrder(self, n: int) -> list[int]:
        return solve(n)
