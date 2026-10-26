"""2745. Construct the Longest New String: alternate AA and BB blocks and insert all AB blocks."""


def solve(x: int, y: int, z: int) -> int:
    """O(1) time and O(1) auxiliary space; inputs are read-only."""
    return 4 * min(x, y) + 2 * z + (2 if x != y else 0)


class Solution:
    def longestString(self, x: int, y: int, z: int) -> int:
        return solve(x, y, z)
