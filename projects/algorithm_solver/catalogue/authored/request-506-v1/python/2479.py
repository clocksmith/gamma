"""Original candidate for LeetCode 2479. Contract: https://leetcode.com/problems/maximum-xor-of-two-non-overlapping-subtrees/
Definition additionally checked against public doocs/leetcode documentation (CC-BY-SA-4.0); original implementation.
Development tests only; not admitted or independently qualified.
Positional arguments match the official function; inputs are not mutated.
Complexity: O(n log S) time and space, S=sum(values); 46-bit arithmetic uses exact Number division, not 32-bit JS XOR"""
def solve(n,edges,values):
    g=[[] for _ in range(n)]
    for a,b in edges:g[a].append(b);g[b].append(a)
    parent=[-1]*n;order=[0]
    for u in order:
        for v in g[u]:
            if v!=parent[u]:parent[v]=u;order.append(v)
    sums=values[:]
    for u in reversed(order[1:]):sums[parent[u]]+=sums[u]
    trie={};ans=0;stack=[(0,False)]
    while stack:
        u,exit=stack.pop();x=sums[u]
        if exit:
            node=trie
            for b in range(45,-1,-1):node=node.setdefault(x>>b&1,{})
        else:
            if trie:
                node=trie;v=0
                for b in range(45,-1,-1):
                    bit=x>>b&1
                    if 1-bit in node:v|=1<<b;node=node[1-bit]
                    else:node=node[bit]
                ans=max(ans,v)
            stack.append((u,True))
            for v in g[u]:
                if v!=parent[u]:stack.append((v,False))
    return ans
