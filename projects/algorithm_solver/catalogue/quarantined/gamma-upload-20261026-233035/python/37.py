"""37. Sudoku Solver."""
def solve(board: list[list[str]]) -> None:
    rows = [set() for _ in range(9)]
    columns = [set() for _ in range(9)]
    boxes = [set() for _ in range(9)]
    empty = []
    for row in range(9):
        for column in range(9):
            value = board[row][column]
            if value == '.':
                empty.append((row, column))
            else:
                rows[row].add(value)
                columns[column].add(value)
                boxes[(row // 3) * 3 + column // 3].add(value)

    def visit(index: int) -> bool:
        if index == len(empty):
            return True
        best = index
        best_options = None
        for candidate in range(index, len(empty)):
            row, column = empty[candidate]
            options = set('123456789') - rows[row] - columns[column] - boxes[(row // 3) * 3 + column // 3]
            if best_options is None or len(options) < len(best_options):
                best, best_options = candidate, options
                if len(options) <= 1:
                    break
        empty[index], empty[best] = empty[best], empty[index]
        row, column = empty[index]
        box = (row // 3) * 3 + column // 3
        for value in best_options:
            board[row][column] = value
            rows[row].add(value); columns[column].add(value); boxes[box].add(value)
            if visit(index + 1):
                return True
            rows[row].remove(value); columns[column].remove(value); boxes[box].remove(value)
        board[row][column] = '.'
        empty[index], empty[best] = empty[best], empty[index]
        return False

    visit(0)

class Solution:
    def solveSudoku(self, board: list[list[str]]) -> None:
        solve(board)
