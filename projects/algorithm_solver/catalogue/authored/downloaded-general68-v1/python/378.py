"""378. Kth Smallest Element in a Sorted Matrix (Medium).

Specification: https://leetcode.com/problems/kth-smallest-element-in-a-sorted-matrix/description/
"""


def solve(matrix: list[list[int]], k: int) -> int:
    flat = [value for row in matrix for value in row]
    flat.sort()
    return flat[k - 1]


class Solution:
    def kthSmallest(self, matrix: list[list[int]], k: int) -> int:
        return solve(matrix, k)
