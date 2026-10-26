"""2103. Rings and Rods (Easy).

Specification: https://leetcode.com/problems/rings-and-rods/description/
"""


def solve(rings: str) -> int:
    """O(n) time, O(1) space; use a three-bit color mask for each of ten rods."""
    rods = [0] * 10
    colors = {'R': 1, 'G': 2, 'B': 4}
    for index in range(0, len(rings), 2):
        rod = ord(rings[index + 1]) - 48
        rods[rod] |= colors[rings[index]]
    return sum(mask == 7 for mask in rods)


class Solution:
    def countPoints(self, rings: str) -> int:
        return solve(rings)
