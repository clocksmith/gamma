"""1284. Minimum Number of Flips to Convert Binary Matrix to Zero Matrix: bitmask BFS for at most nine cells; O(cells*2^cells) time and O(2^cells) space."""

from collections import deque


def solve(mat: list[list[int]]) -> int:
    rows, columns = len(mat), len(mat[0])
    start = 0
    flips = []
    for row in range(rows):
        for column in range(columns):
            start |= mat[row][column] << (row * columns + column)
            mask = 0
            for dr, dc in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
                nr, nc = row + dr, column + dc
                if 0 <= nr < rows and 0 <= nc < columns:
                    mask |= 1 << (nr * columns + nc)
            flips.append(mask)
    queue = deque([(start, 0)])
    seen = {start}
    while queue:
        state, distance = queue.popleft()
        if state == 0:
            return distance
        for mask in flips:
            following = state ^ mask
            if following not in seen:
                seen.add(following)
                queue.append((following, distance + 1))
    return -1


class Solution:
    def minFlips(self, mat: list[list[int]]) -> int:
        return solve(mat)
