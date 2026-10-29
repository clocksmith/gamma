# 514 — Freedom Trail. Original implementation; authored candidate, not independently qualified.
def solve(ring, key):
    positions = {}
    for i, char in enumerate(ring):
        positions.setdefault(char, []).append(i)
    costs = {0: 0}
    for char in key:
        costs = {end: min(cost + min(abs(start - end), len(ring) - abs(start - end)) + 1
                          for start, cost in costs.items()) for end in positions[char]}
    return min(costs.values())

findRotateSteps = solve

class Solution:
    findRotateSteps = staticmethod(solve)
