"""2075. Decode the Slanted Ciphertext: read the stored rectangle along diagonals and discard only trailing spaces."""


def solve(encodedText: str, rows: int) -> str:
    """O(L) time and O(L) auxiliary and result space for L encoded characters; inputs are read-only."""
    columns = len(encodedText) // rows
    decoded = []
    for start in range(columns):
        row, column = 0, start
        while row < rows and column < columns:
            decoded.append(encodedText[row * columns + column])
            row += 1
            column += 1
    return ''.join(decoded).rstrip(' ')


class Solution:
    def decodeCiphertext(self, encodedText: str, rows: int) -> str:
        return solve(encodedText, rows)
