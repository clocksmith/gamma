# Original implementation. Contract: https://leetcode.com/problems/maximum-score-after-applying-operations-on-a-tree/
def solve(edges,values):
    n=len(values);g=[[] for _ in range(n)]
    for u,v in edges:g[u].append(v);g[v].append(u)
    parent=[-1]*n;order=[0]
    for u in order:
        for v in g[u]:
            if v!=parent[u]:parent[v]=u;order.append(v)
    keep=[0]*n
    for u in reversed(order):
        children=[v for v in g[u] if v!=parent[u]]
        keep[u]=min(values[u],sum(keep[v] for v in children)) if children else values[u]
    return sum(values)-keep[0]
