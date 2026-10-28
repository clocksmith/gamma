"""554. Brick Wall (Medium).

Specification: https://leetcode.com/problems/brick-wall/description/
"""


def solve(wall: list[list[int]]) -> int:
    counts = {}
    for row in wall:
        position = 0
        for i in range(len(row) - 1):
            position += row[i]
            counts[position] = counts.get(position, 0) + 1
    best = max(counts.values()) if counts else 0
    return len(wall) - best


class Solution:
    def leastBricks(self, wall: list[list[int]]) -> int:
        return solve(wall)
