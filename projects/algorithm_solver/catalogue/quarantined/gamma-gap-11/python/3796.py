"""3796. Find Maximum Value in a Constrained Sequence."""
from __future__ import annotations


def solve(n: int, restrictions: list[list[int]], diff: list[int]) -> int:
    """O(n + r) time and O(n) space; two passes compute the greatest feasible Lipschitz envelope."""
    bound = [float('inf')] * n
    bound[0] = 0
    for index, maximum in restrictions:
        bound[index] = min(bound[index], maximum)
    for index in range(1, n):
        bound[index] = min(bound[index], bound[index - 1] + diff[index - 1])
    for index in range(n - 2, -1, -1):
        bound[index] = min(bound[index], bound[index + 1] + diff[index])
    return max(bound)


class Solution:
    def findMaxVal(self, n: int, restrictions: list[list[int]], diff: list[int]) -> int:
        return solve(n, restrictions, diff)
