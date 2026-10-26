"""2078. Two Furthest Houses With Different Colors (Easy).

Specification: https://leetcode.com/problems/two-furthest-houses-with-different-colors/description/
"""


def solve(colors: list[int]) -> int:
    """O(n) time, O(1) space; an optimal pair can use an endpoint."""
    last = len(colors) - 1
    result = 0
    for index, color in enumerate(colors):
        if color != colors[0]:
            result = max(result, index)
        if color != colors[last]:
            result = max(result, last - index)
    return result


class Solution:
    def maxDistance(self, colors: list[int]) -> int:
        return solve(colors)
