# Original candidate. Contract: https://leetcode.com/problems/minimize-maximum-value-in-a-grid/
def solve(grid):
    m,n=len(grid),len(grid[0]);rows=[0]*m;cols=[0]*n;out=[[0]*n for _ in range(m)]
    for value,i,j in sorted((grid[i][j],i,j) for i in range(m) for j in range(n)):
        value=max(rows[i],cols[j])+1;out[i][j]=rows[i]=cols[j]=value
    return out
