"""417. Pacific Atlantic Water Flow. Reverse uphill reachability from both ocean borders."""

def solve(heights: list[list[int]]) -> list[list[int]]:
    rows, cols = len(heights), len(heights[0])
    def reach(starts):
        seen = set(starts)
        stack = list(seen)
        while stack:
            row, col = stack.pop()
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nr, nc = row + dr, col + dc
                if (0 <= nr < rows and 0 <= nc < cols and (nr, nc) not in seen
                        and heights[nr][nc] >= heights[row][col]):
                    seen.add((nr, nc))
                    stack.append((nr, nc))
        return seen
    pacific = reach([(0, c) for c in range(cols)] + [(r, 0) for r in range(rows)])
    atlantic = reach([(rows - 1, c) for c in range(cols)] + [(r, cols - 1) for r in range(rows)])
    return [[r, c] for r in range(rows) for c in range(cols) if (r, c) in pacific and (r, c) in atlantic]


class Solution:
    def pacificAtlantic(self, heights: list[list[int]]) -> list[list[int]]:
        return solve(heights)
