"""711. Number of Distinct Islands II. Normalize all eight rotations/reflections after translation; preserve the grid."""

def solve(grid: list[list[int]]) -> int:
    rows, cols = len(grid), len(grid[0])
    seen, shapes = set(), set()
    def canonical(cells):
        variants = [[] for _ in range(8)]
        for x, y in cells:
            for index, point in enumerate(((x, y), (x, -y), (-x, y), (-x, -y),
                                           (y, x), (y, -x), (-y, x), (-y, -x))):
                variants[index].append(point)
        normalized = []
        for points in variants:
            points.sort()
            ox, oy = points[0]
            normalized.append(tuple((x - ox, y - oy) for x, y in points))
        return min(normalized)
    for row in range(rows):
        for col in range(cols):
            if not grid[row][col] or (row, col) in seen:
                continue
            seen.add((row, col))
            stack, cells = [(row, col)], []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] and (nr, nc) not in seen:
                        seen.add((nr, nc)); stack.append((nr, nc))
            shapes.add(canonical(cells))
    return len(shapes)


class Solution:
    def numDistinctIslands2(self, grid: list[list[int]]) -> int:
        return solve(grid)
