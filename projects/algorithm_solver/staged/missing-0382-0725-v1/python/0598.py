"""598. Range Addition II."""

def solve(m: int, n: int, ops: list[list[int]]) -> int:
    for rows, cols in ops:
        m = min(m, rows)
        n = min(n, cols)
    return m * n


class Solution:
    def maxCount(self, m: int, n: int, ops: list[list[int]]) -> int:
        return solve(m, n, ops)
