"""212. Word Search II."""
def solve(board: list[list[str]], words: list[str]) -> list[str]:
    root = {}
    for word in words:
        node = root
        for char in word:
            node = node.setdefault(char, {})
        node['$'] = word
    rows, columns = len(board), len(board[0])
    result = []
    def visit(row: int, column: int, node: dict) -> None:
        char = board[row][column]
        if char not in node:
            return
        following = node[char]
        word = following.pop('$', None)
        if word is not None:
            result.append(word)
        board[row][column] = '#'
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = row + dr, column + dc
            if 0 <= nr < rows and 0 <= nc < columns and board[nr][nc] != '#':
                visit(nr, nc, following)
        board[row][column] = char
        if not following:
            node.pop(char)
    for row in range(rows):
        for column in range(columns):
            visit(row, column, root)
    return result

class Solution:
    def findWords(self, board: list[list[str]], words: list[str]) -> list[str]:
        return solve(board, words)
