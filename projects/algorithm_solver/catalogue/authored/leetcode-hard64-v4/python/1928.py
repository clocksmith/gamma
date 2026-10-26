"""1928. Minimum Cost to Reach Destination in Time."""


def solve(maxTime: int, edges: list[list[int]], passingFees: list[int]) -> int:
    """Exact-time dynamic programming on positive-duration edges; O(T*(V+E)) time and O(T*V) space. Inputs are preserved."""
    size = len(passingFees)
    best = [[float('inf')] * size for _ in range(maxTime + 1)]
    best[0][0] = passingFees[0]
    for elapsed in range(1, maxTime + 1):
        current = best[elapsed]
        for first, second, duration in edges:
            if duration <= elapsed:
                previous = best[elapsed - duration]
                current[first] = min(current[first], previous[second] + passingFees[first])
                current[second] = min(current[second], previous[first] + passingFees[second])
    answer = min(row[-1] for row in best)
    return -1 if answer == float('inf') else answer


class Solution:
    def minCost(self, maxTime: int, edges: list[list[int]], passingFees: list[int]) -> int:
        return solve(maxTime, edges, passingFees)
