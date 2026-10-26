"""3283. Maximum Number of Moves to Kill All Pawns: knight-distance searches followed by subset minimax."""

from array import array
from collections import deque


def solve(kx: int, ky: int, positions: list[list[int]]) -> int:
    """O(n*2500 + n^2*2^n) time and O(2500 + n*2^n) auxiliary space. Inputs are preserved."""
    n = len(positions)
    locations = [*positions, [kx, ky]]
    directions = ((1, 2), (2, 1), (-1, 2), (-2, 1), (1, -2), (2, -1), (-1, -2), (-2, -1))
    distance = []
    for start_x, start_y in locations:
        seen = [-1] * 2500
        start = start_x * 50 + start_y
        seen[start] = 0
        queue = deque([start])
        while queue:
            cell = queue.popleft()
            x, y = divmod(cell, 50)
            for dx, dy in directions:
                nx, ny = x + dx, y + dy
                if 0 <= nx < 50 and 0 <= ny < 50:
                    following = nx * 50 + ny
                    if seen[following] == -1:
                        seen[following] = seen[cell] + 1
                        queue.append(following)
        distance.append([seen[x * 50 + y] for x, y in positions])
    size = 1 << n
    memo = array('i', [-1]) * (size * (n + 1))

    def visit(mask, last):
        if mask == 0:
            return 0
        key = mask * (n + 1) + last
        if memo[key] >= 0:
            return memo[key]
        maximizing = (n - mask.bit_count()) % 2 == 0
        value = -1 if maximizing else 1_000_000
        remaining = mask
        while remaining:
            bit = remaining & -remaining
            remaining -= bit
            following = bit.bit_length() - 1
            candidate = distance[last][following] + visit(mask ^ bit, following)
            value = max(value, candidate) if maximizing else min(value, candidate)
        memo[key] = value
        return value

    return visit(size - 1, n)


class Solution:
    def maxMoves(self, kx: int, ky: int, positions: list[list[int]]) -> int:
        return solve(kx, ky, positions)
