"""514. Freedom Trail."""

from collections import defaultdict

def solve(ring: str, key: str) -> int:
    positions = defaultdict(list)
    for i, char in enumerate(ring):
        positions[char].append(i)
    costs = {0: 0}
    n = len(ring)
    for char in key:
        following = {}
        for position in positions[char]:
            following[position] = min(cost + min(abs(position - previous), n - abs(position - previous)) + 1
                                      for previous, cost in costs.items())
        costs = following
    return min(costs.values())


class Solution:
    def findRotateSteps(self, ring: str, key: str) -> int:
        return solve(ring, key)
