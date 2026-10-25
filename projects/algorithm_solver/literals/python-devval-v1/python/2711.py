def solve(grid):
    height = len(grid)
    width = len(grid[0])
    result = [[0] * width for _ in range(height)]
    starts = [(0, column) for column in range(width)]
    starts.extend((row, 0) for row in range(1, height))
    for row, column in starts:
        diagonal = []
        seen = set()
        while row < height and column < width:
            result[row][column] = len(seen)
            seen.add(grid[row][column])
            diagonal.append((row, column))
            row += 1
            column += 1
        seen = set()
        for row, column in reversed(diagonal):
            result[row][column] = abs(result[row][column] - len(seen))
            seen.add(grid[row][column])
    return result
