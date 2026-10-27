"""427. Construct Quad Tree. Prefix sums identify uniform quadrants; input grid is preserved."""

class Node:
    def __init__(self, val=False, isLeaf=False, topLeft=None, topRight=None,
                 bottomLeft=None, bottomRight=None):
        self.val = val
        self.isLeaf = isLeaf
        self.topLeft = topLeft
        self.topRight = topRight
        self.bottomLeft = bottomLeft
        self.bottomRight = bottomRight

def solve(grid: list[list[int]]):
    n = len(grid)
    prefix = [[0] * (n + 1) for _ in range(n + 1)]
    for r in range(n):
        for c in range(n):
            prefix[r + 1][c + 1] = grid[r][c] + prefix[r][c + 1] + prefix[r + 1][c] - prefix[r][c]
    def build(r, c, size):
        total = prefix[r + size][c + size] - prefix[r][c + size] - prefix[r + size][c] + prefix[r][c]
        if total == 0 or total == size * size:
            return Node(bool(total), True)
        half = size // 2
        return Node(False, False, build(r, c, half), build(r, c + half, half),
                    build(r + half, c, half), build(r + half, c + half, half))
    return build(0, 0, n)


class Solution:
    def construct(self, grid: list[list[int]]):
        return solve(grid)
