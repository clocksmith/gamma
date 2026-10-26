"""2833. Furthest Point From Origin (Easy).

Specification: https://leetcode.com/problems/furthest-point-from-origin/description/
"""


def solve(moves: str) -> int:
    """O(n) time, O(1) space; direct every underscore toward the larger displacement."""
    displacement = 0
    flexible = 0
    for move in moves:
        if move == 'L':
            displacement -= 1
        elif move == 'R':
            displacement += 1
        else:
            flexible += 1
    return abs(displacement) + flexible


class Solution:
    def furthestDistanceFromOrigin(self, moves: str) -> int:
        return solve(moves)
