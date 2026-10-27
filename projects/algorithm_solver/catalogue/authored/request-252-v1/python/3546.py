def solve(grid):
    total = sum(map(sum, grid))
    prefix = 0
    for row in grid[:-1]:
        prefix += sum(row)
        if prefix * 2 == total:
            return True
    prefix = 0
    for column in range(len(grid[0]) - 1):
        prefix += sum(row[column] for row in grid)
        if prefix * 2 == total:
            return True
    return False
