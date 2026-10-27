# Original implementation. Contract: https://leetcode.com/problems/minimum-time-to-visit-disappearing-nodes/
def solve(n,edges,disappear):
    import heapq
    adj=[[] for _ in range(n)]
    for u,v,w in edges:adj[u].append((v,w));adj[v].append((u,w))
    dist=[float('inf')]*n;dist[0]=0;heap=[(0,0)]
    while heap:
        d,u=heapq.heappop(heap)
        if d!=dist[u]:continue
        for v,w in adj[u]:
            t=d+w
            if t<dist[v] and t<disappear[v]:dist[v]=t;heapq.heappush(heap,(t,v))
    return [-1 if x==float('inf') else x for x in dist]
