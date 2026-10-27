# Original candidate implementation. Contract: https://leetcode.com/problems/find-shortest-path-with-k-hops/
import heapq

def solve(n,edges,s,d,k):
    adj=[[] for _ in range(n)]
    for u,v,w in edges:adj[u].append((v,w));adj[v].append((u,w))
    dist=[[float('inf')]*(k+1) for _ in range(n)];dist[s][0]=0;heap=[(0,s,0)]
    while heap:
        cost,u,used=heapq.heappop(heap)
        if cost!=dist[u][used]:continue
        if u==d:return cost
        for v,w in adj[u]:
            if cost+w<dist[v][used]:dist[v][used]=cost+w;heapq.heappush(heap,(cost+w,v,used))
            if used<k and cost<dist[v][used+1]:dist[v][used+1]=cost;heapq.heappush(heap,(cost,v,used+1))
    return -1
