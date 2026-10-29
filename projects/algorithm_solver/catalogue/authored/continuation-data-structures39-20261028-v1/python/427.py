"""Original frontend 427 variant; qualification unknown."""
from collections import deque


class Node:
    def __init__(self, val, isLeaf, topLeft=None, topRight=None, bottomLeft=None, bottomRight=None):
        self.val = bool(val)
        self.isLeaf = bool(isLeaf)
        self.topLeft = topLeft
        self.topRight = topRight
        self.bottomLeft = bottomLeft
        self.bottomRight = bottomRight


def _serialize_quad(root):
    out = []
    q = deque([root])
    while q:
        node = q.popleft()
        if node is None:
            out.append(None)
        else:
            out.append([1 if node.isLeaf else 0, 1 if node.val else 0])
            q.append(node.topLeft)
            q.append(node.topRight)
            q.append(node.bottomLeft)
            q.append(node.bottomRight)
    while out and out[-1] is None:
        out.pop()
    return out


def _build_quad(pref, r0, c0, size):
    r1 = r0 + size
    c1 = c0 + size
    total = pref[r1][c1] - pref[r0][c1] - pref[r1][c0] + pref[r0][c0]
    if total == 0:
        return Node(False, True)
    if total == size * size:
        return Node(True, True)
    half = size // 2
    return Node(
        True,
        False,
        _build_quad(pref, r0, c0, half),
        _build_quad(pref, r0, c0 + half, half),
        _build_quad(pref, r0 + half, c0, half),
        _build_quad(pref, r0 + half, c0 + half, half),
    )


def solve(grid):
    n = len(grid)
    pref = [[0] * (n + 1) for _ in range(n + 1)]
    for r in range(n):
        row_sum = 0
        for c in range(n):
            row_sum += grid[r][c]
            pref[r + 1][c + 1] = pref[r][c + 1] + row_sum
    root = _build_quad(pref, 0, 0, n)
    return _serialize_quad(root)


construct = solve


class Solution:
    def construct(self, grid):
        return solve(grid)
