def new_grid(rows: int, columns: int) -> list[list[int]]:
    return [[0] * columns for _ in range(rows)]


class Solution:
    def findPaths(self, m: int, n: int, maxMove: int, startRow: int, startColumn: int) -> int:
        modulus = 1000000007
        ways = new_grid(m, n)
        ways[startRow][startColumn] = 1
        escaped = 0
        directions = ((-1, 0), (1, 0), (0, -1), (0, 1))
        for _ in range(maxMove):
            next_ways = new_grid(m, n)
            for row in range(m):
                for column in range(n):
                    count = ways[row][column]
                    if count == 0:
                        continue
                    for row_step, column_step in directions:
                        next_row = row + row_step
                        next_column = column + column_step
                        outside = (
                            next_row < 0 or next_row >= m
                            or next_column < 0 or next_column >= n
                        )
                        if outside:
                            escaped = (escaped + count) % modulus
                        else:
                            previous = next_ways[next_row][next_column]
                            next_ways[next_row][next_column] = (previous + count) % modulus
            ways = next_ways
        return escaped
