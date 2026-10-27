# Original candidate; contract and evidence: ../batch1/manifest.json
from collections import Counter


def solve(grid):
    def sweep(transposed):
        rows = len(grid[0]) if transposed else len(grid)
        columns = len(grid) if transposed else len(grid[0])
        def at(r, c):
            return grid[c][r] if transposed else grid[r][c]
        right = Counter(value for row in grid for value in row)
        left = Counter()
        total = sum(value * count for value, count in right.items())
        prefix = 0
        for cut in range(1, rows):
            for column in range(columns):
                value = at(cut - 1, column)
                left[value] += 1
                right[value] -= 1
                prefix += value
            difference = 2 * prefix - total
            if difference == 0:
                return True
            start, end, counts = (0, cut, left) if difference > 0 else (cut, rows, right)
            target = abs(difference)
            if (end - start) * columns <= 1:
                continue
            if end - start == 1:
                possible = at(start, 0) == target or at(start, columns - 1) == target
            elif columns == 1:
                possible = at(start, 0) == target or at(end - 1, 0) == target
            else:
                possible = counts[target] > 0
            if possible:
                return True
        return False
    return sweep(False) or sweep(True)
