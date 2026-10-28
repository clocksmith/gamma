from bisect import bisect_left


def solve(costs, capacity, budget):
    machines = sorted(zip(costs, capacity))
    ordered_costs = [x for x, _ in machines]
    prefix = []
    best = answer = 0
    for _, cap in machines:
        best = max(best, cap)
        prefix.append(best)
    for i, (cost, cap) in enumerate(machines):
        if cost < budget:
            answer = max(answer, cap)
        j = min(i - 1, bisect_left(ordered_costs, budget - cost) - 1)
        if j >= 0:
            answer = max(answer, cap + prefix[j])
    return answer


class Solution:
    def maxCapacity(self, costs, capacity, budget):
        return solve(costs, capacity, budget)
