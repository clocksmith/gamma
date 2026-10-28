"""378. Kth Smallest Element in a Sorted Matrix (Medium).

Specification: https://leetcode.com/problems/kth-smallest-element-in-a-sorted-matrix/description/
"""


def solve(matrix: list[list[int]], k: int) -> int:
    import heapq
    import itertools
    return next(itertools.islice(heapq.merge(*matrix), k - 1, None))


class Solution:
    def kthSmallest(self, matrix: list[list[int]], k: int) -> int:
        return solve(matrix, k)
