"""3206. Alternating Groups I (Easy).

Specification: https://leetcode.com/problems/alternating-groups-i/description/
"""


def solve(colors: list[int]) -> int:
    """O(n) time, O(1) auxiliary space; count circular groups of exactly three tiles."""
    size = len(colors)
    groups = 0
    for center in range(size):
        previous = colors[(center + size - 1) % size]
        following = colors[(center + 1) % size]
        if colors[center] != previous and colors[center] != following:
            groups += 1
    return groups


class Solution:
    def numberOfAlternatingGroups(self, colors: list[int]) -> int:
        return solve(colors)
