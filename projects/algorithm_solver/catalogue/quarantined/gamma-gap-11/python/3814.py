"""3814. Maximum Capacity Within Budget."""
from __future__ import annotations
from bisect import bisect_left


def solve(costs: list[int], capacity: list[int], budget: int) -> int:
    """O(n log n) time and O(n) space; strictly enforces budget and distinct machine indices."""
    machines = sorted(zip(costs, capacity))
    ordered_costs = [cost for cost, _ in machines]
    prefix_best = []
    answer = 0
    for index, (cost, value) in enumerate(machines):
        if cost < budget:
            answer = max(answer, value)
        partner = min(index, bisect_left(ordered_costs, budget - cost)) - 1
        if partner >= 0:
            answer = max(answer, value + prefix_best[partner])
        prefix_best.append(max(value, prefix_best[-1] if prefix_best else 0))
    return answer


class Solution:
    def maxCapacity(self, costs: list[int], capacity: list[int], budget: int) -> int:
        return solve(costs, capacity, budget)
