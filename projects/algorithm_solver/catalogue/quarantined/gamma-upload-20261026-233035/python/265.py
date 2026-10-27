"""265. Paint House II."""
def solve(costs: list[list[int]]) -> int:
    if not costs:
        return 0
    previous = [0] * len(costs[0])
    for row in costs:
        first = min(range(len(previous)), key=previous.__getitem__)
        second_value = min(previous[index] for index in range(len(previous)) if index != first) if len(previous) > 1 else float('inf')
        current = [cost + (second_value if color == first else previous[first]) for color, cost in enumerate(row)]
        previous = current
    return min(previous)

class Solution:
    def minCostII(self, costs: list[list[int]]) -> int:
        return solve(costs)
