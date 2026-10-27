def solve(grid, k):
    rows, cols = len(grid), len(grid[0])
    seen = bytearray(rows * cols)
    answer = 0
    for r in range(rows):
        for c in range(cols):
            start = r * cols + c
            if seen[start] or grid[r][c] == 0:
                continue
            seen[start] = 1
            stack = [start]
            total = 0
            while stack:
                cell = stack.pop()
                x, y = divmod(cell, cols)
                total += grid[x][y]
                for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                    if 0 <= nx < rows and 0 <= ny < cols:
                        other = nx * cols + ny
                        if not seen[other] and grid[nx][ny] > 0:
                            seen[other] = 1
                            stack.append(other)
            answer += total % k == 0
    return answer
