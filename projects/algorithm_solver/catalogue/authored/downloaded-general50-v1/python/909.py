"""909. Snakes and Ladders (Medium).

Specification: https://leetcode.com/problems/snakes-and-ladders/description/
"""


def solve(board: list[list[int]]) -> int:
    n = len(board)
    cells = [0]
    for r in range(n - 1, -1, -1):
        row = board[r] if (n - 1 - r) % 2 == 0 else board[r][::-1]
        for v in row:
            cells.append(v)
    target = n * n
    dist = [-1] * (target + 1)
    dist[1] = 0
    queue = [1]
    while queue:
        current = queue.pop(0)
        if current == target:
            return dist[current]
        for step in range(1, 7):
            nxt = current + step
            if nxt > target:
                break
            if cells[nxt] != -1:
                nxt = cells[nxt]
            if dist[nxt] == -1:
                dist[nxt] = dist[current] + 1
                queue.append(nxt)
    return -1


class Solution:
    def snakesAndLadders(self, board: list[list[int]]) -> int:
        return solve(board)
