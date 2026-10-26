"""1304. Find N Unique Integers Sum up to Zero (Easy).

Specification: https://leetcode.com/problems/find-n-unique-integers-sum-up-to-zero/description/
"""


def solve(n: int) -> list[int]:
    """O(n) time and result space; deterministic opposite pairs, then zero if needed."""
    result = []
    for value in range(1, n // 2 + 1):
        result.extend([-value, value])
    if n % 2 == 1:
        result.append(0)
    return result


class Solution:
    def sumZero(self, n: int) -> list[int]:
        return solve(n)
