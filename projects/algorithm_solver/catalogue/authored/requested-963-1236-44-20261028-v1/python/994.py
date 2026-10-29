"""Original candidate; no qualification or admission."""

from collections import deque

def solve(grid):
    rows,cols=len(grid),len(grid[0]);queue=deque();seen=set();fresh=0;answer=0
    for r in range(rows):
        for c in range(cols):
            if grid[r][c]==2:queue.append((r,c,0));seen.add((r,c))
            elif grid[r][c]==1:fresh+=1
    while queue:
        r,c,time=queue.popleft();answer=max(answer,time)
        for nr,nc in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
            if 0<=nr<rows and 0<=nc<cols and grid[nr][nc]==1 and (nr,nc) not in seen:seen.add((nr,nc));fresh-=1;queue.append((nr,nc,time+1))
    return -1 if fresh else answer


class Solution:
    def orangesRotting(self, grid):
        return solve(grid)
