"""Separate iterative flood variant; caller grid is read-only."""
def solve(grid: list[list[int]]) -> int:
    rows, cols = len(grid), len(grid[0])
    seen = set()
    answer = 0
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] or (r,c) in seen:
                continue
            seen.add((r,c))
            stack = [(r,c)]
            closed = True
            while stack:
                i,j = stack.pop()
                if i in (0,rows-1) or j in (0,cols-1):
                    closed = False
                for u,v in ((i-1,j),(i+1,j),(i,j-1),(i,j+1)):
                    if 0 <= u < rows and 0 <= v < cols and not grid[u][v] and (u,v) not in seen:
                        seen.add((u,v))
                        stack.append((u,v))
            answer += int(closed)
    return answer
class Solution:
    def closedIsland(self, grid: list[list[int]]) -> int:
        return solve(grid)
