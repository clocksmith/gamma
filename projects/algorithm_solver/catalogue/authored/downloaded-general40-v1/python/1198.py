"""1198. Find Smallest Common Element in All Rows (Medium).

Specification: https://leetcode.com/problems/find-smallest-common-element-in-all-rows/description/
"""


def solve(mat: list[list[int]]) -> int:
    counts = {}
    for row in mat:
        for value in set(row):
            counts[value] = counts.get(value, 0) + 1
    best = float('inf')
    for value, count in counts.items():
        if count == len(mat):
            best = min(best, value)
    return -1 if best == float('inf') else best


class Solution:
    def smallestCommonElement(self, mat: list[list[int]]) -> int:
        return solve(mat)
