"""1646. Get Maximum in Generated Array (Easy).

Specification: https://leetcode.com/problems/get-maximum-in-generated-array/description/
"""


def solve(n: int) -> int:
    """O(n) time and space; generated values are local to this call."""
    if n <= 1:
        return n
    values = [0] * (n + 1)
    values[1] = 1
    maximum = 1
    for index in range(2, n + 1):
        half = index // 2
        values[index] = values[half]
        if index % 2 == 1:
            values[index] += values[half + 1]
        maximum = max(maximum, values[index])
    return maximum


class Solution:
    def getMaximumGenerated(self, n: int) -> int:
        return solve(n)
