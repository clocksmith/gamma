"""Original candidate for LeetCode 2865. Contract: https://leetcode.com/problems/beautiful-towers-i/
Development tests only; not admitted or independently qualified.
Positional arguments match the official function; inputs are not mutated.
Complexity: O(n^2) time, O(1) space; n <= 1000, sums <= 10^12"""
def solve(heights):
    ans=0
    for peak in range(len(heights)):
        total=heights[peak];h=heights[peak]
        for i in range(peak-1,-1,-1):h=min(h,heights[i]);total+=h
        h=heights[peak]
        for i in range(peak+1,len(heights)):h=min(h,heights[i]);total+=h
        ans=max(ans,total)
    return ans
