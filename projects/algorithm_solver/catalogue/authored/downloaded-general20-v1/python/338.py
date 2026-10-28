"""338. Counting Bits (Easy).

Specification: https://leetcode.com/problems/counting-bits/description/
"""


def solve(n: int) -> list[int]:
    answer = [0] * (n + 1)
    for value in range(1, n + 1):
        answer[value] = answer[value >> 1] + (value & 1)
    return answer


class Solution:
    def countBits(self, n: int) -> list[int]:
        return solve(n)
