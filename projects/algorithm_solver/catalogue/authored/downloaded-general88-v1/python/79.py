"""79. Word Search (Medium).

Specification: https://leetcode.com/problems/word-search/description/
"""


def solve(board: list[list[str]], word: str) -> bool:
    rows, cols = len(board), len(board[0])

    def dfs(r, c, index):
        if index == len(word):
            return True
        if r < 0 or r >= rows or c < 0 or c >= cols or board[r][c] != word[index]:
            return False
        saved = board[r][c]
        board[r][c] = '#'
        found = dfs(r + 1, c, index + 1) or dfs(r - 1, c, index + 1) or dfs(r, c + 1, index + 1) or dfs(r, c - 1, index + 1)
        board[r][c] = saved
        return found

    for r in range(rows):
        for c in range(cols):
            if dfs(r, c, 0):
                return True
    return False


class Solution:
    def exist(self, board: list[list[str]], word: str) -> bool:
        return solve(board, word)
