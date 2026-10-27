"""Original candidate for LeetCode 2247. Contract: https://leetcode.com/problems/maximum-cost-of-trip-with-k-highways/
Definition additionally checked against public doocs/leetcode documentation (CC-BY-SA-4.0); original implementation.
Development tests only; not admitted or independently qualified.
Positional arguments match the official function; inputs are not mutated.
Complexity: O(2^n n²) time, O(2^n n) space"""
def solve(n,highways,k):
    if k>=n:return -1
    g=[[] for _ in range(n)]
    for a,b,w in highways:g[a].append((b,w));g[b].append((a,w))
    dp={(1<<i,i):0 for i in range(n)}
    for _ in range(k):
        nd={}
        for (mask,u),cost in dp.items():
            for v,w in g[u]:
                if not mask>>v&1:
                    key=(mask|1<<v,v);nd[key]=max(nd.get(key,-1),cost+w)
        dp=nd
    return max(dp.values(),default=-1)
