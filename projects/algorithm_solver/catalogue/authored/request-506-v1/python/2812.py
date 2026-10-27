# Original candidate. Contract: https://leetcode.com/problems/find-the-safest-path-in-a-grid/
def solve(grid):
    from collections import deque
    n=len(grid);d=[[-1]*n for _ in range(n)];q=deque()
    for i in range(n):
        for j in range(n):
            if grid[i][j]:d[i][j]=0;q.append((i,j))
    directions=((1,0),(-1,0),(0,1),(0,-1))
    while q:
        i,j=q.popleft()
        for di,dj in directions:
            x,y=i+di,j+dj
            if 0<=x<n and 0<=y<n and d[x][y]<0:d[x][y]=d[i][j]+1;q.append((x,y))
    def possible(t):
        if d[0][0]<t:return False
        seen={(0,0)};q=deque([(0,0)])
        while q:
            i,j=q.popleft()
            if i==j==n-1:return True
            for di,dj in directions:
                x,y=i+di,j+dj
                if 0<=x<n and 0<=y<n and (x,y) not in seen and d[x][y]>=t:seen.add((x,y));q.append((x,y))
        return False
    lo,hi=0,min(d[0][0],d[-1][-1])+1
    while lo+1<hi:
        mid=(lo+hi)//2
        if possible(mid):lo=mid
        else:hi=mid
    return lo
