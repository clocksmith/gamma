"""3809. Best Reachable Tower."""
from __future__ import annotations


def solve(towers: list[list[int]], center: list[int], radius: int) -> list[int]:
    """O(n) time and O(1) auxiliary space; returns fresh coordinates and preserves inputs."""
    best = [-1, -1]
    quality = -1
    for x, y, value in towers:
        if abs(x - center[0]) + abs(y - center[1]) > radius:
            continue
        if value > quality or (value == quality and (x, y) < (best[0], best[1])):
            quality = value
            best = [x, y]
    return best


class Solution:
    def bestTower(self, towers: list[list[int]], center: list[int], radius: int) -> list[int]:
        return solve(towers, center, radius)
