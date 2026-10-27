"""695. Max Area of Island. Iterative flood fill with separate visitation state; input preserved."""

def solve(grid: list[list[int]]) -> int:
    rows, cols = len(grid), len(grid[0])
    seen = set()
    answer = 0
    for row in range(rows):
        for col in range(cols):
            if not grid[row][col] or (row, col) in seen:
                continue
            stack, area = [(row, col)], 0
            seen.add((row, col))
            while stack:
                r, c = stack.pop()
                area += 1
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] and (nr, nc) not in seen:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            answer = max(answer, area)
    return answer


class Solution:
    def maxAreaOfIsland(self, grid: list[list[int]]) -> int:
        return solve(grid)
