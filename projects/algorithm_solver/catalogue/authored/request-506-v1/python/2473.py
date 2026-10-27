# Original candidate implementation. Contract: https://leetcode.com/problems/minimum-cost-to-buy-apples/
import heapq

def solve(n,roads,appleCost,k):
    adj=[[] for _ in range(n)]
    for a,b,cost in roads:
        adj[a-1].append((b-1,cost*(k+1)));adj[b-1].append((a-1,cost*(k+1)))
    dist=appleCost[:];heap=[(cost,i) for i,cost in enumerate(dist)];heapq.heapify(heap)
    while heap:
        cost,v=heapq.heappop(heap)
        if cost!=dist[v]:continue
        for w,edge in adj[v]:
            if cost+edge<dist[w]:dist[w]=cost+edge;heapq.heappush(heap,(dist[w],w))
    return dist
