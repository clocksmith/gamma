"""3789. Minimum Cost to Acquire Required Items."""
from __future__ import annotations


def solve(cost1: int, cost2: int, costBoth: int, need1: int, need2: int) -> int:
    """O(1) time and O(1) space; a piecewise-linear optimum occurs at one of three demand breakpoints."""
    answer = cost1 * need1 + cost2 * need2
    for both in (min(need1, need2), max(need1, need2)):
        cost = both * costBoth + max(0, need1 - both) * cost1 + max(0, need2 - both) * cost2
        answer = min(answer, cost)
    return answer


class Solution:
    def minimumCost(self, cost1: int, cost2: int, costBoth: int, need1: int, need2: int) -> int:
        return solve(cost1, cost2, costBoth, need1, need2)
