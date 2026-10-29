"""Original candidate; no qualification or admission."""

from collections import deque

def solve(grid,catJump,mouseJump):
    cells=[(r,c) for r in range(len(grid)) for c in range(len(grid[0])) if grid[r][c]!='#'];index={p:i for i,p in enumerate(cells)};n=len(cells)
    mouse=next(index[r,c] for r,c in cells if grid[r][c]=='M');cat=next(index[r,c] for r,c in cells if grid[r][c]=='C');food=next(index[r,c] for r,c in cells if grid[r][c]=='F')
    def moves(jump):
        out=[]
        for i,(r,c) in enumerate(cells):
            options=[i]
            for dr,dc in ((-1,0),(1,0),(0,-1),(0,1)):
                for step in range(1,jump+1):
                    p=(r+dr*step,c+dc*step)
                    if p not in index:break
                    options.append(index[p])
            out.append(options)
        return out
    mm,cm=moves(mouseJump),moves(catJump);size=2*n*n;winner=[0]*size;degree=[0]*size;distance=[0]*size;maximum=[0]*size;queue=deque()
    for m in range(n):
        for c in range(n):
            terminal=2 if m==c or c==food else 1 if m==food else 0
            for turn in (0,1):
                state=2*(m*n+c)+turn;degree[state]=len(mm[m] if turn==0 else cm[c])
                if terminal:winner[state]=terminal;queue.append(state)
    while queue:
        state=queue.popleft();turn=state%2;pair=state//2;m,c=divmod(pair,n);parents=(2*(previous*n+c) for previous in mm[m]) if turn==1 else (2*(m*n+previous)+1 for previous in cm[c])
        for parent in parents:
            if winner[parent]:continue
            player=1 if parent%2==0 else 2
            if winner[state]==player:winner[parent]=player;distance[parent]=distance[state]+1;queue.append(parent)
            else:
                degree[parent]-=1;maximum[parent]=max(maximum[parent],distance[state])
                if degree[parent]==0:winner[parent]=3-player;distance[parent]=maximum[parent]+1;queue.append(parent)
    start=2*(mouse*n+cat);return winner[start]==1 and distance[start]<=1000


class Solution:
    def canMouseWin(self, grid, catJump, mouseJump):
        return solve(grid, catJump, mouseJump)
