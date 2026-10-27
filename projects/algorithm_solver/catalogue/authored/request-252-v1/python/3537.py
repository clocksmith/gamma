# Original candidate; contract and evidence: ../batch1/manifest.json
def solve(n):
    side = 1 << n
    grid = [[0] * side for _ in range(side)]

    def fill(row, column, size, start):
        if size == 1:
            grid[row][column] = start
            return
        half = size // 2
        count = half * half
        fill(row, column + half, half, start)
        fill(row + half, column + half, half, start + count)
        fill(row + half, column, half, start + 2 * count)
        fill(row, column, half, start + 3 * count)

    fill(0, 0, side, 0)
    return grid
