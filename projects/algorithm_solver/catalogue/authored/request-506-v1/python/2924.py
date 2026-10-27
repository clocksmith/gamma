"""Original candidate for LeetCode 2924. Contract: https://leetcode.com/problems/find-champion-ii/
Development tests only; not admitted or independently qualified.
Positional arguments match the official function; inputs are not mutated.
Complexity: O(n+m) time, O(n) space; input is a DAG"""
def solve(n,edges):
    indegree=[0]*n
    for u,v in edges:indegree[v]+=1
    roots=[i for i in range(n) if indegree[i]==0]
    return roots[0] if len(roots)==1 else -1
