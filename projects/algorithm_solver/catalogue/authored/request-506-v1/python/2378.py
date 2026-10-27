# Original implementation. Contract: https://leetcode.com/problems/choose-edges-to-maximize-score-in-a-tree/
def solve(edges):
    n=len(edges);g=[[] for _ in range(n)]
    for i,(p,w) in enumerate(edges):
        if i:g[p].append((i,w))
    order=[0]
    for u in order:order.extend(v for v,w in g[u])
    free=[0]*n;blocked=[0]*n
    for u in reversed(order):
        base=sum(free[v] for v,w in g[u]);blocked[u]=base
        free[u]=base+max([0]+[w+blocked[v]-free[v] for v,w in g[u]])
    return free[0]
