"""Hack2Hire 67ff11d2a19f45c95d40567f (Three-Color Map Coloring) over an INFERRED spec; qualification unknown."""

def solve(locations, adjacencies):
    n = len(locations)
    index = {name: i for i, name in enumerate(locations)}
    neighbours = [set() for _ in range(n)]
    for a, b in adjacencies:
        neighbours[index[a]].add(index[b])
        neighbours[index[b]].add(index[a])
    neighbours = [sorted(s) for s in neighbours]
    colour = [-1] * n
    seen = [[0, 0, 0] for _ in range(n)]   # seen[v][c]: coloured neighbours of v with colour c

    def pick():
        best, key = -1, None
        for v in range(n):
            if colour[v] < 0:
                k = ((seen[v][0] > 0) + (seen[v][1] > 0) + (seen[v][2] > 0), len(neighbours[v]))
                if key is None or k > key:
                    best, key = v, k
        return best, key

    def search(left):
        if left == 0:
            return True
        v, key = pick()
        options = (0,) if key[0] == 0 else (0, 1, 2)   # saturation 0: v's component is uncoloured, colours are symmetric
        for c in options:
            if seen[v][c]:
                continue
            colour[v] = c
            for u in neighbours[v]:
                seen[u][c] += 1
            if search(left - 1):
                return True
            for u in neighbours[v]:
                seen[u][c] -= 1
            colour[v] = -1
        return False

    return search(n)


class Solution:
    def canThreeColor(self, locations, adjacencies):
        return solve(locations, adjacencies)
