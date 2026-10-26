"""3516. Find Closest Person (Easy).

Specification: https://leetcode.com/problems/find-closest-person/description/
"""


def solve(x: int, y: int, z: int) -> int:
    """O(1) time and space; return zero when the two distances are equal."""
    first_distance = abs(x - z)
    second_distance = abs(y - z)
    if first_distance < second_distance:
        return 1
    if second_distance < first_distance:
        return 2
    return 0


class Solution:
    def findClosest(self, x: int, y: int, z: int) -> int:
        return solve(x, y, z)
