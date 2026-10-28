"""417. Pacific Atlantic Water Flow (Medium).

Specification: https://leetcode.com/problems/pacific-atlantic-water-flow/description/
"""


def solve(heights: list[list[int]]) -> list[list[int]]:
    rows, cols = len(heights), len(heights[0])

    def reachable_from(ocean):
        seen = set()
        stack = []
        for r in range(rows):
            for c in range(cols):
                if (ocean == 'pacific' and (r == 0 or c == 0)) or (ocean == 'atlantic' and (r == rows - 1 or c == cols - 1)):
                    seen.add((r, c))
                    stack.append((r, c))
        directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        while stack:
            r, c = stack.pop()
            for dr, dc in directions:
                nr, nc = r + dr, c + dc
                if nr < 0 or nr >= rows or nc < 0 or nc >= cols:
                    continue
                if (nr, nc) in seen:
                    continue
                if heights[nr][nc] < heights[r][c]:
                    continue
                seen.add((nr, nc))
                stack.append((nr, nc))
        return seen

    pacific = reachable_from('pacific')
    atlantic = reachable_from('atlantic')
    result = []
    for r in range(rows):
        for c in range(cols):
            if (r, c) in pacific and (r, c) in atlantic:
                result.append([r, c])
    return result


class Solution:
    def pacificAtlantic(self, heights: list[list[int]]) -> list[list[int]]:
        return solve(heights)
