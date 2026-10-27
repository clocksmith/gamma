"""531. Lonely Pixel I."""

def solve(picture: list[list[str]]) -> int:
    rows, cols = len(picture), len(picture[0])
    row_counts = [row.count('B') for row in picture]
    col_counts = [sum(picture[r][c] == 'B' for r in range(rows)) for c in range(cols)]
    return sum(picture[r][c] == 'B' and row_counts[r] == col_counts[c] == 1
               for r in range(rows) for c in range(cols))


class Solution:
    def findLonelyPixel(self, picture: list[list[str]]) -> int:
        return solve(picture)
