"""2027. Minimum Moves to Convert String (Easy).

Specification: https://leetcode.com/problems/minimum-moves-to-convert-string/description/
"""


def solve(s: str) -> int:
    """O(n) time, O(1) space; greedily cover the leftmost X with a length-three operation."""
    moves = 0
    index = 0
    while index < len(s):
        if s[index] == 'X':
            moves += 1
            index += 3
        else:
            index += 1
    return moves


class Solution:
    def minimumMoves(self, s: str) -> int:
        return solve(s)
