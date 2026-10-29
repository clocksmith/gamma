"""Original development candidate; independent qualification pending."""
def solve(grid):
    n = len(grid)
    labels = [[-1] * n for _ in range(n)]
    sizes = []
    for r in range(n):
        for c in range(n):
            if not grid[r][c] or labels[r][c] >= 0:
                continue
            label = len(sizes)
            labels[r][c] = label
            stack = [(r, c)]
            area = 0
            while stack:
                x, y = stack.pop()
                area += 1
                for a, b in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
                    if 0 <= a < n and 0 <= b < n and grid[a][b] and labels[a][b] < 0:
                        labels[a][b] = label
                        stack.append((a,b))
            sizes.append(area)
    best = max(sizes, default=0)
    for r in range(n):
        for c in range(n):
            if grid[r][c] == 0:
                neighbors = {labels[a][b] for a,b in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)) if 0 <= a < n and 0 <= b < n and labels[a][b] >= 0}
                best = max(best, 1 + sum(sizes[x] for x in neighbors))
    return best


class Solution:
    def largestIsland(self, grid):
        return solve(grid)
