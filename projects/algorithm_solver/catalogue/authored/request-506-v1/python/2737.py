# Original implementation. Contract: https://leetcode.com/problems/find-the-closest-marked-node/
def solve(n,edges,s,marked):
    g=[[] for _ in range(n)]
    for u,v,w in edges:g[u].append((v,w))
    d=[float('inf')]*n;d[s]=0;used=[False]*n;marked=set(marked)
    for _ in range(n):
        u=min((i for i in range(n) if not used[i]),key=lambda i:d[i],default=-1)
        if u<0 or d[u]==float('inf'):return -1
        if u in marked:return d[u]
        used[u]=True
        for v,w in g[u]:d[v]=min(d[v],d[u]+w)
    return -1
