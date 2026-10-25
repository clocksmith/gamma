"""2132. Stamping the Grid."""

def solve(grid: list[list[int]], stampHeight: int, stampWidth: int) -> bool:
    """O(rows*cols) time and space; prefix sums locate stamps, differences cover cells."""
    rows, cols = len(grid), len(grid[0])
    stride = cols + 1
    size = (rows + 1) * stride
    occupied = [0] * size
    for row in range(rows):
        running = 0
        previous = row * stride
        current = (row + 1) * stride
        for col in range(cols):
            running += grid[row][col]
            occupied[current + col + 1] = occupied[previous + col + 1] + running
    coverage = [0] * size
    for row in range(rows - stampHeight + 1):
        top = row * stride
        bottom = (row + stampHeight) * stride
        for col in range(cols - stampWidth + 1):
            right = col + stampWidth
            count = (occupied[bottom + right] - occupied[top + right]
                     - occupied[bottom + col] + occupied[top + col])
            if count == 0:
                coverage[top + col] += 1
                coverage[top + right] -= 1
                coverage[bottom + col] -= 1
                coverage[bottom + right] += 1
    for row in range(rows):
        for col in range(cols):
            index = row * stride + col
            if row:
                coverage[index] += coverage[index - stride]
            if col:
                coverage[index] += coverage[index - 1]
            if row and col:
                coverage[index] -= coverage[index - stride - 1]
            if grid[row][col] == 0 and coverage[index] == 0:
                return False
    return True


class Solution:
    def possibleToStamp(self, grid: list[list[int]], stampHeight: int, stampWidth: int) -> bool:
        return solve(grid, stampHeight, stampWidth)
