"""1496. Path Crossing (Easy).

Specification: https://leetcode.com/problems/path-crossing/description/
"""


def solve(path: str) -> bool:
    """O(n) expected time, O(n) space under the bounded coordinate domain."""
    x, y = 0, 0
    visited = {(0, 0)}
    for direction in path:
        if direction == 'N':
            y += 1
        elif direction == 'S':
            y -= 1
        elif direction == 'E':
            x += 1
        else:
            x -= 1
        position = (x, y)
        if position in visited:
            return True
        visited.add(position)
    return False


class Solution:
    def isPathCrossing(self, path: str) -> bool:
        return solve(path)
