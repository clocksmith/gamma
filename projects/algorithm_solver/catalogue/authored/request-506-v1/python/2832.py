# Original candidate. Contract: https://leetcode.com/problems/maximal-range-that-each-element-is-maximum-in-it/
def solve(nums):
    n=len(nums); left=[-1]*n; right=[n]*n; stack=[]
    for i,x in enumerate(nums):
        while stack and nums[stack[-1]]<x:right[stack.pop()]=i
        if stack:left[i]=stack[-1]
        stack.append(i)
    return [right[i]-left[i]-1 for i in range(n)]
