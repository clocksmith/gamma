"""505. The Maze II."""

from heapq import heappush, heappop

def solve(maze: list[list[int]], start: list[int], destination: list[int]) -> int:
    rows, cols = len(maze), len(maze[0])
    distance = [[float('inf')] * cols for _ in range(rows)]
    distance[start[0]][start[1]] = 0
    heap = [(0, start[0], start[1])]
    while heap:
        cost, row, col = heappop(heap)
        if cost != distance[row][col]:
            continue
        if [row, col] == destination:
            return cost
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc, steps = row, col, 0
            while 0 <= nr + dr < rows and 0 <= nc + dc < cols and maze[nr + dr][nc + dc] == 0:
                nr += dr
                nc += dc
                steps += 1
            if cost + steps < distance[nr][nc]:
                distance[nr][nc] = cost + steps
                heappush(heap, (cost + steps, nr, nc))
    return -1


class Solution:
    def shortestDistance(self, maze: list[list[int]], start: list[int], destination: list[int]) -> int:
        return solve(maze, start, destination)
