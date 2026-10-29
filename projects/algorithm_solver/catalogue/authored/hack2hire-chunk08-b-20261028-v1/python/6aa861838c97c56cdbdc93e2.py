"""Hack2Hire 6aa861838c97c56cdbdc93e2 (Tetris Block Drop) over an INFERRED spec; qualification unknown."""

def _land(background, block, offset):
    rows, h, w = len(background), len(block), len(block[0])
    drop = None
    for j in range(w):
        lowest = -1
        for r in range(h):
            if block[r][j]:
                lowest = r
        if lowest < 0:
            continue
        col, first = offset + j, rows
        for r in range(rows):
            if background[r][col]:
                first = r
                break
        candidate = first - 1 - lowest
        if drop is None or candidate < drop:
            drop = candidate
    grid = [row[:] for row in background]
    for r in range(h):
        for j in range(w):
            if block[r][j]:
                grid[drop + r][offset + j] = 1
    return grid


def solve(background, block, offset):
    return _land(background, block, offset)


class Solution:
    def dropBlock(self, background, block, offset):
        return solve(background, block, offset)
