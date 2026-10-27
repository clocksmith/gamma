"""Original candidate for LeetCode 2508. Contract: https://leetcode.com/problems/add-edges-to-make-degrees-of-all-nodes-even/
Development tests only; not admitted or independently qualified.
Positional arguments match the official function; inputs are not mutated.
Complexity: O(n+m) expected time and space"""
def solve(n,edges):
    adj=[set() for _ in range(n+1)]
    for u,v in edges:adj[u].add(v);adj[v].add(u)
    odd=[i for i in range(1,n+1) if len(adj[i])%2]
    if not odd:return True
    if len(odd)==2:
        a,b=odd
        return b not in adj[a] or any(i!=a and i!=b and i not in adj[a] and i not in adj[b] for i in range(1,n+1))
    if len(odd)==4:
        a,b,c,d=odd
        return (b not in adj[a] and d not in adj[c]) or (c not in adj[a] and d not in adj[b]) or (d not in adj[a] and c not in adj[b])
    return False
