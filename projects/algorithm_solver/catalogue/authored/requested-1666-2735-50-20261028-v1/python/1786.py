"""Original candidate; no qualification or admission."""

import heapq

def solve(n,edges):
    graph=[[] for _ in range(n)]
    for a,b,w in edges:graph[a-1].append((b-1,w));graph[b-1].append((a-1,w))
    distance=[float('inf')]*n;distance[-1]=0;heap=[(0,n-1)]
    while heap:
        value,u=heapq.heappop(heap)
        if value!=distance[u]:continue
        for v,w in graph[u]:
            if value+w<distance[v]:distance[v]=value+w;heapq.heappush(heap,(value+w,v))
    ways=[0]*n;ways[-1]=1
    for u in sorted(range(n),key=distance.__getitem__):
        for v,_ in graph[u]:
            if distance[v]>distance[u]:ways[v]=(ways[v]+ways[u])%1000000007
    return ways[0]


class Solution:
    def countRestrictedPaths(self, n, edges):
        return solve(n, edges)
