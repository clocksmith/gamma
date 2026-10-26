"""2240. Number of Ways to Buy Pens and Pencils: enumerate the more expensive item and count affordable quantities of the other."""


def solve(total: int, cost1: int, cost2: int) -> int:
    """O(total / max(cost1, cost2) + 1) time and O(1) auxiliary space; inputs are read-only."""
    expensive, cheap = max(cost1, cost2), min(cost1, cost2)
    answer = 0
    for spent in range(0, total + 1, expensive):
        answer += (total - spent) // cheap + 1
    return answer


class Solution:
    def waysToBuyPensPencils(self, total: int, cost1: int, cost2: int) -> int:
        return solve(total, cost1, cost2)
