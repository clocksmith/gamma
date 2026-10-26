"""830. Positions of Large Groups (Easy).

Specification: https://leetcode.com/problems/positions-of-large-groups/description/
"""


def solve(s: str) -> list[list[int]]:
    """O(n) time, O(1) auxiliary space excluding output; report inclusive bounds in order."""
    result = []
    start = 0
    while start < len(s):
        end = start + 1
        while end < len(s) and s[end] == s[start]:
            end += 1
        if end - start >= 3:
            result.append([start, end - 1])
        start = end
    return result


class Solution:
    def largeGroupPositions(self, s: str) -> list[list[int]]:
        return solve(s)
