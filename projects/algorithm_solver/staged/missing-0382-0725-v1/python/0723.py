"""723. Candy Crush. Mark simultaneous matches, apply gravity, and repeat; intentionally mutate and return the supplied board."""

def solve(board: list[list[int]]) -> list[list[int]]:
    rows, cols = len(board), len(board[0])
    while True:
        remove = set()
        for r in range(rows):
            for c in range(cols - 2):
                if board[r][c] and board[r][c] == board[r][c + 1] == board[r][c + 2]:
                    remove.update(((r, c), (r, c + 1), (r, c + 2)))
        for r in range(rows - 2):
            for c in range(cols):
                if board[r][c] and board[r][c] == board[r + 1][c] == board[r + 2][c]:
                    remove.update(((r, c), (r + 1, c), (r + 2, c)))
        if not remove:
            return board
        for r, c in remove:
            board[r][c] = 0
        for c in range(cols):
            write = rows - 1
            for r in range(rows - 1, -1, -1):
                if board[r][c]:
                    board[write][c] = board[r][c]
                    write -= 1
            for r in range(write, -1, -1):
                board[r][c] = 0


class Solution:
    def candyCrush(self, board: list[list[int]]) -> list[list[int]]:
        return solve(board)
