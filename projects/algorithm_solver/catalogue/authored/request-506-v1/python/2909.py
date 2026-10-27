"""Original candidate for LeetCode 2909. Contract: https://leetcode.com/problems/minimum-sum-of-mountain-triplets-ii/
Development tests only; not admitted or independently qualified.
Positional arguments match the official function; inputs are not mutated.
Complexity: O(n) time and space"""
def solve(nums):
    n=len(nums);right=[float('inf')]*(n+1)
    for i in range(n-1,-1,-1):right[i]=min(nums[i],right[i+1])
    left=float('inf');ans=float('inf')
    for j,x in enumerate(nums):
        if left<x and right[j+1]<x:ans=min(ans,left+x+right[j+1])
        left=min(left,x)
    return -1 if ans==float('inf') else ans
