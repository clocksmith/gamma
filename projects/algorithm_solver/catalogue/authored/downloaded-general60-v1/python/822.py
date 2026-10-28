"""822. Card Flipping Game (Medium).

Specification: https://leetcode.com/problems/card-flipping-game/description/
"""


def solve(fronts: list[int], backs: list[int]) -> int:
    bad = {fronts[i] for i in range(len(fronts)) if fronts[i] == backs[i]}
    best = float('inf')
    for value in fronts + backs:
        if value not in bad:
            best = min(best, value)
    return 0 if best == float('inf') else best


class Solution:
    def flipgame(self, fronts: list[int], backs: list[int]) -> int:
        return solve(fronts, backs)
