"""Separate immutable-grid variant; each path owns an integer visited mask."""
def solve(grid: list[list[int]]) -> int:
    cells = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v]
    indices = {p: i for i, p in enumerate(cells)}
    weights = [grid[r][c] for r, c in cells]
    neighbors = [[indices[p] for p in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)) if p in indices] for r,c in cells]
    upper_bound = sum(weights)
    best = 0
    def visit(last, mask, total):
        nonlocal best
        best = max(best, total)
        if best == upper_bound:
            return
        for nxt in neighbors[last]:
            if not mask >> nxt & 1:
                visit(nxt, mask | 1 << nxt, total + weights[nxt])
                if best == upper_bound:
                    return
    for i, value in enumerate(weights):
        visit(i, 1 << i, value)
        if best == upper_bound:
            break
    return best
class Solution:
    def getMaximumGold(self, grid: list[list[int]]) -> int:
        return solve(grid)
