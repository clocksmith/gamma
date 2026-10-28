"""1079. Letter Tile Possibilities (Medium).

Specification: https://leetcode.com/problems/letter-tile-possibilities/description/
"""


def solve(tiles: str) -> int:
    counts = [0] * 26
    for ch in tiles:
        counts[ord(ch) - 65] += 1

    def dfs():
        total = 0
        for i in range(26):
            if counts[i] > 0:
                counts[i] -= 1
                total += 1 + dfs()
                counts[i] += 1
        return total

    return dfs()


class Solution:
    def numTilePossibilities(self, tiles: str) -> int:
        return solve(tiles)
