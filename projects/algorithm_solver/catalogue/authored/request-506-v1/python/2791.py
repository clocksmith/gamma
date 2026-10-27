"""Original candidate for LeetCode 2791. Contract: https://leetcode.com/problems/count-paths-that-can-form-a-palindrome-in-a-tree/
Development tests only; not admitted or independently qualified.
Positional arguments match the official function; inputs are not mutated.
Complexity: O(26n) time, O(n) space; masks use 26 bits, counts fit JS Number"""
def solve(parent,s):
    children=[[] for _ in parent]
    for i in range(1,len(parent)):children[parent[i]].append(i)
    stack=[(0,0)];counts={};ans=0
    while stack:
        u,mask=stack.pop();ans+=counts.get(mask,0)
        for bit in range(26):ans+=counts.get(mask^(1<<bit),0)
        counts[mask]=counts.get(mask,0)+1
        for v in children[u]:stack.append((v,mask^(1<<(ord(s[v])-97))))
    return ans
