"""3257. Maximum Value Sum by Placing Three Rooks II.

Enumerate the middle rook and the three best distinct columns above and below it; O(rows*columns) time and O(rows+columns) space. Inputs are preserved.
"""

def solve(board: list[list[int]]) -> int:
    rows, columns = len(board), len(board[0])

    def top_three(values):
        best = []
        for column, value in enumerate(values):
            best.append((value, column))
            best.sort(reverse=True)
            if len(best) > 3:
                best.pop()
        return best

    below = [None] * rows
    values = [float('-inf')] * columns
    for row in range(rows - 1, -1, -1):
        below[row] = top_three(values)
        for column in range(columns):
            values[column] = max(values[column], board[row][column])
    values = board[0].copy()
    answer = float('-inf')
    for row in range(1, rows - 1):
        above = top_three(values)
        for column, middle in enumerate(board[row]):
            for first, first_column in above:
                if first_column == column:
                    continue
                for last, last_column in below[row]:
                    if last_column != column and last_column != first_column:
                        answer = max(answer, first + middle + last)
        for column in range(columns):
            values[column] = max(values[column], board[row][column])
    return answer


class Solution:
    def maximumValueSum(self, board: list[list[int]]) -> int:
        return solve(board)
