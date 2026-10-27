"""499. The Maze III. Dijkstra orders by traveled distance and then direction string; stop rolling at the hole."""

from heapq import heappush, heappop

def solve(maze: list[list[int]], ball: list[int], hole: list[int]) -> str:
    rows, cols = len(maze), len(maze[0])
    target = tuple(hole)
    heap = [(0, '', ball[0], ball[1])]
    best = {(ball[0], ball[1]): (0, '')}
    while heap:
        distance, path, row, col = heappop(heap)
        if best[(row, col)] != (distance, path):
            continue
        if (row, col) == target:
            return path
        for dr, dc, letter in ((1, 0, 'd'), (0, -1, 'l'), (0, 1, 'r'), (-1, 0, 'u')):
            nr, nc, steps = row, col, 0
            while 0 <= nr + dr < rows and 0 <= nc + dc < cols and maze[nr + dr][nc + dc] == 0:
                nr += dr
                nc += dc
                steps += 1
                if (nr, nc) == target:
                    break
            candidate = (distance + steps, path + letter)
            if steps and candidate < best.get((nr, nc), (float('inf'), '')):
                best[(nr, nc)] = candidate
                heappush(heap, (candidate[0], candidate[1], nr, nc))
    return 'impossible'


class Solution:
    def findShortestWay(self, maze: list[list[int]], ball: list[int], hole: list[int]) -> str:
        return solve(maze, ball, hole)
