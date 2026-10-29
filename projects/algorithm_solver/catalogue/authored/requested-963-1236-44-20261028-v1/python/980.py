"""Original candidate; no qualification or admission."""

from functools import lru_cache

def solve(grid):
    cells=[(r,c) for r in range(len(grid)) for c in range(len(grid[0])) if grid[r][c]!=-1];index={v:i for i,v in enumerate(cells)}
    start=next(index[r,c] for r,c in cells if grid[r][c]==1);end=next(index[r,c] for r,c in cells if grid[r][c]==2)
    adj=[[index[p] for p in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)) if p in index] for r,c in cells];full=(1<<len(cells))-1
    @lru_cache(None)
    def count(at,mask):
        if at==end:return int(mask==full)
        return sum(count(nxt,mask|(1<<nxt)) for nxt in adj[at] if not mask>>nxt&1)
    return count(start,1<<start)


class Solution:
    def uniquePathsIII(self, grid):
        return solve(grid)
