"""1791. Find Center of Star Graph (Easy).

Specification: https://leetcode.com/problems/find-center-of-star-graph/description/
"""


def solve(edges: list[list[int]]) -> int:
    """O(1) time and space; the first two edges share the guaranteed star center."""
    candidate = edges[0][0]
    return candidate if candidate == edges[1][0] or candidate == edges[1][1] else edges[0][1]


class Solution:
    def findCenter(self, edges: list[list[int]]) -> int:
        return solve(edges)
