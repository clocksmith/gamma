"""Original hack2hire:67eaec184c9bb801bfd0ef4d; inferred public-preview contract; qualification unknown."""
from collections import deque

def dualCarDestinations(grid):
    rows, cols = len(grid), len(grid[0])
    positions = {}
    neighbors = {}
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value == '#':
                continue
            cell = r * cols + c
            if value in 'abAB':
                positions[value] = cell
            neighbors[cell] = []
            for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
                a, b = r + dx, c + dy
                if 0 <= a < rows and 0 <= b < cols and grid[a][b] != '#':
                    neighbors[cell].append(a * cols + b)
    start = (positions['a'], positions['b'])
    target = (positions['A'], positions['B'])
    seen = {start}
    queue = deque([(start[0], start[1], 0)])
    while queue:
        a, b, distance = queue.popleft()
        if (a, b) == target:
            return distance
        for x in neighbors[a]:
            for y in neighbors[b]:
                if x == y or x == b and y == a or (x, y) in seen:
                    continue
                seen.add((x, y))
                queue.append((x, y, distance + 1))
    return -1

solve = dualCarDestinations

class Solution:
    dualCarDestinations = staticmethod(dualCarDestinations)
