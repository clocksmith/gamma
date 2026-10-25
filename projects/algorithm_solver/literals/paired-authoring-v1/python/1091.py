class Solution:
    def shortestPathBinaryMatrix(self, grid: list[list[int]]) -> int:
        size = len(grid)
        if grid[0][0] != 0:
            return -1
        grid[0][0] = 1
        queue = [(0, 0, 1)]
        head = 0
        while head < len(queue):
            row, column, distance = queue[head]
            head += 1
            if row == size - 1 and column == size - 1:
                return distance
            for row_step in (-1, 0, 1):
                for column_step in (-1, 0, 1):
                    if row_step == 0 and column_step == 0:
                        continue
                    next_row = row + row_step
                    next_column = column + column_step
                    if 0 <= next_row < size and 0 <= next_column < size:
                        if grid[next_row][next_column] == 0:
                            grid[next_row][next_column] = 1
                            queue.append((next_row, next_column, distance + 1))
        return -1
