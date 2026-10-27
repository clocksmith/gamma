# Original implementation. Contract: https://leetcode.com/problems/closest-node-to-path-in-tree/
from collections import deque
def solve(n,edges,query):
    g=[[] for _ in range(n)]
    for u,v in edges:g[u].append(v);g[v].append(u)
    distances=[]
    for s in range(n):
        d=[-1]*n;d[s]=0;q=deque([s])
        while q:
            u=q.popleft()
            for v in g[u]:
                if d[v]<0:d[v]=d[u]+1;q.append(v)
        distances.append(d)
    return [min((v for v in range(n) if distances[s][v]+distances[v][t]==distances[s][t]),key=lambda v:distances[x][v]) for s,t,x in query]
