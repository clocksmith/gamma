def cardinal_neighbors(row: int, column: int, rows: int, columns: int):
    for row_step, column_step in ((-1, 0), (0, 1), (1, 0), (0, -1)):
        next_row = row + row_step
        next_column = column + column_step
        if 0 <= next_row < rows and 0 <= next_column < columns:
            yield next_row, next_column


class Solution:
    def maxDistance(self, grid: list[list[int]]) -> int:
        size = len(grid)
        queue = []
        for row in range(size):
            for column in range(size):
                if grid[row][column] == 1:
                    queue.append((row, column, 0))
        if not queue or len(queue) == size * size:
            return -1
        head = 0
        furthest = 0
        while head < len(queue):
            row, column, distance = queue[head]
            head += 1
            for next_row, next_column in cardinal_neighbors(row, column, size, size):
                if grid[next_row][next_column] == 0:
                    grid[next_row][next_column] = 1
                    next_distance = distance + 1
                    furthest = max(furthest, next_distance)
                    queue.append((next_row, next_column, next_distance))
        return furthest
