"""174. Dungeon Game (Hard).

Specification: https://leetcode.com/problems/dungeon-game/description/
"""


def solve(dungeon: list[list[int]]) -> int:
    rows, cols = len(dungeon), len(dungeon[0])
    dp = [[0] * cols for _ in range(rows)]
    for r in range(rows - 1, -1, -1):
        for c in range(cols - 1, -1, -1):
            if r == rows - 1 and c == cols - 1:
                dp[r][c] = max(1, 1 - dungeon[r][c])
            elif r == rows - 1:
                dp[r][c] = max(1, dp[r][c + 1] - dungeon[r][c])
            elif c == cols - 1:
                dp[r][c] = max(1, dp[r + 1][c] - dungeon[r][c])
            else:
                dp[r][c] = max(1, min(dp[r + 1][c], dp[r][c + 1]) - dungeon[r][c])
    return dp[0][0]


class Solution:
    def calculateMinimumHP(self, dungeon: list[list[int]]) -> int:
        return solve(dungeon)
