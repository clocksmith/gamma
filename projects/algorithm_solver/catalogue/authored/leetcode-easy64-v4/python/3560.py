"""3560. Find Minimum Log Transportation Cost (Easy).

Specification: https://leetcode.com/problems/find-minimum-log-transportation-cost/description/
"""


def solve(n: int, m: int, k: int) -> int:
    """O(1) time and space; feasible inputs require at most one cut; products use exact integers."""
    excess = max(0, max(n, m) - k)
    return excess * k


class Solution:
    def minCuttingCost(self, n: int, m: int, k: int) -> int:
        return solve(n, m, k)
