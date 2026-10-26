"""821. Shortest Distance to a Character (Easy).

Specification: https://leetcode.com/problems/shortest-distance-to-a-character/description/
"""


def solve(s: str, c: str) -> list[int]:
    """O(n) time and output space; combine nearest occurrences from both directions."""
    result = [0] * len(s)
    nearest = -len(s)
    for index, character in enumerate(s):
        if character == c:
            nearest = index
        result[index] = index - nearest
    nearest = 2 * len(s)
    for index in range(len(s) - 1, -1, -1):
        if s[index] == c:
            nearest = index
        result[index] = min(result[index], nearest - index)
    return result


class Solution:
    def shortestToChar(self, s: str, c: str) -> list[int]:
        return solve(s, c)
