"""Hack2Hire 6aa8623b8c97c56cdbdc93eb (Tetris Block Drop) over an INFERRED spec; qualification unknown."""

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
    grid = _land(background, block, offset)
    width = len(grid[0])
    kept = [row for row in grid if not all(row)]
    return [[0] * width for _ in range(len(grid) - len(kept))] + kept


class Solution:
    def dropBlockAndClear(self, background, block, offset):
        return solve(background, block, offset)
