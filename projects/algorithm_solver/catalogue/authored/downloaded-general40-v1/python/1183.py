"""1183. Maximum Number of Ones (Hard).

Specification: https://leetcode.com/problems/maximum-number-of-ones/description/
"""


def solve(width: int, height: int, sideLength: int, maxOnes: int) -> int:
    counts = []
    for i in range(sideLength):
        rows = sum(1 for r in range(i, height, sideLength))
        for j in range(sideLength):
            cols = sum(1 for c in range(j, width, sideLength))
            counts.append(rows * cols)
    counts.sort(reverse=True)
    return sum(counts[:maxOnes])


class Solution:
    def maximumNumberOfOnes(self, width: int, height: int, sideLength: int, maxOnes: int) -> int:
        return solve(width, height, sideLength, maxOnes)
