def solve(grid):
    size = len(grid)
    area = 0
    for row in grid:
        area += sum(value > 0 for value in row)
        area += max(row, default=0)
    for column in range(size):
        area += max((row[column] for row in grid), default=0)
    return area
