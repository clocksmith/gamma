def solve(grid):
    width = len(grid[0])
    ways = [0] * width
    ways[0] = 1
    for row in grid:
        for column in range(width):
            if row[column]:
                ways[column] = 0
            elif column:
                ways[column] += ways[column - 1]
    return ways[-1]
