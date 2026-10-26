"""2018. Check if Word Can Be Placed In Crossword: match complete horizontal or vertical slots in either reading direction."""


def solve(board: list[list[str]], word: str) -> bool:
    """O(rows * columns) time and O(1) auxiliary space; inputs are read-only."""
    rows, columns = len(board), len(board[0])
    length = len(word)

    def matches(row: int, column: int, dr: int, dc: int) -> bool:
        forward = backward = True
        for index in range(length):
            letter = board[row + index * dr][column + index * dc]
            if letter != ' ' and letter != word[index]:
                forward = False
            if letter != ' ' and letter != word[length - 1 - index]:
                backward = False
            if not forward and not backward:
                return False
        return forward or backward

    for row in range(rows):
        start = 0
        for column in range(columns + 1):
            if column == columns or board[row][column] == '#':
                if column - start == length and matches(row, start, 0, 1):
                    return True
                start = column + 1
    for column in range(columns):
        start = 0
        for row in range(rows + 1):
            if row == rows or board[row][column] == '#':
                if row - start == length and matches(start, column, 1, 0):
                    return True
                start = row + 1
    return False


class Solution:
    def placeWordInCrossword(self, board: list[list[str]], word: str) -> bool:
        return solve(board, word)
