# 329 — Longest Increasing Path in a Matrix. Original implementation; authored candidate, not independently qualified.
def solve(matrix):
    from collections import deque
    if not matrix or not matrix[0]:
        return 0
    rows, cols = len(matrix), len(matrix[0])
    degree = [[0] * cols for _ in range(rows)]
    directions = ((1, 0), (-1, 0), (0, 1), (0, -1))
    queue = deque()
    for r in range(rows):
        for c in range(cols):
            degree[r][c] = sum(0 <= r + dr < rows and 0 <= c + dc < cols and
                               matrix[r + dr][c + dc] > matrix[r][c] for dr, dc in directions)
            if degree[r][c] == 0:
                queue.append((r, c))
    layers = 0
    while queue:
        layers += 1
        for _ in range(len(queue)):
            r, c = queue.popleft()
            for dr, dc in directions:
                nr, nc = r + dr, c + dc
                if 0 <= nr < rows and 0 <= nc < cols and matrix[nr][nc] < matrix[r][c]:
                    degree[nr][nc] -= 1
                    if degree[nr][nc] == 0:
                        queue.append((nr, nc))
    return layers

longestIncreasingPath = solve

class Solution:
    longestIncreasingPath = staticmethod(solve)
