# Original implementation. Contract: https://leetcode.com/problems/spiral-matrix-iv/
def solve(m,n,head_values):
    out=[[-1]*n for _ in range(m)];r=c=d=0;directions=[(0,1),(1,0),(0,-1),(-1,0)]
    for x in head_values:
        out[r][c]=x;dr,dc=directions[d];a,b=r+dr,c+dc
        if not(0<=a<m and 0<=b<n and out[a][b]==-1):d=(d+1)%4;dr,dc=directions[d];a,b=r+dr,c+dc
        r,c=a,b
    return out
