# Original candidate. Contract: https://leetcode.com/problems/maximum-trailing-zeros-in-a-cornered-path/
def solve(grid):
    m,n=len(grid),len(grid[0]);fac=[]
    for prime in (2,5):
        a=[[0]*n for _ in range(m)]
        for i in range(m):
            for j in range(n):
                x=grid[i][j]
                while x%prime==0:a[i][j]+=1;x//=prime
        row=[[0]*(n+1) for _ in range(m)];col=[[0]*n for _ in range(m+1)]
        for i in range(m):
            for j in range(n):row[i][j+1]=row[i][j]+a[i][j];col[i+1][j]=col[i][j]+a[i][j]
        fac.append((a,row,col))
    ans=0
    for i in range(m):
        for j in range(n):
            totals=[]
            for a,r,c in fac:
                left,right=r[i][j+1],r[i][n]-r[i][j];up,down=c[i+1][j],c[m][j]-c[i][j]
                totals.append([x+y-a[i][j] for x in (left,right) for y in (up,down)])
            ans=max(ans,max(min(x,y) for x,y in zip(*totals)))
    return ans
