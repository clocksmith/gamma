def solve(grid, k):
    rows, columns = len(grid), len(grid[0])
    answer = []
    for top in range(rows - k + 1):
        row = []
        for left in range(columns - k + 1):
            values = sorted({grid[r][c] for r in range(top, top + k)
                             for c in range(left, left + k)})
            row.append(min((b - a for a, b in zip(values, values[1:])), default=0))
        answer.append(row)
    return answer
