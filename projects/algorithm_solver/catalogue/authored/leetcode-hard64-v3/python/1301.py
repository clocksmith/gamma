"""1301. Number of Paths with Max Score: reverse grid dynamic programming; O(rows*columns) time and space. Board contents are preserved."""


def solve(board: list[str]) -> list[int]:
    modulus = 1_000_000_007
    rows, columns = len(board), len(board[0])
    score = [[-1] * columns for _ in range(rows)]
    ways = [[0] * columns for _ in range(rows)]
    score[-1][-1] = 0
    ways[-1][-1] = 1
    for row in range(rows - 1, -1, -1):
        for column in range(columns - 1, -1, -1):
            if board[row][column] == 'X' or (row == rows - 1 and column == columns - 1):
                continue
            best, count = -1, 0
            for nr, nc in ((row + 1, column), (row, column + 1), (row + 1, column + 1)):
                if nr >= rows or nc >= columns or score[nr][nc] < 0:
                    continue
                if score[nr][nc] > best:
                    best, count = score[nr][nc], ways[nr][nc]
                elif score[nr][nc] == best:
                    count = (count + ways[nr][nc]) % modulus
            if best >= 0:
                value = int(board[row][column]) if board[row][column].isdigit() else 0
                score[row][column] = best + value
                ways[row][column] = count
    return [score[0][0], ways[0][0]] if score[0][0] >= 0 else [0, 0]


class Solution:
    def pathsWithMaxScore(self, board: list[str]) -> list[int]:
        return solve(board)
