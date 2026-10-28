"""1222. Queens That Can Attack the King (Medium).

Specification: https://leetcode.com/problems/queens-that-can-attack-the-king/description/
"""


def solve(queens: list[list[int]], king: list[int]) -> list[list[int]]:
    queen_set = {(r, c) for r, c in queens}
    result = []
    directions = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]
    for dr, dc in directions:
        r, c = king[0] + dr, king[1] + dc
        while 0 <= r < 8 and 0 <= c < 8:
            if (r, c) in queen_set:
                result.append([r, c])
                break
            r += dr
            c += dc
    result.sort()
    return result


class Solution:
    def queensThatCanAttackTheKing(self, queens: list[list[int]], king: list[int]) -> list[list[int]]:
        return solve(queens, king)
