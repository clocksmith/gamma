"""Hack2Hire 68f9a7290fa32e4d82f4fb89 (Find Nearest Exit in Maze, variant 2 of 2) over an INFERRED spec; qualification unknown."""


def solve(matrix, entrance):
    m, n = len(matrix), len(matrix[0])
    start = entrance[0] * n + entrance[1]
    seen = bytearray(m * n)
    seen[start] = 1
    level, distance = [start], 0
    while level:
        exits = [v for v in level if v != start and (v < n or v >= (m - 1) * n or v % n == 0 or v % n == n - 1)]
        if exits:
            best = min(exits)
            return [best // n, best % n]
        following = []
        for v in level:
            r, c = divmod(v, n)
            for rr, cc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if 0 <= rr < m and 0 <= cc < n and matrix[rr][cc] == 1:
                    w = rr * n + cc
                    if not seen[w]:
                        seen[w] = 1
                        following.append(w)
        level = following
        distance += 1
    return [-1, -1]


class Solution:
    def nearestExitCell(self, matrix, entrance):
        return solve(matrix, entrance)
