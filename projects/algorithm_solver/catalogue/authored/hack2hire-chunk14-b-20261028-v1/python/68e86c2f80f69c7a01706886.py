"""Hack2Hire 68e86c2f80f69c7a01706886 (Word Search in a Straight Line) over an INFERRED spec; qualification unknown."""


def solve(board, word):
    m, n, length = len(board), len(board[0]), len(word)
    directions = [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]
    for r in range(m):
        for c in range(n):
            if board[r][c] != word[0]:
                continue
            for dr, dc in directions:
                er, ec = r + dr * (length - 1), c + dc * (length - 1)
                if not (0 <= er < m and 0 <= ec < n):
                    continue
                k = 1
                while k < length and board[r + dr * k][c + dc * k] == word[k]:
                    k += 1
                if k == length:
                    return True
    return False


class Solution:
    def existsInStraightLine(self, board, word):
        return solve(board, word)
