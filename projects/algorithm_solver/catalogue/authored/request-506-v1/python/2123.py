# Original implementation. Contract: https://leetcode.com/problems/minimum-operations-to-remove-adjacent-ones-in-matrix/
def solve(grid):
    from collections import deque
    m,n=len(grid),len(grid[0]); size=m*n
    left=[i*n+j for i in range(m) for j in range(n) if grid[i][j] and (i+j)%2==0]
    adj={u:[] for u in left}
    for u in left:
        i,j=divmod(u,n)
        for a,b in ((i-1,j),(i+1,j),(i,j-1),(i,j+1)):
            if 0<=a<m and 0<=b<n and grid[a][b]:adj[u].append(a*n+b)
    pu=[-1]*size;pv=[-1]*size;answer=0
    while True:
        dist=[-1]*size;q=deque()
        for u in left:
            if pu[u]<0:dist[u]=0;q.append(u)
        shortest=size+1
        while q:
            u=q.popleft()
            if dist[u]>=shortest:continue
            for v in adj[u]:
                w=pv[v]
                if w<0:shortest=min(shortest,dist[u]+1)
                elif dist[w]<0:dist[w]=dist[u]+1;q.append(w)
        if shortest==size+1:return answer
        ptr=[0]*size
        for start in left:
            if pu[start]>=0:continue
            stack=[start];rights=[]
            while stack:
                u=stack[-1];advanced=False
                while ptr[u]<len(adj[u]):
                    v=adj[u][ptr[u]];ptr[u]+=1;w=pv[v]
                    if w<0 and dist[u]+1==shortest:
                        rights.append(v)
                        for a,b in zip(stack,rights):pu[a]=b;pv[b]=a
                        answer+=1;stack=[];advanced=True;break
                    if w>=0 and dist[w]==dist[u]+1 and dist[w]<shortest:
                        rights.append(v);stack.append(w);advanced=True;break
                if not advanced:
                    dist[u]=-1;stack.pop()
                    if rights:rights.pop()
