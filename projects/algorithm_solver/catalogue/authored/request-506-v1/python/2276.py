"""Original candidate for LeetCode 2276. Contract: https://leetcode.com/problems/count-integers-in-intervals/
Development tests only; not admitted or independently qualified.
Batch adapter solve(operations, arguments) follows CountIntervals class-call arrays.
Complexity: O(q log U) amortized node creation, O(q log U) space, U=10^9; O(1) count"""
def solve(operations,arguments):
    # Sparse segment tree stores covered integer counts on inclusive ranges.
    tree={};out=[]
    def add(v,l,r,a,b):
        if tree.get(v,0)==r-l+1:return
        if a<=l and r<=b:tree[v]=r-l+1;return
        m=(l+r)//2
        if a<=m:add(v*2,l,m,a,b)
        if b>m:add(v*2+1,m+1,r,a,b)
        tree[v]=tree.get(v*2,0)+tree.get(v*2+1,0)
    for op,a in zip(operations,arguments):
        if op=='add':add(1,1,10**9,*a);out.append(None)
        elif op=='count':out.append(tree.get(1,0))
        else:out.append(None)
    return out
