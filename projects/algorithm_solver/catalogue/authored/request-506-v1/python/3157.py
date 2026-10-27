"""Original candidate for LeetCode 3157. Contract: https://leetcode.com/problems/find-the-level-of-tree-with-minimum-sum/
Definition additionally checked against public doocs/leetcode documentation (CC-BY-SA-4.0); original implementation.
Development tests only; not admitted or independently qualified.
Explicit JSON adapter: nonempty root compact BFS values with null children; root level1, ties choose smallest level.
Complexity: O(n) time and space"""
def build(values):
    if not values or values[0] is None:return []
    nodes=[[values[0],-1,-1]];q=0;p=1
    while q<len(nodes) and p<len(values):
        for side in (1,2):
            if p<len(values) and values[p] is not None:
                nodes[q][side]=len(nodes);nodes.append([values[p],-1,-1])
            p+=1
        q+=1
    return nodes
def solve(root):
    ns=build(root);level=[0];depth=1;best=float('inf');answer=1
    while level:
        total=sum(ns[i][0] for i in level)
        if total<best:best=total;answer=depth
        level=[c for i in level for c in ns[i][1:] if c>=0];depth+=1
    return answer
