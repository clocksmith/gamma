# 407 — Trapping Rain Water II. Original implementation; authored candidate, not independently qualified.
def solve(heightMap):
    import heapq
    if not heightMap or not heightMap[0]:
        return 0
    rows, cols = len(heightMap), len(heightMap[0])
    seen, heap = set(), []
    for r in range(rows):
        for c in range(cols):
            if r in (0, rows - 1) or c in (0, cols - 1):
                seen.add((r, c))
                heap.append((heightMap[r][c], r, c))
    heapq.heapify(heap)
    total = 0
    while heap:
        level, r, c = heapq.heappop(heap)
        for nr, nc in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
            if 0 <= nr < rows and 0 <= nc < cols and (nr, nc) not in seen:
                seen.add((nr, nc))
                total += max(0, level - heightMap[nr][nc])
                heapq.heappush(heap, (max(level, heightMap[nr][nc]), nr, nc))
    return total

trapRainWater = solve

class Solution:
    trapRainWater = staticmethod(solve)
