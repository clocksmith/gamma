"""Original development candidate; independent qualification pending."""
from collections import deque

def solve(grid):
    m,n = len(grid),len(grid[0])
    target = 0
    for r,row in enumerate(grid):
        for c,ch in enumerate(row):
            if ch == '@':
                start = (r,c,0)
            elif 'a' <= ch <= 'f':
                target |= 1 << (ord(ch)-97)
    queue = deque([(*start,0)])
    seen = {start}
    while queue:
        r,c,mask,d = queue.popleft()
        if mask == target:
            return d
        for a,b in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
            if not (0 <= a < m and 0 <= b < n):
                continue
            ch = grid[a][b]
            if ch == '#' or ('A' <= ch <= 'F' and not mask & (1 << (ord(ch)-65))):
                continue
            nxt = mask | (1 << (ord(ch)-97)) if 'a' <= ch <= 'f' else mask
            state = (a,b,nxt)
            if state not in seen:
                seen.add(state)
                queue.append((*state,d+1))
    return -1


class Solution:
    def shortestPathAllKeys(self, grid):
        return solve(grid)
