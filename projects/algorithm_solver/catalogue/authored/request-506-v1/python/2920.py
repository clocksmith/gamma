# Original candidate implementation. Contract: https://leetcode.com/problems/maximum-points-after-collecting-coins-from-all-nodes/
def solve(edges,coins,k):
    n=len(coins);adj=[[] for _ in coins]
    for u,v in edges:adj[u].append(v);adj[v].append(u)
    parent=[-1]*n;order=[0]
    for u in order:
        for v in adj[u]:
            if v!=parent[u]:parent[v]=u;order.append(v)
    levels=max(coins).bit_length()+1;dp=[[0]*(levels+1) for _ in coins]
    for u in reversed(order):
        for shift in range(levels-1,-1,-1):
            keep=(coins[u]>>shift)-k;halve=coins[u]>>(shift+1)
            for v in adj[u]:
                if parent[v]==u:keep+=dp[v][shift];halve+=dp[v][shift+1]
            dp[u][shift]=max(keep,halve)
    return dp[0][0]
