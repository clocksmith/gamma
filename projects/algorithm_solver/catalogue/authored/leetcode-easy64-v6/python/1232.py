"""1232. Check If It Is a Straight Line (Easy).

Specification: https://leetcode.com/problems/check-if-it-is-a-straight-line/description/
"""


def solve(coordinates: list[list[int]]) -> bool:
    """O(n) time, O(1) space; exact cross products in the public domain; preserve inputs."""
    origin_x, origin_y = coordinates[0]
    delta_x = coordinates[1][0] - origin_x
    delta_y = coordinates[1][1] - origin_y
    for index in range(2, len(coordinates)):
        x, y = coordinates[index]
        if (x - origin_x) * delta_y != (y - origin_y) * delta_x:
            return False
    return True


class Solution:
    def checkStraightLine(self, coordinates: list[list[int]]) -> bool:
        return solve(coordinates)
