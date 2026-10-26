"""455. Assign Cookies (Easy).

Specification: https://leetcode.com/problems/assign-cookies/description/
"""


def solve(g: list[int], s: list[int]) -> int:
    """O(n log n + m log m) time, O(n + m) space; sort copies and satisfy least-greedy children first."""
    greed = sorted(g)
    cookies = sorted(s)
    child = 0
    for size in cookies:
        if child < len(greed) and size >= greed[child]:
            child += 1
    return child


class Solution:
    def findContentChildren(self, g: list[int], s: list[int]) -> int:
        return solve(g, s)
