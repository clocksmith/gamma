"""302. Smallest Rectangle Enclosing Black Pixels."""
def solve(image: list[list[str]], x: int, y: int) -> int:
    rows, columns = len(image), len(image[0])
    top, bottom, left, right = rows, -1, columns, -1
    for row in range(rows):
        for column in range(columns):
            if image[row][column] == '1':
                top = min(top, row)
                bottom = max(bottom, row)
                left = min(left, column)
                right = max(right, column)
    return (bottom - top + 1) * (right - left + 1)

class Solution:
    def minArea(self, image, x, y):
        return solve(image, x, y)
