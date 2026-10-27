# Original candidate implementation. Contract: https://leetcode.com/problems/distance-to-a-cycle-in-undirected-graph/
from collections import deque

def solve(n,edges):
    adj=[[] for _ in range(n)]
    for a,b in edges:adj[a].append(b);adj[b].append(a)
    degree=[len(v) for v in adj];queue=deque(i for i,d in enumerate(degree) if d==1)
    while queue:
        v=queue.popleft();degree[v]=0
        for w in adj[v]:
            if degree[w]>0:
                degree[w]-=1
                if degree[w]==1:queue.append(w)
    dist=[0 if d>0 else -1 for d in degree];queue=deque(i for i,d in enumerate(dist) if d==0)
    while queue:
        v=queue.popleft()
        for w in adj[v]:
            if dist[w]<0:dist[w]=dist[v]+1;queue.append(w)
    return dist
