"""407. Trapping Rain Water II. Flood inward from the lowest boundary; preserves the height map."""

from heapq import heappush, heappop

def solve(heightMap: list[list[int]]) -> int:
    rows, cols = len(heightMap), len(heightMap[0])
    if rows < 3 or cols < 3:
        return 0
    seen = [[False] * cols for _ in range(rows)]
    heap = []
    for row in range(rows):
        for col in range(cols):
            if row in (0, rows - 1) or col in (0, cols - 1):
                seen[row][col] = True
                heappush(heap, (heightMap[row][col], row, col))
    answer = 0
    while heap:
        level, row, col = heappop(heap)
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = row + dr, col + dc
            if 0 <= nr < rows and 0 <= nc < cols and not seen[nr][nc]:
                seen[nr][nc] = True
                height = heightMap[nr][nc]
                answer += max(0, level - height)
                heappush(heap, (max(level, height), nr, nc))
    return answer


class Solution:
    def trapRainWater(self, heightMap: list[list[int]]) -> int:
        return solve(heightMap)
