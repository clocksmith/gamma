"""Original frontend 749 variant; qualification unknown."""

def solve(isInfected):
    grid = [row[:] for row in isInfected]
    rows, cols = len(grid), len(grid[0])
    total = 0
    while True:
        seen = [[False] * cols for _ in range(rows)]
        regions = []
        for r in range(rows):
            for c in range(cols):
                if grid[r][c] != 1 or seen[r][c]:
                    continue
                seen[r][c] = True
                cells, threatened, walls, stack = [], set(), 0, [(r, c)]
                while stack:
                    x, y = stack.pop()
                    cells.append((x, y))
                    for u, v in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                        if 0 <= u < rows and 0 <= v < cols:
                            if grid[u][v] == 0:
                                threatened.add((u, v))
                                walls += 1
                            elif grid[u][v] == 1 and not seen[u][v]:
                                seen[u][v] = True
                                stack.append((u, v))
                regions.append((cells, threatened, walls))
        if not regions:
            return total
        best = max(range(len(regions)), key=lambda i: len(regions[i][1]))
        if not regions[best][1]:
            return total
        total += regions[best][2]
        for x, y in regions[best][0]:
            grid[x][y] = 2
        for i, (_, threatened, _) in enumerate(regions):
            if i != best:
                for x, y in threatened:
                    grid[x][y] = 1


class Solution:
    def containVirus(self, isInfected):
        return solve(isInfected)
