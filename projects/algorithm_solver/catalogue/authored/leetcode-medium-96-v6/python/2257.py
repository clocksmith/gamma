"""2257. Count Unguarded Cells in the Grid: sweep visibility in four directions while walls interrupt and guards restart each ray."""


def solve(m: int, n: int, guards: list[list[int]], walls: list[list[int]]) -> int:
    """O(m * n + g + w) time and O(m * n) auxiliary space; inputs are read-only."""
    cells = bytearray(m * n)
    visible = bytearray(m * n)
    for row, column in walls:
        cells[row * n + column] = 1
    for row, column in guards:
        cells[row * n + column] = 2
    for row in range(m):
        for columns in (range(n), range(n - 1, -1, -1)):
            active = False
            for column in columns:
                index = row * n + column
                if cells[index]:
                    active = cells[index] == 2
                elif active:
                    visible[index] = 1
    for column in range(n):
        for rows in (range(m), range(m - 1, -1, -1)):
            active = False
            for row in rows:
                index = row * n + column
                if cells[index]:
                    active = cells[index] == 2
                elif active:
                    visible[index] = 1
    return sum(cells[index] == 0 and visible[index] == 0 for index in range(m * n))


class Solution:
    def countUnguarded(self, m: int, n: int, guards: list[list[int]], walls: list[list[int]]) -> int:
        return solve(m, n, guards, walls)
