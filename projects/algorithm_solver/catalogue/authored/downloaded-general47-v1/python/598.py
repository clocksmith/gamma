"""598. Range Addition II (Easy).

Specification: https://leetcode.com/problems/range-addition-ii/description/
"""


def solve(m: int, n: int, ops: list[list[int]]) -> int:
    if not ops:
        return m * n
    min_row = min(op[0] for op in ops)
    min_col = min(op[1] for op in ops)
    return min_row * min_col


class Solution:
    def maxCount(self, m: int, n: int, ops: list[list[int]]) -> int:
        return solve(m, n, ops)
