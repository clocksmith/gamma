"""Hack2Hire 6a02333a2608e589a944a29d (Calculate Board Score) over an INFERRED spec; qualification unknown."""


def solve(board):
    rows, cols = len(board), len(board[0])
    seen = bytearray(rows * cols)
    total = 0
    for start in range(rows * cols):
        if seen[start]:
            continue
        terrain = board[start // cols][start % cols][0]
        seen[start] = 1
        queue = [start]
        crowns = 0
        head = 0
        while head < len(queue):
            cell = queue[head]
            head += 1
            r, c = divmod(cell, cols)
            crowns += ord(board[r][c][1]) - 48
            for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if 0 <= nr < rows and 0 <= nc < cols:
                    nxt = nr * cols + nc
                    if not seen[nxt] and board[nr][nc][0] == terrain:
                        seen[nxt] = 1
                        queue.append(nxt)
        total += len(queue) * crowns
    return total


class Solution:
    def calculateScore(self, board):
        return solve(board)
