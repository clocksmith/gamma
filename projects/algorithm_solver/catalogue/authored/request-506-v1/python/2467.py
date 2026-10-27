"""Original candidate for LeetCode 2467. Contract: https://leetcode.com/problems/most-profitable-path-in-a-tree/
Development tests only; not admitted or independently qualified.
Positional arguments match the official function; inputs are not mutated.
Complexity: O(n) time and space; iterative traversal avoids deep recursion"""
def solve(edges,bob,amount):
    n=len(amount);adj=[[] for _ in range(n)]
    for u,v in edges:adj[u].append(v);adj[v].append(u)
    parent=[-1]*n;depth=[0]*n;order=[0]
    for u in order:
        for v in adj[u]:
            if v!=parent[u]:parent[v]=u;depth[v]=depth[u]+1;order.append(v)
    bt=[n+1]*n;t=0
    while bob!=-1:bt[bob]=t;t+=1;bob=parent[bob]
    income=[0]*n;answer=-float('inf')
    for u in order:
        value=amount[u] if depth[u]<bt[u] else amount[u]//2 if depth[u]==bt[u] else 0
        income[u]=(income[parent[u]] if parent[u]!=-1 else 0)+value
        if u and len(adj[u])==1:answer=max(answer,income[u])
    return answer
