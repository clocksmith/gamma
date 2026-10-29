"""Hack2Hire 6907a349e1919109b6df1193 (Knight Paths on a Phone Keypad) over an INFERRED spec; qualification unknown."""

POSITION = {1: (0, 0), 2: (0, 1), 3: (0, 2), 4: (1, 0), 5: (1, 1), 6: (1, 2), 7: (2, 0), 8: (2, 1), 9: (2, 2), 0: (3, 1)}
MOVES = {a: [b for b in sorted(POSITION) if sorted((abs(POSITION[a][0] - POSITION[b][0]), abs(POSITION[a][1] - POSITION[b][1]))) == [1, 2]]
         for a in POSITION}


def solve(start, end):
    dist = {start: 0}
    frontier = [start]
    while frontier:
        nxt = []
        for a in frontier:
            for b in MOVES[a]:
                if b not in dist:
                    dist[b] = dist[a] + 1
                    nxt.append(b)
        frontier = nxt
    if end not in dist:
        return []
    paths, stack = [], [(start, str(start))]
    while stack:
        a, path = stack.pop()
        if a == end:
            paths.append(path)
            continue
        for b in MOVES[a]:
            if dist.get(b) == dist[a] + 1 and dist[b] <= dist[end]:
                stack.append((b, path + str(b)))
    return sorted(paths)


class Solution:
    def knightPaths(self, start, end):
        return solve(start, end)
