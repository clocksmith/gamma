"""3870. Count Commas in Range (Easy).

Specification: https://leetcode.com/problems/count-commas-in-range/description/
"""


def solve(n: int) -> int:
    """O(1) time and space; the declared bound n <= 100000 permits at most one comma per number."""
    return max(0, n - 999)


class Solution:
    def countCommas(self, n: int) -> int:
        return solve(n)
