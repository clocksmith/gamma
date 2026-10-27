"""Original candidate for LeetCode 1973. Contract: https://leetcode.com/problems/count-nodes-equal-to-sum-of-descendants/
Definition additionally checked against public doocs/leetcode documentation (CC-BY-SA-4.0); original implementation.
Development tests only; not admitted or independently qualified.
Explicit JSON adapter: root is compact BFS level-order values with null children; output count, native pointer identity is not observable.
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
    ns=build(root);sums=[0]*len(ns);ans=0
    for i in range(len(ns)-1,-1,-1):
        val,l,r=ns[i];s=(sums[l] if l>=0 else 0)+(sums[r] if r>=0 else 0)
        ans+=s==val;sums[i]=s+val
    return ans
